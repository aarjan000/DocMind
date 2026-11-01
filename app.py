import ipaddress
import re
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import streamlit as st

from src.config import MAX_UPLOAD_BYTES, SUPPORTED_FORMATS, UPLOAD_DIR
from src.database.vector_store import (
    delete_document,
    get_indexed_documents,
    get_vector_store,
    remove_orphaned_vectors,
)
from src.embeddings.embedder import get_embedding_model
from src.ingestion.indexer import index_file
from src.llm.groq_llm import get_llm
from src.retrieval.rag_chain import answer_question, create_rag_chain
from src.retrieval.retriever import get_retriever

st.set_page_config(page_title="DocMind", page_icon="📚", layout="wide")


@st.cache_resource
def load_resources():
    embedding_model = get_embedding_model()
    vector_store = get_vector_store(embedding_model)
    llm = get_llm()
    rag_chain = create_rag_chain(llm)
    return embedding_model, vector_store, rag_chain


def safe_filename(name):
    name = Path(name).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        raise ValueError("The uploaded file has an invalid filename.")
    return name


def _is_public_host(hostname):
    try:
        addresses = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve the PDF URL hostname.") from exc
    if not addresses:
        raise ValueError("The PDF URL hostname did not resolve.")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private, local and reserved network addresses are not allowed.")
    return True


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_pdf(url):
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid public HTTP or HTTPS PDF URL.")
    _is_public_host(parsed.hostname)

    request = Request(url.strip(), headers={"User-Agent": "DocMind/1.0"})
    opener = build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=30) as response:
            content = response.read(MAX_UPLOAD_BYTES + 1)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("This URL redirects. Paste the final direct PDF URL instead.") from exc
        raise ValueError(f"PDF download failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError(f"Could not download the PDF: {exc}") from exc

    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("The PDF exceeds the 50 MB limit.")
    if not content.startswith(b"%PDF-"):
        raise ValueError("The URL did not return a valid PDF file.")

    filename = safe_filename(unquote(Path(parsed.path).name) or "downloaded_document.pdf")
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return filename, content


def flash_messages():
    messages = st.session_state.pop("docmind_flash", [])
    for kind, message in messages:
        if kind == "success":
            st.sidebar.success(message)
        elif kind == "warning":
            st.sidebar.warning(message)
        else:
            st.sidebar.error(message)


# Initialize shared resources. A configuration or API-key error is shown clearly.
try:
    embedding_model, vector_store, rag_chain = load_resources()
except Exception as exc:
    st.error("DocMind could not initialize its AI services.")
    st.exception(exc)
    st.stop()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# One-time per browser session cleanup for vectors left behind by deleted files.
if not st.session_state.get("orphan_cleanup_done", False):
    try:
        current_names = {
            path.name for path in UPLOAD_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS
        }
        removed = remove_orphaned_vectors(vector_store, current_names)
        if removed:
            st.session_state.setdefault("docmind_flash", []).append(
                ("warning", f"Cleaned up {removed} stale vector chunk(s) from deleted files.")
            )
        st.session_state.orphan_cleanup_done = True
    except Exception as exc:
        st.session_state.setdefault("docmind_flash", []).append(
            ("error", f"Could not reconcile the document index: {exc}")
        )


# Sidebar
st.sidebar.title("📚 DocMind")
st.sidebar.caption("Your AI document assistant")
flash_messages()
st.sidebar.divider()

st.sidebar.subheader("Upload documents")
uploaded_files = st.sidebar.file_uploader(
    "Choose files",
    type=[extension.lstrip(".") for extension in sorted(SUPPORTED_FORMATS)],
    accept_multiple_files=True,
    help="Supported: PDF, DOCX, CSV, TXT, JPG and JPEG. Maximum 50 MB per file.",
)

if st.sidebar.button("Upload and index", use_container_width=True):
    if not uploaded_files:
        st.sidebar.warning("Choose at least one file first.")
    else:
        outcomes = []
        for uploaded in uploaded_files:
            try:
                filename = safe_filename(uploaded.name)
                extension = Path(filename).suffix.lower()
                if extension not in SUPPORTED_FORMATS:
                    raise ValueError(f"Unsupported format: {extension}")
                content = uploaded.getvalue()
                if not content:
                    raise ValueError("The file is empty.")
                if len(content) > MAX_UPLOAD_BYTES:
                    raise ValueError("The file exceeds the 50 MB limit.")
                destination = UPLOAD_DIR / filename
                if destination.exists():
                    raise FileExistsError(
                        f"{filename} already exists. Delete it first if you want to replace it."
                    )
                destination.write_bytes(content)
                outcome = index_file(destination, vector_store)
                if outcome["status"] == "no_text":
                    outcomes.append(("warning", f"{filename}: {outcome['message']}"))
                else:
                    outcomes.append(("success", f"{filename}: {outcome['chunks']} chunks indexed."))
            except Exception as exc:
                outcomes.append(("error", f"{uploaded.name}: {exc}"))
        st.session_state.docmind_flash = outcomes
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Import PDF from a URL")
pdf_url = st.sidebar.text_input("Direct PDF URL", placeholder="https://example.com/file.pdf")
if st.sidebar.button("Download and index", use_container_width=True):
    try:
        if not pdf_url.strip():
            raise ValueError("Paste a PDF URL first.")
        with st.spinner("Downloading and indexing PDF..."):
            filename, content = download_pdf(pdf_url)
            destination = UPLOAD_DIR / filename
            if destination.exists():
                raise FileExistsError(f"{filename} already exists. Delete it before replacing it.")
            destination.write_bytes(content)
            outcome = index_file(destination, vector_store)
        if outcome["status"] == "no_text":
            st.session_state.docmind_flash = [("warning", f"{filename}: {outcome['message']}")]
        else:
            st.session_state.docmind_flash = [("success", f"{filename}: {outcome['chunks']} chunks indexed.")]
    except Exception as exc:
        st.session_state.docmind_flash = [("error", str(exc))]
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Document library")
try:
    indexed_documents = get_indexed_documents(vector_store)
except Exception as exc:
    indexed_documents = {}
    st.sidebar.error(f"Could not read index status: {exc}")

document_files = sorted(
    [path for path in UPLOAD_DIR.iterdir()
     if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS],
    key=lambda path: path.name.casefold(),
)

if not document_files:
    st.sidebar.info("No documents uploaded yet.")

for path in document_files:
    row = st.sidebar.columns([0.60, 0.20, 0.20])
    count = indexed_documents.get(path.name, 0)
    status = f"Indexed · {count} chunks" if count else "Not indexed"
    row[0].caption(f"**{path.name}**\n\n{status}")
    if row[1].button("Index", key=f"index_{path.name}", help=f"Index or refresh {path.name}"):
        try:
            with st.spinner(f"Indexing {path.name}..."):
                outcome = index_file(path, vector_store)
            st.session_state.docmind_flash = [(
                "success" if outcome["status"] != "no_text" else "warning",
                f"{path.name}: {outcome['message']} ({outcome['chunks']} chunks).",
            )]
        except Exception as exc:
            st.session_state.docmind_flash = [("error", f"Indexing failed for {path.name}: {exc}")]
        st.rerun()
    if row[2].button("Delete", key=f"delete_{path.name}", help=f"Delete {path.name}"):
        st.session_state.pending_delete = path.name
        st.rerun()

if st.session_state.get("pending_delete"):
    pending_name = st.session_state.pending_delete
    st.sidebar.warning(f"Permanently delete {pending_name} and its indexed chunks?")
    confirm_col, cancel_col = st.sidebar.columns(2)
    if confirm_col.button("Confirm", key="confirm_document_delete"):
        try:
            pending_path = UPLOAD_DIR / pending_name
            deleted_chunks = delete_document(vector_store, pending_name)
            if pending_path.exists():
                pending_path.unlink()
            st.session_state.docmind_flash = [(
                "success",
                f"Deleted {pending_name} and {deleted_chunks} indexed chunk(s).",
            )]
        except Exception as exc:
            st.session_state.orphan_cleanup_done = False
            st.session_state.docmind_flash = [("error", f"Deletion failed for {pending_name}: {exc}")]
        st.session_state.pending_delete = None
        st.rerun()
    if cancel_col.button("Cancel", key="cancel_document_delete"):
        st.session_state.pending_delete = None
        st.rerun()

st.sidebar.caption("Chat history is currently kept for this browser session only.")


# Main chat
st.title("📚 DocMind")
st.caption("Ask questions across your selected documents. Answers are grounded in retrieved excerpts.")

if "messages" not in st.session_state:
    st.session_state.messages = []

header_left, header_right = st.columns([0.8, 0.2])
with header_right:
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

indexed_names = set(indexed_documents)
all_library_names = [path.name for path in document_files]
selected_sources = st.sidebar.multiselect(
    "Select documents to search",
    options=all_library_names,
    default=[name for name in all_library_names if name in indexed_names],
)
selected_indexed_sources = [name for name in selected_sources if name in indexed_names]

if selected_sources and len(selected_indexed_sources) != len(selected_sources):
    st.info("Some selected files are not indexed yet. They will be ignored until indexing succeeds.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources used"):
                for source in message["sources"]:
                    st.write(f"**{source['source']}** — {source['reference']}")

question = st.chat_input("Ask something about your documents...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if not selected_indexed_sources:
            response = "Please select at least one successfully indexed document from the sidebar."
            st.warning(response)
            st.session_state.messages.append({"role": "assistant", "content": response, "sources": []})
        else:
            try:
                with st.spinner("Searching selected documents and preparing an answer..."):
                    retriever = get_retriever(
                        vector_store,
                        selected_sources=selected_indexed_sources,
                    )
                    result = answer_question(retriever, rag_chain, question)
                st.markdown(result["answer"])
                if result["sources"]:
                    with st.expander("Sources used", expanded=True):
                        for source in result["sources"]:
                            st.write(f"**{source['source']}** — {source['reference']}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                })
            except Exception as exc:
                st.error(f"The question could not be processed: {exc}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I couldn't process that question: {exc}",
                    "sources": [],
                })
