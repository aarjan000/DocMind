from pathlib import Path

from docx import Document


def load_word(file_path):
    """Extract DOCX paragraphs and table rows with traceable references."""
    file_path = Path(file_path)
    document = Document(file_path)
    records = []

    for number, paragraph in enumerate(document.paragraphs, start=1):
        text = paragraph.text.strip()
        if text:
            records.append({
                "source": file_path.name,
                "reference": f"Paragraph {number}",
                "text": text,
            })

    for table_number, table in enumerate(document.tables, start=1):
        for row_number, row in enumerate(table.rows, start=1):
            cells = [cell.text.strip() for cell in row.cells]
            content = " | ".join(cells)
            if content.strip():
                records.append({
                    "source": file_path.name,
                    "reference": f"Table {table_number}, Row {row_number}",
                    "text": content,
                })
    return records
