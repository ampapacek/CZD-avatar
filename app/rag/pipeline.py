from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models import ChatResponse, RetrievedChunk, Source
from app.rag.catalog import save_chunk_catalog
from app.rag.chunking import chunk_documents
from app.rag.documents import load_documents
from app.rag.embeddings import SentenceTransformerEmbeddings
from app.rag.llm import OpenAICompatibleLLM
from app.rag.msearch import MSearchRetriever
from app.rag.prompts import build_messages
from app.rag.retrieval import HybridRetriever
from app.rag.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


def _shorten(text: str, limit: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


class RAGPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._embeddings: SentenceTransformerEmbeddings | None = None
        self._vector_store: QdrantVectorStore | None = None
        self._retriever: HybridRetriever | None = None
        self._msearch_retriever: MSearchRetriever | None = None
        self._llm: OpenAICompatibleLLM | None = None

    @property
    def embeddings(self) -> SentenceTransformerEmbeddings:
        if self._embeddings is None:
            logger.info("Loading embedding model: %s", self.settings.embedding_model)
            self._embeddings = SentenceTransformerEmbeddings(self.settings.embedding_model)
        return self._embeddings

    @property
    def vector_store(self) -> QdrantVectorStore:
        if self._vector_store is None:
            self._vector_store = QdrantVectorStore(
                collection=self.settings.qdrant_collection,
                vector_size=self.embeddings.dimension,
                path=self.settings.qdrant_path,
                url=self.settings.qdrant_url or None,
            )
            self._vector_store.ensure_collection(reset=False)
        return self._vector_store

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = HybridRetriever(self.embeddings, self.vector_store, self.settings.chunk_catalog_path)
        return self._retriever

    @property
    def msearch_retriever(self) -> MSearchRetriever:
        if self._msearch_retriever is None:
            self._msearch_retriever = MSearchRetriever(self.settings)
        return self._msearch_retriever

    @property
    def llm(self) -> OpenAICompatibleLLM:
        if self._llm is None:
            self._llm = OpenAICompatibleLLM(
                api_key=self.settings.llm_api_key,
                model=self.settings.llm_model,
                base_url=self.settings.llm_base_url,
            )
        return self._llm

    def ingest(self, path: Path, reset: bool = True) -> dict[str, Any]:
        logger.info("Starting ingestion from %s", path)
        documents = load_documents(path)
        chunks = chunk_documents(documents, self.settings.chunk_size, self.settings.chunk_overlap)
        self.vector_store.ensure_collection(reset=reset)
        embeddings = self.embeddings.embed_texts([chunk.text for chunk in chunks]) if chunks else []
        if chunks:
            self.vector_store.upsert_chunks(chunks, embeddings)
        save_chunk_catalog(self.settings.chunk_catalog_path, chunks)
        self._retriever = None
        logger.info("Ingestion complete: %s documents, %s chunks", len(documents), len(chunks))
        return {
            "documents_loaded": len(documents),
            "chunks_indexed": len(chunks),
            "collection": self.settings.qdrant_collection,
        }

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
        retrieval_backend: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
    ) -> list[dict[str, Any]]:
        resolved_top_k = self.settings.top_k if top_k is None else top_k
        resolved_backend = retrieval_backend or self.settings.retrieval_backend
        resolved_min_score = self.settings.min_score if min_score is None else min_score
        resolved_min_relative_score = (
            self.settings.min_relative_score if min_relative_score is None else min_relative_score
        )
        if resolved_top_k <= 0:
            logger.info(
                "Retrieved 0 chunks for question=%r top_k=%s; retrieval disabled",
                question,
                resolved_top_k,
            )
            return []

        if resolved_backend == "msearch":
            chunks = self.msearch_retriever.retrieve(
                question,
                resolved_top_k,
                collection_id=msearch_collection,
                mode=msearch_mode,
                min_confidence=msearch_min_confidence,
            )
            logger.info(
                "Retrieved %s chunks from mSearch for question=%r top_k=%s collection=%s mode=%s min_confidence=%s",
                len(chunks),
                question,
                resolved_top_k,
                msearch_collection or self.settings.msearch_collection,
                msearch_mode or self.settings.msearch_mode,
                self.settings.msearch_min_confidence if msearch_min_confidence is None else msearch_min_confidence,
            )
            return chunks

        if resolved_backend != "local":
            raise RuntimeError(f"Unknown retrieval backend: {resolved_backend}")

        chunks = self.retriever.retrieve(
            question,
            resolved_top_k,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            min_score=resolved_min_score,
            min_relative_score=resolved_min_relative_score,
        )
        logger.info(
            "Retrieved %s chunks for question=%r top_k=%s dense_weight=%.3f bm25_weight=%.3f min_score=%s min_relative_score=%s",
            len(chunks),
            question,
            resolved_top_k,
            dense_weight,
            bm25_weight,
            resolved_min_score,
            resolved_min_relative_score,
        )
        if chunks:
            logger.info(
                "Top retrieved: %s",
                [
                    {
                        "citation_id": chunk.get("citation_id"),
                        "title": chunk.get("metadata", {}).get("title"),
                        "score": round(float(chunk.get("score") or 0.0), 3),
                    }
                    for chunk in chunks[:5]
                ],
            )
        return chunks

    def chat(
        self,
        question: str,
        style: str,
        length: str,
        custom_instructions: str | None = None,
        system_prompt: str | None = None,
        user_prompt_template: str | None = None,
        style_prompts: dict[str, str] | None = None,
        length_prompts: dict[str, str] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int | None = None,
        model: str | None = None,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
        retrieval_backend: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
    ) -> ChatResponse:
        started = time.perf_counter()
        resolved_model = model or self.llm.model
        retrieved = self.retrieve(
            question,
            top_k,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            min_score=min_score,
            min_relative_score=min_relative_score,
            retrieval_backend=retrieval_backend,
            msearch_collection=msearch_collection,
            msearch_mode=msearch_mode,
            msearch_min_confidence=msearch_min_confidence,
        )
        messages = build_messages(
            question,
            retrieved,
            style,
            length,
            custom_instructions,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            style_prompts=style_prompts,
            length_prompts=length_prompts,
            conversation_history=conversation_history,
        )
        generation = self.llm.generate(
            messages,
            model=resolved_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        answer = generation.answer
        upstream_model = generation.model or resolved_model
        elapsed = time.perf_counter() - started
        logger.info(
            "Generated answer question=%r style=%s length=%s custom=%r model=%s response_time=%.2fs answer=%s",
            question,
            style,
            length,
            custom_instructions,
            resolved_model,
            elapsed,
            _shorten(answer),
        )
        return ChatResponse(
            answer=answer,
            sources=[_source_from_chunk(chunk) for chunk in retrieved],
            retrieved_chunks=[_retrieved_chunk_from_record(chunk) for chunk in retrieved],
            model=resolved_model,
            upstream_model=upstream_model,
            response_time_seconds=round(elapsed, 3),
        )

    def close(self) -> None:
        if self._vector_store is not None:
            logger.info("Closing vector store")
            self._vector_store.close()
            self._vector_store = None


def _retrieved_chunk_from_record(record: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        citation_id=record.get("citation_id", ""),
        chunk_id=record.get("chunk_id", ""),
        text=record.get("text", ""),
        metadata=record.get("metadata", {}),
        score=float(record.get("score") or 0.0),
        dense_score=float(record["dense_score"]) if record.get("dense_score") is not None else None,
        bm25_score=float(record["bm25_score"]) if record.get("bm25_score") is not None else None,
    )


def _source_from_chunk(record: dict[str, Any]) -> Source:
    metadata = record.get("metadata", {})
    return Source(
        citation_id=record.get("citation_id", ""),
        chunk_id=record.get("chunk_id", ""),
        source_kind=metadata.get("source_kind"),
        title=metadata.get("title"),
        source_path=metadata.get("source_path"),
        source_path_display=metadata.get("source_path_display"),
        page_number=metadata.get("page_number"),
        url=metadata.get("url"),
        document_url=metadata.get("document_url"),
        source_url=metadata.get("source_url"),
        source_name=metadata.get("source_name"),
        score=float(record.get("score") or 0.0),
    )
