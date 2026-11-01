from pathlib import Path
import os
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
# Separate database for multilingual BGE-M3 embeddings.
VECTOR_STORE_DIR = DATA_DIR / "vector_store_bge_m3"
COLLECTION_NAME = "docmind_bge_m3"
SUPPORTED_FORMATS = {
    ".pdf", ".csv", ".docx", ".jpg", ".jpeg", ".txt"
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVAL_K = 6
# English, Nepali, Hindi and Tamil.
OCR_LANGUAGES = os.getenv(
    "DOCMIND_OCR_LANGUAGES",
    "eng+nep+hin+tam"
)
OCR_DPI = 200
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
