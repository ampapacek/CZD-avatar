import unittest

from fastapi.testclient import TestClient

from app import main
from app.config import get_settings
from app.rag.pipeline import RAGPipeline, RetrievalCandidates
from app.rag.reranker import blend_and_rank


def _candidates():
    # Retrieval order is c1 > c2 > ... > c5 by score.
    return [
        {
            "chunk_id": f"c{i}",
            "citation_id": f"Z{i}",
            "text": f"text {i}",
            "metadata": {"title": f"Doc {i}"},
            "score": 1.0 - (i - 1) * 0.1,
        }
        for i in range(1, 6)
    ]


class _FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve(self, question, candidate_k, **kwargs):
        return [dict(chunk) for chunk in self._chunks][:candidate_k]


class _ReverseReranker:
    """Cross-encoder that strongly disagrees: later candidates score higher."""

    def rerank(self, question, records, weight, top_k):
        scores = [float(index) for index in range(len(records))]
        return blend_and_rank(records, scores, weight, top_k)


class _StreamingReverseReranker(_ReverseReranker):
    """Reverse reranker that also streams one progress event per two records."""

    def rerank_iter(self, question, records, weight, top_k):
        for done in range(2, len(records) + 1, 2):
            yield ("progress", done, len(records), 0.01 * done)
        yield ("progress", len(records), len(records), 0.01 * len(records))
        yield ("result", self.rerank(question, records, weight, top_k))


class ApplyRerankIterTests(unittest.TestCase):
    def _pipeline(self):
        pipeline = RAGPipeline(get_settings())
        pipeline._retriever = _FakeRetriever(_candidates())
        pipeline._reranker = _StreamingReverseReranker()
        return pipeline

    def test_streams_eta_progress_then_result_and_seeds_estimator(self):
        pipeline = self._pipeline()
        candidates = pipeline.retrieve_candidates(
            "q", top_k=3, retrieval_backend="local", rerank_enabled=True, rerank_weight=1.0, rerank_candidates=5
        )
        events = list(pipeline.apply_rerank_iter("q", candidates))

        # First event is the up-front ETA seed (None on this first run).
        self.assertEqual(events[0][0], "eta")
        self.assertIsNone(events[0][1])
        # Final event carries the reranked chunks and a measured duration.
        kind, chunks, seconds = events[-1]
        self.assertEqual(kind, "result")
        self.assertEqual(chunks[0]["chunk_id"], "c5")
        self.assertGreaterEqual(seconds, 0.0)
        # The completed run seeds the estimator for next time.
        self.assertIsNotNone(pipeline._rerank_eta.seed_seconds([c["text"] for c in candidates.candidates]))

    def test_inactive_rerank_yields_only_result(self):
        pipeline = self._pipeline()
        candidates = pipeline.retrieve_candidates(
            "q", top_k=3, retrieval_backend="local", rerank_enabled=False, rerank_weight=0.0
        )
        events = list(pipeline.apply_rerank_iter("q", candidates))
        self.assertEqual([e[0] for e in events], ["result"])
        self.assertEqual([c["chunk_id"] for c in events[0][1]], ["c1", "c2", "c3"])
        self.assertEqual(events[0][2], 0.0)


class RetrieveWithBaselineTests(unittest.TestCase):
    def _pipeline(self):
        pipeline = RAGPipeline(get_settings())
        pipeline._retriever = _FakeRetriever(_candidates())
        pipeline._reranker = _ReverseReranker()
        return pipeline

    def test_baseline_is_pre_rerank_topk_untouched_by_blending(self):
        pipeline = self._pipeline()
        reranked, baseline = pipeline.retrieve_with_baseline(
            "q",
            top_k=3,
            retrieval_backend="local",
            rerank_enabled=True,
            rerank_weight=1.0,
            rerank_candidates=5,
        )
        # Baseline is the first 3 candidates by retrieval score, original order.
        self.assertEqual([chunk["chunk_id"] for chunk in baseline], ["c1", "c2", "c3"])
        # The reranker reverses the pool, so the top reranked chunk is the last candidate.
        self.assertEqual(reranked[0]["chunk_id"], "c5")
        # Baseline is a snapshot taken before blending mutated score/citation_id.
        self.assertEqual(baseline[0]["citation_id"], "Z1")
        self.assertAlmostEqual(baseline[0]["score"], 1.0)

    def test_two_phase_baseline_available_before_rerank(self):
        pipeline = self._pipeline()
        candidates = pipeline.retrieve_candidates(
            "q",
            top_k=3,
            retrieval_backend="local",
            rerank_enabled=True,
            rerank_weight=1.0,
            rerank_candidates=5,
        )
        # Phase 1 exposes the first-stage top_k before any reranking runs.
        self.assertTrue(candidates.rerank_active)
        self.assertEqual([chunk["chunk_id"] for chunk in candidates.baseline], ["c1", "c2", "c3"])
        # Phase 2 reorders, but the baseline snapshot stays as it was.
        reranked = pipeline.apply_rerank("q", candidates)
        self.assertEqual(reranked[0]["chunk_id"], "c5")
        self.assertEqual([chunk["chunk_id"] for chunk in candidates.baseline], ["c1", "c2", "c3"])

    def test_no_baseline_when_reranking_inactive(self):
        pipeline = self._pipeline()
        reranked, baseline = pipeline.retrieve_with_baseline(
            "q",
            top_k=3,
            retrieval_backend="local",
            rerank_enabled=False,
            rerank_weight=0.0,
        )
        self.assertEqual(baseline, [])
        self.assertEqual([chunk["chunk_id"] for chunk in reranked], ["c1", "c2", "c3"])


class RetrieveStreamEndpointTests(unittest.TestCase):
    def test_streams_msearch_rescored_sources_before_local_rerank_finishes(self):
        baseline = _candidates()[:3]
        final = list(reversed(_candidates()))[:3]
        candidates = RetrievalCandidates(
            candidates=_candidates(),
            baseline=baseline,
            rerank_active=True,
            rerank_weight=1.0,
            resolved_top_k=3,
        )

        orig_retrieve_candidates = main.pipeline.retrieve_candidates
        orig_apply_rerank_iter = main.pipeline.apply_rerank_iter
        main.pipeline.retrieve_candidates = lambda *args, **kwargs: candidates

        def fake_apply_rerank_iter(*args, **kwargs):
            yield ("eta", 2.0)
            yield ("progress", 1, 5, 0.5)
            yield ("result", final, 0.6)

        main.pipeline.apply_rerank_iter = fake_apply_rerank_iter
        try:
            client = TestClient(main.app)
            response = client.post(
                "/retrieve/stream",
                json={
                    "question": "q",
                    "retrieval_backend": "msearch",
                    "msearch_rescore": True,
                    "rerank_enabled": True,
                    "rerank_weight": 1.0,
                    "rerank_candidates": 5,
                    "top_k": 3,
                },
            )
        finally:
            main.pipeline.retrieve_candidates = orig_retrieve_candidates
            main.pipeline.apply_rerank_iter = orig_apply_rerank_iter

        self.assertEqual(response.status_code, 200, response.text)
        event_names = [
            line.removeprefix("event: ").strip()
            for line in response.text.splitlines()
            if line.startswith("event: ")
        ]
        self.assertEqual(
            event_names,
            ["preliminary_sources", "rerank_progress", "rerank_progress", "sources", "done"],
        )
        self.assertLess(response.text.index('"chunk_id": "c1"'), response.text.index('"chunk_id": "c5"'))


if __name__ == "__main__":
    unittest.main()
