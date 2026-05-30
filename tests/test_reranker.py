import unittest

from app.rag.reranker import blend_and_rank


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


if __name__ == "__main__":
    unittest.main()
