import unittest

from app.rag.msearch import _group_collections_by_prefix, _records_from_response


# Shape mirrors a real mSearch hybrid response: when `highlight: true` is sent,
# BM25 (`source: "key"`) hits come back with a `passages` array whose entries are
# single matched query tokens, not real passage text. The full chunk text always
# lives in `document.content`.
KEYWORD_HIT_RESPONSE = {
    "documents": [
        {
            "document_id": "doc-1",
            "score": 0.81,
            "source": "key",
            "passages": [
                {"text": "Stalin", "section_name": "content"},
                {"text": "Stalin", "section_name": "content"},
                {"text": "Čína", "section_name": "content"},
                {"text": "velmoci", "section_name": "content"},
                {"text": "velmocí", "section_name": "content"},
            ],
            "document": {
                "id": "v2026-02/soudobe-dejiny-cele/1997-01.pdf_page_108",
                "title": "1997-01.pdf",
                "file_name": "1997-01.pdf",
                "url": "https://storage.ufal.mff.cuni.cz/x.pdf",
                "page_number": 108,
                "content": (
                    "106 Soudobé dějiny IV/1 nemá nic společného. Avšak Stalin, jak "
                    "Churchill později potvrdil, pevně a věrně dodržel naši dohodu z "
                    "října a během dlouhých měsíců bojů o vliv ve střední Evropě se "
                    "Čína teprve postupně stávala skutečnou velmocí na světové scéně."
                ),
            },
        }
    ]
}


class MSearchTextTests(unittest.TestCase):
    def test_keyword_hit_uses_full_content_not_highlight_tokens(self) -> None:
        records = _records_from_response(KEYWORD_HIT_RESPONSE, limit=10)

        self.assertEqual(len(records), 1)
        text = records[0]["text"]

        # The chunk must be the real passage, not the highlight token salad.
        self.assertIn("Churchill", text)
        self.assertNotIn("Stalin\n\nStalin", text)

        # Every retrieved chunk should carry real context, not a few keywords.
        self.assertGreater(len(text.split()), 20)


class CollectionGroupingTests(unittest.TestCase):
    def test_groups_all_versions_per_wp_newest_first(self) -> None:
        collections = [
            {"collection_id": "a", "collection_name": "wp1-histoedu-v2026-01", "last_modified": "2026-01-10"},
            {"collection_id": "b", "collection_name": "wp1-histoedu-v2026-02", "last_modified": "2026-02-10"},
            {"collection_id": "c", "collection_name": "wp3-law-v2026-02", "last_modified": "2026-02-01"},
            {"collection_id": "d", "collection_name": "public-misc", "last_modified": "2026-03-01"},
            {"collection_id": "", "collection_name": "wp2-zaplavy-v1", "last_modified": "2026-01-01"},
        ]

        grouped = _group_collections_by_prefix(collections)

        # All wp1 versions kept, newest first; non-wp and id-less entries dropped.
        self.assertEqual([entry["collection_id"] for entry in grouped["wp1"]], ["b", "a"])
        self.assertEqual([entry["collection_id"] for entry in grouped["wp3"]], ["c"])
        self.assertNotIn("wp2", grouped)
        self.assertNotIn("wp4", grouped)


if __name__ == "__main__":
    unittest.main()
