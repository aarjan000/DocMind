from pathlib import Path

import pandas as pd


def load_csv(file_path):
    file_path = Path(file_path)
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            frame = pd.read_csv(
                file_path,
                dtype=str,
                keep_default_na=False,
                encoding=encoding,
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise ValueError(f"Could not decode CSV file: {last_error}")

    records = []
    for row_number, row in enumerate(frame.to_dict(orient="records"), start=1):
        content = "\n".join(
            f"{column}: {value}" for column, value in row.items()
            if str(value).strip()
        )
        if content.strip():
            records.append({
                "source": file_path.name,
                "reference": f"Row {row_number}",
                "row_number": row_number,
                "text": content,
            })
    return records
