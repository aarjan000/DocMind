from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_OVERLAP, CHUNK_SIZE


def create_chunks(records):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for record in records:
        text = str(record.get("text", "")).strip()
        if not text:
            continue
        metadata = {key: value for key, value in record.items() if key != "text"}
        for part in splitter.split_text(text):
            if part.strip():
                chunks.append({**metadata, "text": part})
    return chunks
