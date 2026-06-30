import unittest
from unittest.mock import patch

from app.config import Settings, get_settings
from app.rag.msearch import MSearchRetriever, _group_collections_by_prefix, _records_from_response
from app.rag.pipeline import RAGPipeline


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

    def test_passage_only_keyword_fragments_are_omitted(self) -> None:
        response = {
            "documents": [
                {
                    "document_id": "tiny-1",
                    "score": 0.9,
                    "source": "key",
                    "passages": [
                        {"text": "Josefa Toufara"},
                        {"text": "Josef-Toufar"},
                        {"text": "Toufar a"},
                    ],
                    "document": {"id": "tiny-1", "title": "tiny.pdf", "content": ""},
                },
                {
                    "document_id": "tiny-2",
                    "score": 0.8,
                    "source": "key",
                    "passages": [
                        {"text": "Josef Toufar Josef Toufar Josef Toufar Josef Toufar Josef Toufar Josef Toufar"},
                    ],
                    "document": {"id": "tiny-2", "title": "repeated.pdf", "content": ""},
                },
                {
                    "document_id": "useful-1",
                    "score": 0.7,
                    "source": "key",
                    "passages": [
                        {
                            "text": (
                                "Během vyšetřování Josefa Toufara v únoru 1950 vznikla "
                                "propaganda kolem událostí v Číhošti."
                            )
                        },
                    ],
                    "document": {"id": "useful-1", "title": "useful.pdf", "content": ""},
                },
            ],
        }

        records = _records_from_response(response, limit=10)

        self.assertEqual([record["chunk_id"] for record in records], ["msearch:useful-1"])
        self.assertEqual(records[0]["citation_id"], "Z1")


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


def _full_doc(index: int) -> dict:
    return {
        "document_id": f"doc-{index}",
        "score": 1.0 - (index / 100),
        "source": "sem",
        "document": {
            "id": f"doc-{index}",
            "title": f"doc-{index}.pdf",
            "content": f"Full chunk text for document {index} with enough context.",
        },
    }


def _tiny_doc(index: int) -> dict:
    return {
        "document_id": f"tiny-{index}",
        "score": 1.0 - (index / 100),
        "source": "key",
        "passages": [{"text": "Josefa Toufara"}],
        "document": {"id": f"tiny-{index}", "title": f"tiny-{index}.pdf", "content": ""},
    }


class _FakeMSearchResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class _FakeMSearchClient:
    payloads = []
    documents = []

    def __init__(self, *args, **kwargs):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        payload = kwargs["json"]
        self.payloads.append(payload)
        return _FakeMSearchResponse({"documents": self.documents[: payload["max_results"]]})


class MSearchRetrieveTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakeMSearchClient.payloads = []
        _FakeMSearchClient.documents = []

    def _retriever(self) -> MSearchRetriever:
        settings = Settings(
            MSEARCH_USERNAME="user",
            MSEARCH_PASSWORD="password",
            MSEARCH_BASE_URL="https://msearch.example.test",
        )
        return MSearchRetriever(settings)

    def test_retrieve_asks_for_top_k_when_first_page_is_usable(self) -> None:
        retriever = self._retriever()
        _FakeMSearchClient.documents = [_full_doc(index) for index in range(8)]
        with patch("app.rag.msearch.httpx.Client", _FakeMSearchClient):
            records = retriever.retrieve("query", top_k=4)

        self.assertEqual([payload["max_results"] for payload in _FakeMSearchClient.payloads], [4])
        self.assertEqual(len(records), 4)

    def test_retrieve_expands_once_when_first_page_loses_filtered_fragments(self) -> None:
        retriever = self._retriever()
        _FakeMSearchClient.documents = [
            _tiny_doc(0),
            _tiny_doc(1),
            _full_doc(2),
            _full_doc(3),
            _full_doc(4),
            _full_doc(5),
            _full_doc(6),
            _full_doc(7),
        ]
        with patch("app.rag.msearch.httpx.Client", _FakeMSearchClient):
            records = retriever.retrieve("query", top_k=4)

        self.assertEqual([payload["max_results"] for payload in _FakeMSearchClient.payloads], [4, 8])
        self.assertEqual(len(records), 4)
        self.assertEqual([record["chunk_id"] for record in records], ["msearch:doc-2", "msearch:doc-3", "msearch:doc-4", "msearch:doc-5"])


class _RecordingMSearchRetriever:
    """Captures the kwargs the pipeline passes to mSearch retrieval."""

    def __init__(self):
        self.calls = []

    def retrieve(self, question, top_k, **kwargs):
        self.calls.append(kwargs)
        return []


class MSearchRescoreWiringTests(unittest.TestCase):
    def _pipeline(self):
        pipeline = RAGPipeline(get_settings())
        recorder = _RecordingMSearchRetriever()
        pipeline._msearch_retriever = recorder
        return pipeline, recorder

    def test_rescore_enabled_passes_cross_encoder(self):
        pipeline, recorder = self._pipeline()
        pipeline.retrieve_candidates("q", top_k=5, retrieval_backend="msearch", msearch_rescore=True)
        self.assertEqual(recorder.calls[0]["rescore_method"], "cross_encoder")

    def test_rescore_disabled_passes_none(self):
        pipeline, recorder = self._pipeline()
        pipeline.retrieve_candidates("q", top_k=5, retrieval_backend="msearch", msearch_rescore=False)
        self.assertIsNone(recorder.calls[0]["rescore_method"])

    def test_rescore_default_follows_settings(self):
        pipeline, recorder = self._pipeline()
        # msearch_rescore=None means "use the configured default" (False by default).
        pipeline.retrieve_candidates("q", top_k=5, retrieval_backend="msearch")
        expected = "cross_encoder" if pipeline.settings.msearch_rescore else None
        self.assertEqual(recorder.calls[0]["rescore_method"], expected)


if __name__ == "__main__":
    unittest.main()
