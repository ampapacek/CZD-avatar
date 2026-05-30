import unittest

from app.rag.reranker import CrossEncoderReranker, RerankEtaEstimator, blend_and_rank


def _records():
    # Retrieval order is c1 > c2 > c3; the reranker strongly disagrees and
    # considers c3 the most relevant.
    return [
        {"chunk_id": "c1", "text": "a", "score": 0.9},
        {"chunk_id": "c2", "text": "b", "score": 0.6},
        {"chunk_id": "c3", "text": "c", "score": 0.3},
    ]


class BlendAndRankTests(unittest.TestCase):
    def test_full_weight_follows_reranker_order(self) -> None:
        ranked = blend_and_rank(_records(), rerank_scores=[0.0, 1.0, 5.0], weight=1.0, top_k=3)

        self.assertEqual([r["chunk_id"] for r in ranked], ["c3", "c2", "c1"])
        # Citation ids are reassigned to the new order.
        self.assertEqual([r["citation_id"] for r in ranked], ["Z1", "Z2", "Z3"])
        # Original retrieval score is preserved for transparency.
        self.assertEqual(ranked[0]["retrieval_score"], 0.3)
        self.assertEqual(ranked[0]["rerank_score"], 5.0)

    def test_zero_weight_keeps_retrieval_order(self) -> None:
        ranked = blend_and_rank(_records(), rerank_scores=[0.0, 1.0, 5.0], weight=0.0, top_k=3)

        self.assertEqual([r["chunk_id"] for r in ranked], ["c1", "c2", "c3"])

    def test_truncates_to_top_k(self) -> None:
        ranked = blend_and_rank(_records(), rerank_scores=[0.0, 1.0, 5.0], weight=1.0, top_k=2)

        self.assertEqual([r["chunk_id"] for r in ranked], ["c3", "c2"])


class RerankEtaEstimatorTests(unittest.TestCase):
    def test_seed_is_none_until_first_run_completes(self) -> None:
        estimator = RerankEtaEstimator()
        self.assertIsNone(estimator.seed_seconds(["abcd", "ef"]))

    def test_seed_scales_with_candidate_text_size(self) -> None:
        estimator = RerankEtaEstimator()
        # 10 chars took 2s -> 0.2 s/char.
        estimator.update(2.0, ["aaaaa", "bbbbb"])
        # A 5-char candidate set should be estimated at half the time.
        self.assertAlmostEqual(estimator.seed_seconds(["ccccc"]), 1.0)

    def test_update_blends_toward_new_observations(self) -> None:
        estimator = RerankEtaEstimator(alpha=0.5)
        estimator.update(2.0, ["a" * 10])  # 0.2 s/char
        estimator.update(0.0, ["a" * 10])  # 0.0 s/char, blended 50/50 -> 0.1
        self.assertAlmostEqual(estimator.seed_seconds(["a" * 10]), 1.0)


class _StubModel:
    """Minimal CrossEncoder stand-in that scores by text length per batch."""

    def __init__(self) -> None:
        self.batch_calls: list[int] = []

    def predict(self, pairs, batch_size=16, show_progress_bar=False):
        self.batch_calls.append(len(pairs))
        return [float(len(text)) for _, text in pairs]


class RerankIterTests(unittest.TestCase):
    def _reranker(self) -> CrossEncoderReranker:
        reranker = CrossEncoderReranker("stub", batch_size=2)
        reranker.__dict__["model"] = _StubModel()  # bypass the cached_property loader
        return reranker

    def test_yields_progress_per_batch_then_result(self) -> None:
        reranker = self._reranker()
        records = [{"chunk_id": f"c{i}", "text": "x" * i, "score": 1.0 / (i + 1)} for i in range(5)]

        events = list(reranker.rerank_iter("q", records, weight=1.0, top_k=5))

        progress = [e for e in events if e[0] == "progress"]
        results = [e for e in events if e[0] == "result"]
        # 5 records at batch_size 2 -> 3 batches -> 3 progress events.
        self.assertEqual([(e[1], e[2]) for e in progress], [(2, 5), (4, 5), (5, 5)])
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][1]), 5)

    def test_empty_records_yield_single_result(self) -> None:
        reranker = self._reranker()
        events = list(reranker.rerank_iter("q", [], weight=1.0, top_k=5))
        self.assertEqual(events, [("result", [])])


if __name__ == "__main__":
    unittest.main()
