from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.rag.chunking import Chunk


class QdrantVectorStore:
    """Qdrant wrapper with local path mode for MVP and URL mode for deployment."""

    def __init__(self, collection: str, vector_size: int, path: Path | None = None, url: str | None = None) -> None:
        self.collection = collection
        self.vector_size = vector_size
        if url:
            self.client = QdrantClient(url=url)
        else:
            path = path or Path("data/qdrant")
            path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))

    def ensure_collection(self, reset: bool = False) -> None:
        exists = self._collection_exists()
        if reset and exists:
            self.client.delete_collection(self.collection)
            exists = False
        if not exists:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]], batch_size: int = 64) -> None:
        for start in range(0, len(chunks), batch_size):
            points = []
            for chunk, vector in zip(chunks[start : start + batch_size], embeddings[start : start + batch_size], strict=True):
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }
                points.append(PointStruct(id=_point_id(chunk.chunk_id), vector=vector, payload=payload))
            self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], limit: int) -> list[dict[str, Any]]:
        try:
            result = self.client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            points = result.points
        except (AttributeError, TypeError):
            points = self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
        return [
            {
                "chunk_id": point.payload.get("chunk_id"),
                "text": point.payload.get("text"),
                "metadata": point.payload.get("metadata", {}),
                "score": float(point.score),
            }
            for point in points
            if point.payload
        ]

    def _collection_exists(self) -> bool:
        try:
            return self.client.collection_exists(self.collection)
        except (AttributeError, UnexpectedResponse):
            try:
                self.client.get_collection(self.collection)
                return True
            except Exception:
                return False

    def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            close()


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
