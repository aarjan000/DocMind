import tempfile
import unittest
from pathlib import Path

from src.ingestion.file_hash import sha256_file


class IndexerHashTests(unittest.TestCase):
    def test_hash_changes_when_file_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("first", encoding="utf-8")
            first = sha256_file(path)
            path.write_text("second", encoding="utf-8")
            second = sha256_file(path)
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
