import unittest

from app.config import get_settings
from app.rag.pipeline import RAGPipeline
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


if __name__ == "__main__":
    unittest.main()
