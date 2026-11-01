# DocMind v1 — stable local RAG baseline

DocMind is a local document question-answering app built with Streamlit, LangChain, ChromaDB, Hugging Face embeddings and Groq.

## Supported formats

- PDF (text extraction plus OCR for pages with no extractable text)
- DOCX (paragraphs and tables)
- CSV (row-level references)
- TXT
- JPG / JPEG (Tesseract OCR)

Legacy `.doc` files and PNG are not supported in this version.

## Requirements

- Python 3.12 is the recommended deployment baseline. The original project was developed with Python 3.14; some ML dependencies may not yet provide equally reliable wheels for every Python 3.14 environment.
- A Groq API key.
- Tesseract OCR installed and available on PATH for scanned PDFs and image files.

## Windows setup

From the project directory:

```cmd
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Put your real Groq API key in `.env`:

```text
GROQ_API_KEY=your_real_key
GROQ_MODEL=openai/gpt-oss-120b
```

Run:

```cmd
streamlit run app.py
```

The first run downloads the local embedding model, so it can take a little while.

## Document lifecycle

- Uploading a new file saves it in `data/uploads/` and indexes it.
- Each indexed chunk stores its source, reference, file hash and chunk index.
- Re-indexing an unchanged file does not create duplicate chunks.
- Re-indexing a changed file adds the new version and removes stale chunks for that filename.
- Deleting a document removes its local file and its vectors from ChromaDB.
- On first app load in a browser session, orphaned vectors for files no longer present in the upload folder are cleaned up.

## Run tests

```cmd
python -m unittest discover -s tests -v
```

## Important current limitations before a public launch

This is a more reliable local MVP, not yet a secure multi-user SaaS deployment. Chat history is session-only; there is no authentication, tenant isolation, billing, rate limiting, malware scanning, cloud object storage, backup/restore workflow, or production observability. The URL importer blocks private/local IP targets and redirects, but a production service should move URL fetching into a hardened backend with DNS-rebinding protections. OCR is English-only and may be slow for very large scanned PDFs. Validate retrieval quality on a representative evaluation set before selling access.
