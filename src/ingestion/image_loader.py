from pathlib import Path
import shutil
from PIL import Image
import pytesseract
from src.config import OCR_LANGUAGES
def load_image(file_path):
    """Extract multilingual text from JPG/JPEG images."""
    file_path = Path(file_path)
    if not shutil.which("tesseract"):
        raise RuntimeError(
            "Tesseract OCR was not found on PATH."
        )
    try:
        with Image.open(file_path) as image:
            text = pytesseract.image_to_string(
                image.convert("RGB"),
                lang=OCR_LANGUAGES,
            ).strip()
    except Exception as exc:
        raise RuntimeError(
            f"Could not read image {file_path.name}: {exc}"
        ) from exc
    if not text:
        return []
    return [{
        "source": file_path.name,
        "reference": "Image",
        "text": text,
    }]
