from pathlib import Path
import pymupdf
from src.config import OCR_LANGUAGES, OCR_DPI
def load_pdf(file_path):
    """
    Extract native PDF text whenever available.
    Use full-page OCR only for scanned pages.
    """
    file_path = Path(file_path)
    records = []
    document = pymupdf.open(file_path)
    try:
        for page_number, page in enumerate(document, start=1):
            try:
                # Prefer native PDF text extraction.
                native_text = page.get_text("text").strip()
                if native_text:
                    text = native_text
                else:
                    # No selectable text: treat as a scanned page.
                    text_page = page.get_textpage_ocr(
                        language=OCR_LANGUAGES,
                        dpi=OCR_DPI,
                        full=True,
                    )
                    text = page.get_text(
                        "text",
                        textpage=text_page,
                    ).strip()
            except Exception as exc:
                raise RuntimeError(
                    f"PDF extraction failed on page {page_number} "
                    f"of {file_path.name}. "
                    f"Configured OCR languages: {OCR_LANGUAGES}."
                ) from exc
            if text:
                records.append({
                    "source": file_path.name,
                    "reference": f"Page {page_number}",
                    "page_number": page_number,
                    "text": text,
                })
    finally:
        document.close()
    return records
