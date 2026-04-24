from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from app.rag.catalog import load_chunk_catalog
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore


TOKEN_RE = re.compile(r"[\wÁ-ž]+", flags=re.UNICODE)


class HybridRetriever:
    """Dense Qdrant retrieval plus BM25 over the persisted chunk catalog."""

    def __init__(self, embeddings: EmbeddingProvider, vector_store: QdrantVectorStore, catalog_path: Path) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.catalog_path = catalog_path
        self._catalog: list[dict[str, Any]] | None = None
        self._bm25: BM25Okapi | None = None

    def retrieve(
        self,
        question: str,
        top_k: int,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        dense_weight, bm25_weight = _normalize_weights(dense_weight, bm25_weight)
        dense_limit = max(top_k * 3, top_k)
        dense = self.vector_store.search(self.embeddings.embed_query(question), limit=dense_limit)
        bm25 = self._bm25_search(question, limit=dense_limit)

        merged: dict[str, dict[str, Any]] = {}
        for record in _normalize_scores(dense):
            item = dict(record)
            item["score"] = dense_weight * record["score"]
            item["dense_score"] = record["score"]
            item["bm25_score"] = 0.0
            merged[item["chunk_id"]] = item

        for record in _normalize_scores(bm25):
            existing = merged.get(record["chunk_id"])
            if existing:
                existing["score"] += bm25_weight * record["score"]
                existing["bm25_score"] = record["score"]
            else:
                item = dict(record)
                item["score"] = bm25_weight * record["score"]
                item["dense_score"] = 0.0
                item["bm25_score"] = record["score"]
                merged[item["chunk_id"]] = item

        ranked = sorted(merged.values(), key=lambda item: item["score"], reverse=True)
        ranked = _filter_by_thresholds(ranked, min_score, min_relative_score)
        for index, item in enumerate(ranked[:top_k], start=1):
            item["citation_id"] = f"Z{index}"
        return ranked[:top_k]

    def _bm25_search(self, question: str, limit: int) -> list[dict[str, Any]]:
        catalog = self._load_catalog()
        if not catalog:
            return []
        bm25 = self._load_bm25()
        scores = bm25.get_scores(_tokenize(question))
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)[:limit]
        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            record = catalog[idx]
            results.append(
                {
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "metadata": record.get("metadata", {}),
                    "score": score,
                }
            )
        return results

    def _load_catalog(self) -> list[dict[str, Any]]:
        if self._catalog is None:
            self._catalog = load_chunk_catalog(self.catalog_path)
        return self._catalog

    def _load_bm25(self) -> BM25Okapi:
        if self._bm25 is None:
            tokenized = [_tokenize(record["text"]) for record in self._load_catalog()]
            self._bm25 = BM25Okapi(tokenized)
        return self._bm25


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def _normalize_scores(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []
    scores = [float(record.get("score") or 0.0) for record in records]
    max_score = max(scores)
    min_score = min(scores)
    normalized = []
    for record, score in zip(records, scores, strict=True):
        item = dict(record)
        if math.isclose(max_score, min_score):
            item["score"] = 1.0 if max_score > 0 else 0.0
        else:
            item["score"] = (score - min_score) / (max_score - min_score)
        normalized.append(item)
    return normalized


def _normalize_weights(dense_weight: float, bm25_weight: float) -> tuple[float, float]:
    total = dense_weight + bm25_weight
    if total <= 0:
        return 0.7, 0.3
    return dense_weight / total, bm25_weight / total


def _filter_by_thresholds(
    records: list[dict[str, Any]],
    min_score: float | None,
    min_relative_score: float | None,
) -> list[dict[str, Any]]:
    if not records:
        return []
    best_score = float(records[0].get("score") or 0.0)
    filtered = records
    if min_score is not None:
        filtered = [record for record in filtered if float(record.get("score") or 0.0) >= min_score]
    if min_relative_score is not None and best_score > 0:
        threshold = best_score * min_relative_score
        filtered = [record for record in filtered if float(record.get("score") or 0.0) >= threshold]
    return filtered
