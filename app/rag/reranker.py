from __future__ import annotations

import logging
import time
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)


class RerankEtaEstimator:
    """Cross-run estimate of reranking time, normalized by candidate text size.

    Reranking cost scales with how much text the cross-encoder must read, so we
    track an exponentially weighted moving average of seconds-per-character over
    the whole candidate set. ``seed_seconds`` turns that into an up-front ETA for
    the next run; it returns ``None`` until at least one run has completed, which
    is why the very first reranking shows no estimate. Within a run the estimate
    is refined per batch from the actual elapsed time, so this only provides the
    starting point.

    State is in-memory and resets on process restart by design.
    """

    def __init__(self, alpha: float = 0.3) -> None:
        self.alpha = alpha
        self._seconds_per_char: float | None = None

    @staticmethod
    def _total_chars(texts: list[str]) -> int:
        # Floor at 1 so a degenerate empty candidate set can't divide by zero.
        return sum(len(text or "") for text in texts) or 1

    def seed_seconds(self, texts: list[str]) -> float | None:
        if self._seconds_per_char is None:
            return None
        return self._seconds_per_char * self._total_chars(texts)

    def update(self, seconds: float, texts: list[str]) -> None:
        rate = seconds / self._total_chars(texts)
        if self._seconds_per_char is None:
            self._seconds_per_char = rate
        else:
            self._seconds_per_char = (1.0 - self.alpha) * self._seconds_per_char + self.alpha * rate


def reranker_model_available(model_name: str) -> bool:
    """Return True only if the reranker model can load without a download.

    Checks a local directory path first, then the Hugging Face cache for a
    complete snapshot (config + weights). Used to hide the reranking controls
    when the model is not present, since downloading it on first use is slow.
    """
    if not model_name:
        return False
    if Path(model_name).expanduser().exists():
        return True
    try:
        from huggingface_hub import try_to_load_from_cache
    except Exception:
        return False

    def cached(filename: str) -> bool:
        return isinstance(try_to_load_from_cache(model_name, filename), str)

    if not cached("config.json"):
        return False
    return cached("model.safetensors") or cached("pytorch_model.bin")


class CrossEncoderReranker:
    """Cross-encoder reranking over first-stage retrieval candidates.

    The cross-encoder scores each (question, chunk) pair jointly, which is more
    accurate than the bi-encoder/BM25 first stage but also slower, so it only
    runs on the small candidate pool returned by retrieval. Its score is blended
    with the first-stage score by ``weight`` (0 = ignore reranker, 1 = trust it
    entirely) and the candidates are re-sorted and truncated to ``top_k``.
    """

    def __init__(
        self,
        model_name: str,
        *,
        max_length: int = 512,
        batch_size: int = 16,
        device: str = "",
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device or None

    @cached_property
    def model(self):
        # Imported lazily so the heavy torch/transformers load only happens when
        # reranking is actually used (the default msearch flow never touches it).
        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder reranker: %s", self.model_name)
        # local_files_only=True: the model must be pre-downloaded by a developer
        # (see README). Reranking never fetches it on demand, so an end user can
        # never trigger a multi-gigabyte download from the UI. If it is missing
        # this raises instead of downloading — and reranker_model_available() keeps
        # the controls hidden so that path is not reachable in normal use.
        return CrossEncoder(
            self.model_name,
            max_length=self.max_length,
            device=self.device,
            local_files_only=True,
        )

    def score_pairs(self, question: str, texts: list[str]) -> list[float]:
        pairs = [(question, text or "") for text in texts]
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        return [float(score) for score in scores]

    def rerank(
        self,
        question: str,
        records: list[dict[str, Any]],
        weight: float,
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return records[:top_k]
        rerank_scores = self.score_pairs(question, [record.get("text", "") for record in records])
        return blend_and_rank(records, rerank_scores, weight, top_k)

    def rerank_iter(
        self,
        question: str,
        records: list[dict[str, Any]],
        weight: float,
        top_k: int,
    ) -> Iterator[tuple]:
        """Rerank one batch at a time so a caller can stream progress.

        Yields ``("progress", scored_pairs, total_pairs, elapsed_seconds)`` after
        each batch, then a final ``("result", ranked_records)``. Scoring the pairs
        in explicit ``batch_size`` chunks (instead of one ``model.predict`` call)
        is what lets the elapsed time be sampled mid-run for a live ETA.
        """
        if not records or top_k <= 0:
            yield ("result", records[:top_k])
            return
        pairs = [(question, record.get("text", "") or "") for record in records]
        total = len(pairs)
        scores: list[float] = []
        started = time.perf_counter()
        for start in range(0, total, self.batch_size):
            batch = pairs[start : start + self.batch_size]
            batch_scores = self.model.predict(batch, batch_size=self.batch_size, show_progress_bar=False)
            scores.extend(float(score) for score in batch_scores)
            yield ("progress", len(scores), total, time.perf_counter() - started)
        yield ("result", blend_and_rank(records, scores, weight, top_k))


def blend_and_rank(
    records: list[dict[str, Any]],
    rerank_scores: list[float],
    weight: float,
    top_k: int,
) -> list[dict[str, Any]]:
    """Blend first-stage and reranker scores, then sort and truncate to top_k.

    Both signals are min-max normalized across the candidate set so the blend
    weight is meaningful regardless of each model's raw score scale.
    """
    if not records:
        return []
    weight = min(max(weight, 0.0), 1.0)
    retrieval_norm = _minmax([float(record.get("score") or 0.0) for record in records])
    rerank_norm = _minmax([float(score) for score in rerank_scores])
    for record, raw, retrieval_n, rerank_n in zip(records, rerank_scores, retrieval_norm, rerank_norm, strict=True):
        record["retrieval_score"] = record.get("score")
        record["rerank_score"] = float(raw)
        record["score"] = (1.0 - weight) * retrieval_n + weight * rerank_n
    ranked = sorted(records, key=lambda record: float(record.get("score") or 0.0), reverse=True)[:top_k]
    for index, record in enumerate(ranked, start=1):
        record["citation_id"] = f"Z{index}"
    return ranked


def _minmax(scores: list[float]) -> list[float]:
    if not scores:
        return []
    highest = max(scores)
    lowest = min(scores)
    if highest == lowest:
        return [1.0 if highest > 0 else 0.0 for _ in scores]
    span = highest - lowest
    return [(score - lowest) / span for score in scores]
