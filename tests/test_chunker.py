import unittest

from src.ingestion.chunker import create_chunks


class ChunkerTests(unittest.TestCase):
    def test_metadata_without_page_number_is_preserved(self):
        chunks = create_chunks([{
            "source": "records.csv",
            "reference": "Row 3",
            "row_number": 3,
            "text": "name: Ada Lovelace\nrole: Mathematician",
        }])
        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["source"], "records.csv")
        self.assertEqual(chunks[0]["reference"], "Row 3")
        self.assertEqual(chunks[0]["row_number"], 3)
        self.assertIn("Ada Lovelace", chunks[0]["text"])

    def test_empty_records_produce_no_chunks(self):
        self.assertEqual(create_chunks([{"source": "empty.txt", "text": "  "}]), [])


if __name__ == "__main__":
    unittest.main()
