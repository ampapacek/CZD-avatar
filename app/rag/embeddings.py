from __future__ import annotations

from functools import cached_property

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingProvider:
    """Small abstraction so local/API embedding providers can be swapped later."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


class SentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    @cached_property
    def dimension(self) -> int:
        vector = self.embed_query("test")
        return len(vector)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 32,
        )
        return _to_list(embeddings)

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
        return _to_list(embedding)


def _to_list(value: np.ndarray | list[float] | list[list[float]]) -> list[float] | list[list[float]]:
    if isinstance(value, np.ndarray):
        return value.astype(float).tolist()
    return value

