import hashlib
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import COLLECTION_NAME, VECTOR_STORE_DIR


def get_vector_store(embedding_model):
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=str(VECTOR_STORE_DIR),
    )


def _chunk_id(source, file_hash, chunk_index):
    identity = f"{source}\0{file_hash}\0{chunk_index}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def upsert_document(vector_store, chunks, source, file_hash):
    """Add the new version first, then remove stale chunks for this source.

    Deterministic IDs prevent duplicate chunks when the same file is indexed again.
    The old version is retained if extraction or embedding fails before the upsert.
    """
    if not chunks:
        raise ValueError(f"No text chunks were produced for {source}; nothing indexed.")

    existing = vector_store.get(
        where={"source": source},
        include=["metadatas"],
    )
    old_ids = existing.get("ids", [])
    old_metadatas = existing.get("metadatas", []) or []

    if old_ids and old_metadatas and all(
        metadata and metadata.get("file_hash") == file_hash
        for metadata in old_metadatas
    ) and len(old_ids) == len(chunks):
        return {"status": "unchanged", "chunks": len(chunks)}

    documents = []
    ids = []
    for index, chunk in enumerate(chunks):
        metadata = {
            key: value for key, value in chunk.items()
            if key != "text" and value is not None
        }
        metadata["source"] = source
        metadata["file_hash"] = file_hash
        metadata["chunk_index"] = index
        metadata["reference"] = str(metadata.get("reference", "Document"))
        # Chroma metadata values must be simple scalar values.
        metadata = {
            key: value for key, value in metadata.items()
            if isinstance(value, (str, int, float, bool))
        }
        documents.append(Document(page_content=chunk["text"], metadata=metadata))
        ids.append(_chunk_id(source, file_hash, index))

    vector_store.add_documents(documents=documents, ids=ids)
    stale_ids = [item_id for item_id in old_ids if item_id not in set(ids)]
    if stale_ids:
        vector_store.delete(ids=stale_ids)
    return {"status": "indexed", "chunks": len(chunks)}


def delete_document(vector_store, source):
    result = vector_store.get(where={"source": source}, include=["metadatas"])
    ids = result.get("ids", [])
    if ids:
        vector_store.delete(ids=ids)
    return len(ids)


def get_indexed_documents(vector_store):
    result = vector_store.get(include=["metadatas"])
    documents = {}
    for metadata in result.get("metadatas", []) or []:
        if not metadata or not metadata.get("source"):
            continue
        source = metadata["source"]
        documents[source] = documents.get(source, 0) + 1
    return documents


def remove_orphaned_vectors(vector_store, existing_filenames):
    """Remove vector entries whose source file no longer exists on disk."""
    result = vector_store.get(include=["metadatas"])
    grouped = {}
    for item_id, metadata in zip(
        result.get("ids", []), result.get("metadatas", []) or []
    ):
        if metadata and metadata.get("source"):
            grouped.setdefault(metadata["source"], []).append(item_id)
    stale_ids = [
        item_id
        for source, ids in grouped.items()
        if source not in existing_filenames
        for item_id in ids
    ]
    if stale_ids:
        vector_store.delete(ids=stale_ids)
    return len(stale_ids)
