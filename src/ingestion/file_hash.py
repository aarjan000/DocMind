import hashlib
from pathlib import Path


def sha256_file(file_path):
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
