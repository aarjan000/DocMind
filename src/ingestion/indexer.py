from pathlib import Path

from src.config import SUPPORTED_FORMATS, UPLOAD_DIR
from src.database.vector_store import get_vector_store, upsert_document
from src.embeddings.embedder import get_embedding_model
from src.ingestion.chunker import create_chunks
from src.ingestion.file_router import load_file
from src.ingestion.file_hash import sha256_file



def index_file(file_path, vector_store, file_hash=None):
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)
    if file_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    digest = file_hash or sha256_file(file_path)
    records = load_file(file_path)
    if not records:
        return {
            "source": file_path.name,
            "status": "no_text",
            "records": 0,
            "chunks": 0,
            "message": "No text could be extracted. Existing indexed version was preserved.",
        }

    chunks = create_chunks(records)
    if not chunks:
        return {
            "source": file_path.name,
            "status": "no_text",
            "records": len(records),
            "chunks": 0,
            "message": "No usable chunks were created. Existing indexed version was preserved.",
        }

    result = upsert_document(vector_store, chunks, file_path.name, digest)
    return {
        "source": file_path.name,
        "status": result["status"],
        "records": len(records),
        "chunks": result["chunks"],
        "message": "Already up to date." if result["status"] == "unchanged" else "Indexed successfully.",
    }


def index_new_documents(upload_dir=UPLOAD_DIR, vector_store=None, embedding_model=None):
    upload_dir = Path(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    if vector_store is None:
        embedding_model = embedding_model or get_embedding_model()
        vector_store = get_vector_store(embedding_model)

    results = []
    files = sorted(
        (path for path in upload_dir.iterdir()
         if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS),
        key=lambda path: path.name.lower(),
    )
    for path in files:
        try:
            results.append(index_file(path, vector_store))
        except Exception as exc:
            results.append({
                "source": path.name,
                "status": "failed",
                "records": 0,
                "chunks": 0,
                "message": str(exc),
            })
    return results
