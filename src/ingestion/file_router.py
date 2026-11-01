from pathlib import Path

from src.config import SUPPORTED_FORMATS
from src.ingestion.csv_loader import load_csv
from src.ingestion.image_loader import load_image
from src.ingestion.pdf_loader import load_pdf
from src.ingestion.text_loader import load_text
from src.ingestion.word_loader import load_word

LOADERS = {
    ".pdf": load_pdf,
    ".csv": load_csv,
    ".docx": load_word,
    ".jpg": load_image,
    ".jpeg": load_image,
    ".txt": load_text,
}


def load_file(file_path):
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {extension or '(no extension)'}")
    return LOADERS[extension](file_path)
