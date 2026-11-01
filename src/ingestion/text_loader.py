from pathlib import Path


def load_text(file_path):
    file_path = Path(file_path)
    raw = file_path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if not text.strip():
        return []
    return [{"source": file_path.name, "reference": "Text", "text": text}]
