import unittest

from langchain_core.documents import Document

from src.database.vector_store import upsert_document


class FakeVectorStore:
    def __init__(self):
        self.items = {}

    def get(self, where=None, include=None):
        source = where.get("source") if where else None
        selected = {
            item_id: value for item_id, value in self.items.items()
            if source is None or value["metadata"].get("source") == source
        }
        return {
            "ids": list(selected),
            "metadatas": [item["metadata"] for item in selected.values()],
        }

    def add_documents(self, documents, ids):
        for document, item_id in zip(documents, ids):
            self.items[item_id] = {
                "document": document,
                "metadata": document.metadata,
            }

    def delete(self, ids):
        for item_id in ids:
            self.items.pop(item_id, None)


class VectorStoreTests(unittest.TestCase):
    def test_reindex_same_file_does_not_duplicate_chunks(self):
        store = FakeVectorStore()
        chunks = [{"source": "book.pdf", "reference": "Page 1", "text": "hello"}]
        first = upsert_document(store, chunks, "book.pdf", "hash-a")
        second = upsert_document(store, chunks, "book.pdf", "hash-a")
        self.assertEqual(first["status"], "indexed")
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(len(store.items), 1)

    def test_changed_file_replaces_old_chunks(self):
        store = FakeVectorStore()
        old_chunks = [{"source": "book.pdf", "reference": "Page 1", "text": "old"}]
        new_chunks = [
            {"source": "book.pdf", "reference": "Page 1", "text": "new one"},
            {"source": "book.pdf", "reference": "Page 2", "text": "new two"},
        ]
        upsert_document(store, old_chunks, "book.pdf", "hash-a")
        result = upsert_document(store, new_chunks, "book.pdf", "hash-b")
        self.assertEqual(result["chunks"], 2)
        self.assertEqual(len(store.items), 2)
        self.assertTrue(all(
            item["metadata"]["file_hash"] == "hash-b"
            for item in store.items.values()
        ))

    def test_reference_metadata_is_kept(self):
        store = FakeVectorStore()
        chunks = [{"source": "sheet.csv", "reference": "Row 8", "row_number": 8, "text": "value"}]
        upsert_document(store, chunks, "sheet.csv", "hash-c")
        saved = next(iter(store.items.values()))["metadata"]
        self.assertEqual(saved["reference"], "Row 8")
        self.assertEqual(saved["row_number"], 8)


if __name__ == "__main__":
    unittest.main()
