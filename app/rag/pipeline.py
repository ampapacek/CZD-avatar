from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models import ChatResponse, RetrievedChunk, Source
from app.rag.catalog import save_chunk_catalog
from app.rag.chunking import chunk_documents
from app.rag.documents import load_documents
from app.rag.embeddings import SentenceTransformerEmbeddings
from app.rag.llm import OpenAICompatibleLLM
from app.rag.llm_providers import available_llm_providers, provider_api_key, provider_preset, resolve_llm_provider
from app.rag.msearch import MSearchRetriever
from app.rag.reranker import CrossEncoderReranker, RerankEtaEstimator
from app.rag.retrieval import HybridRetriever
from app.rag.token_budget import (
    PromptBudgetConfig,
    conversation_history_tokens,
    prepare_prompt_budget,
    summarized_history,
)
from app.rag.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalCandidates:
    """First-stage retrieval result, before the cross-encoder reorders it.

    Splitting retrieval from reranking lets the streaming endpoint show the
    first-stage ``baseline`` immediately and swap in the reranked order once the
    (slower) cross-encoder finishes.
    """

    candidates: list[dict[str, Any]] = field(default_factory=list)
    # Pre-rerank top_k snapshot (deep-copied so later blending can't mutate it).
    # Empty when reranking is inactive.
    baseline: list[dict[str, Any]] = field(default_factory=list)
    rerank_active: bool = False
    rerank_weight: float = 0.0
    resolved_top_k: int = 0


def _shorten(text: str, limit: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _clean_retrieval_query(text: str) -> str:
    query = " ".join((text or "").split()).strip()
    if len(query) >= 2 and query[0] == query[-1] and query[0] in {'"', "'", "`"}:
        query = query[1:-1].strip()
    for prefix in ("Dotaz:", "Query:", "Search query:", "Vyhledávací dotaz:"):
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix) :].strip()
    return query


class RAGPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._embeddings: SentenceTransformerEmbeddings | None = None
        self._vector_store: QdrantVectorStore | None = None
        self._retriever: HybridRetriever | None = None
        self._msearch_retriever: MSearchRetriever | None = None
        self._reranker: CrossEncoderReranker | None = None
        self._rerank_eta = RerankEtaEstimator()
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
    def reranker(self) -> CrossEncoderReranker:
        if self._reranker is None:
            self._reranker = CrossEncoderReranker(
                self.settings.reranker_model,
                max_length=self.settings.reranker_max_length,
                batch_size=self.settings.reranker_batch_size,
                device=self.settings.reranker_device,
            )
        return self._reranker

    @property
    def llm(self) -> OpenAICompatibleLLM:
        if self._llm is None:
            provider_presets = available_llm_providers()
            provider_id = resolve_llm_provider(self.settings.llm_provider, provider_presets)
            provider_config = provider_preset(provider_id, provider_presets)
            self._llm = OpenAICompatibleLLM(
                api_key=provider_api_key(provider_id, provider_presets),
                model=str(provider_config.get("default_model") or ""),
                base_url=str(provider_config.get("base_url") or ""),
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
        llm_provider: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
        msearch_rescore: bool | None = None,
        rerank_enabled: bool | None = None,
        rerank_weight: float | None = None,
        rerank_candidates: int | None = None,
    ) -> list[dict[str, Any]]:
        chunks, _ = self.retrieve_with_baseline(
            question,
            top_k,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            min_score=min_score,
            min_relative_score=min_relative_score,
            retrieval_backend=retrieval_backend,
            llm_provider=llm_provider,
            msearch_collection=msearch_collection,
            msearch_mode=msearch_mode,
            msearch_min_confidence=msearch_min_confidence,
            msearch_rescore=msearch_rescore,
            rerank_enabled=rerank_enabled,
            rerank_weight=rerank_weight,
            rerank_candidates=rerank_candidates,
        )
        return chunks

    def retrieve_with_baseline(
        self,
        question: str,
        top_k: int | None = None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
        retrieval_backend: str | None = None,
        llm_provider: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
        msearch_rescore: bool | None = None,
        rerank_enabled: bool | None = None,
        rerank_weight: float | None = None,
        rerank_candidates: int | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Retrieve chunks and, when reranking is active, the pre-rerank ordering.

        The second list is the top_k the user would have seen without the local
        cross-encoder (a snapshot taken before blending), so the UI can show the
        two orderings side by side. It is empty when local reranking is inactive.
        Note that when ``msearch_rescore`` is on, the candidate pool is already
        cross-encoder-reordered by mSearch, so the baseline reflects that order and
        the local rerank only shows what it adds on top.
        """
        candidates = self.retrieve_candidates(
            question,
            top_k,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            min_score=min_score,
            min_relative_score=min_relative_score,
            retrieval_backend=retrieval_backend,
            llm_provider=llm_provider,
            msearch_collection=msearch_collection,
            msearch_mode=msearch_mode,
            msearch_min_confidence=msearch_min_confidence,
            msearch_rescore=msearch_rescore,
            rerank_enabled=rerank_enabled,
            rerank_weight=rerank_weight,
            rerank_candidates=rerank_candidates,
        )
        reranked = self.apply_rerank(question, candidates)
        return reranked, candidates.baseline

    def retrieve_candidates(
        self,
        question: str,
        top_k: int | None = None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
        retrieval_backend: str | None = None,
        llm_provider: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
        msearch_rescore: bool | None = None,
        rerank_enabled: bool | None = None,
        rerank_weight: float | None = None,
        rerank_candidates: int | None = None,
    ) -> RetrievalCandidates:
        """Run only the first stage and snapshot the pre-rerank top_k.

        Reranking is deferred to :meth:`apply_rerank` so callers (e.g. the
        streaming endpoint) can surface the baseline before the cross-encoder runs.
        """
        resolved_top_k = self.settings.top_k if top_k is None else top_k
        resolved_backend = retrieval_backend or self.settings.retrieval_backend
        resolved_min_score = self.settings.min_score if min_score is None else min_score
        resolved_min_relative_score = (
            self.settings.min_relative_score if min_relative_score is None else min_relative_score
        )
        effective_msearch_collection = msearch_collection or self.settings.msearch_collection
        if resolved_top_k <= 0:
            logger.info(
                "Retrieved 0 chunks for question=%r top_k=%s; retrieval disabled",
                question,
                resolved_top_k,
            )
            return RetrievalCandidates()

        resolved_rerank_weight = self.settings.reranker_weight if rerank_weight is None else rerank_weight
        rerank_active = (
            self.settings.reranker_enabled if rerank_enabled is None else rerank_enabled
        ) and resolved_rerank_weight > 0
        resolved_candidates = self.settings.reranker_candidates if rerank_candidates is None else rerank_candidates
        # When reranking, pull a larger candidate pool for the cross-encoder to
        # reorder, then truncate back to top_k after blending.
        candidate_k = max(resolved_top_k, resolved_candidates) if rerank_active else resolved_top_k

        if resolved_backend == "msearch":
            resolved_msearch_rescore = (
                self.settings.msearch_rescore if msearch_rescore is None else msearch_rescore
            )
            chunks = self.msearch_retriever.retrieve(
                question,
                candidate_k,
                collection_id=effective_msearch_collection,
                mode=msearch_mode,
                min_confidence=msearch_min_confidence,
                min_score=resolved_min_score,
                min_relative_score=resolved_min_relative_score,
                rescore_method="cross_encoder" if resolved_msearch_rescore else None,
            )
            logger.info(
                "Retrieved %s chunks from mSearch for question=%r top_k=%s candidates=%s collection=%s mode=%s min_confidence=%s rescore=%s",
                len(chunks),
                question,
                resolved_top_k,
                candidate_k,
                effective_msearch_collection,
                msearch_mode or self.settings.msearch_mode,
                self.settings.msearch_min_confidence if msearch_min_confidence is None else msearch_min_confidence,
                "cross_encoder" if resolved_msearch_rescore else "none",
            )
        elif resolved_backend == "local":
            chunks = self.retriever.retrieve(
                question,
                candidate_k,
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
        else:
            raise RuntimeError(f"Unknown retrieval backend: {resolved_backend}")

        # Snapshot the pre-rerank top_k before apply_rerank mutates the records
        # in place (it rewrites score/citation_id during blending).
        baseline = [copy.deepcopy(chunk) for chunk in chunks[:resolved_top_k]] if rerank_active else []
        return RetrievalCandidates(
            candidates=chunks,
            baseline=baseline,
            rerank_active=rerank_active,
            rerank_weight=resolved_rerank_weight,
            resolved_top_k=resolved_top_k,
        )

    def apply_rerank(self, question: str, candidates: RetrievalCandidates) -> list[dict[str, Any]]:
        """Blend in the cross-encoder (when active) and truncate to top_k."""
        chunks = self._maybe_rerank(
            question,
            candidates.candidates,
            candidates.rerank_active,
            candidates.rerank_weight,
            candidates.resolved_top_k,
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

    def apply_rerank_iter(self, question: str, candidates: RetrievalCandidates):
        """Streaming variant of :meth:`apply_rerank` for the SSE endpoint.

        Yields ``("eta", seed_seconds | None)`` once up front, then
        ``("progress", done, total, elapsed)`` per batch, and finally
        ``("result", chunks, rerank_seconds)``. The seed comes from the cross-run
        ETA estimator (``None`` on the first ever run) and the measured duration
        feeds back into it so later runs start with a sharper estimate.
        """
        if not candidates.rerank_active or not candidates.candidates:
            yield ("result", candidates.candidates[: candidates.resolved_top_k], 0.0)
            return

        texts = [record.get("text", "") for record in candidates.candidates]
        yield ("eta", self._rerank_eta.seed_seconds(texts))

        started = time.perf_counter()
        result: list[dict[str, Any]] = []
        for event in self.reranker.rerank_iter(
            question, candidates.candidates, candidates.rerank_weight, candidates.resolved_top_k
        ):
            if event[0] == "result":
                result = event[1]
            else:
                yield event
        elapsed = time.perf_counter() - started
        self._rerank_eta.update(elapsed, texts)
        logger.info(
            "Reranked %s candidates to %s chunks for question=%r weight=%.2f model=%s elapsed=%.2fs",
            len(candidates.candidates),
            len(result),
            question,
            candidates.rerank_weight,
            self.settings.reranker_model,
            elapsed,
        )
        if result:
            logger.info(
                "Top retrieved: %s",
                [
                    {
                        "citation_id": chunk.get("citation_id"),
                        "title": chunk.get("metadata", {}).get("title"),
                        "score": round(float(chunk.get("score") or 0.0), 3),
                    }
                    for chunk in result[:5]
                ],
            )
        yield ("result", result, elapsed)

    def _maybe_rerank(
        self,
        question: str,
        chunks: list[dict[str, Any]],
        rerank_active: bool,
        weight: float,
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not rerank_active or not chunks:
            return chunks[:top_k]
        started = time.perf_counter()
        reranked = self.reranker.rerank(question, chunks, weight, top_k)
        logger.info(
            "Reranked %s candidates to %s chunks for question=%r weight=%.2f model=%s elapsed=%.2fs",
            len(chunks),
            len(reranked),
            question,
            weight,
            self.settings.reranker_model,
            time.perf_counter() - started,
        )
        return reranked

    def chat(
        self,
        question: str,
        length: str,
        placeholder_defs: dict[str, Any] | None = None,
        selections: dict[str, str] | None = None,
        system_prompt: str | None = None,
        user_prompt_template: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        conversation_summary: str | None = None,
        top_k: int | None = None,
        model: str | None = None,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
        llm_provider: str | None = None,
        context_window_tokens: int | None = None,
        output_token_budget_short: int | None = None,
        output_token_budget_medium: int | None = None,
        output_token_budget_long: int | None = None,
        min_prompt_chunks: int | None = None,
        token_budget_safety_margin: float | None = None,
        conversation_summary_trigger_tokens: int | None = None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        min_score: float | None = None,
        min_relative_score: float | None = None,
        retrieval_backend: str | None = None,
        msearch_collection: str | None = None,
        msearch_mode: str | None = None,
        msearch_min_confidence: float | None = None,
        msearch_rescore: bool | None = None,
        rerank_enabled: bool | None = None,
        rerank_weight: float | None = None,
        rerank_candidates: int | None = None,
        rewrite_query_for_retrieval: bool = False,
    ) -> ChatResponse:
        started = time.perf_counter()
        resolved_model = model or self.llm.model
        budget_config = PromptBudgetConfig.from_settings(
            self.settings,
            context_window_tokens=context_window_tokens,
            output_token_budget_short=output_token_budget_short,
            output_token_budget_medium=output_token_budget_medium,
            output_token_budget_long=output_token_budget_long,
            min_prompt_chunks=min_prompt_chunks,
            token_budget_safety_margin=token_budget_safety_margin,
            conversation_summary_trigger_tokens=conversation_summary_trigger_tokens,
        )
        effective_history, effective_summary, summary_warning = self._resolve_conversation_context(
            conversation_history or [],
            conversation_summary=conversation_summary,
            model=resolved_model,
            budget_config=budget_config,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        retrieval_query = self.rewrite_query_for_retrieval(
            question,
            conversation_history=conversation_history or [],
            conversation_summary=conversation_summary,
            enabled=rewrite_query_for_retrieval,
            model=resolved_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        retrieved, baseline_retrieved = self.retrieve_with_baseline(
            retrieval_query,
            top_k,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            min_score=min_score,
            min_relative_score=min_relative_score,
            retrieval_backend=retrieval_backend,
            llm_provider=llm_provider,
            msearch_collection=msearch_collection,
            msearch_mode=msearch_mode,
            msearch_min_confidence=msearch_min_confidence,
            msearch_rescore=msearch_rescore,
            rerank_enabled=rerank_enabled,
            rerank_weight=rerank_weight,
            rerank_candidates=rerank_candidates,
        )
        budget = prepare_prompt_budget(
            question=question,
            retrieved_chunks=retrieved,
            length=length,
            model=resolved_model,
            config=budget_config,
            placeholder_defs=placeholder_defs,
            selections=selections,
            conversation_history=effective_history,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
        )
        if summary_warning:
            budget.warnings.append(summary_warning)
        budget.conversation_summary_used = bool(effective_summary)
        generation = self.llm.generate(
            budget.messages,
            model=resolved_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        answer = generation.answer
        upstream_model = generation.model or resolved_model
        elapsed = time.perf_counter() - started
        logger.info(
            "Generated answer question=%r retrieval_query=%r length=%s model=%s response_time=%.2fs answer=%s",
            question,
            retrieval_query,
            length,
            resolved_model,
            elapsed,
            _shorten(answer),
        )
        return ChatResponse(
            answer=answer,
            original_question=question,
            retrieval_query=retrieval_query,
            retrieval_query_was_rewritten=retrieval_query != question,
            sources=[_source_from_chunk(chunk) for chunk in budget.used_chunks],
            retrieved_chunks=[_retrieved_chunk_from_record(chunk) for chunk in budget.used_chunks],
            used_chunks=[_retrieved_chunk_from_record(chunk) for chunk in budget.used_chunks],
            omitted_chunks=[_retrieved_chunk_from_record(chunk) for chunk in budget.omitted_chunks],
            baseline_chunks=[_retrieved_chunk_from_record(chunk) for chunk in baseline_retrieved],
            token_budget=budget.metadata(),
            chunk_budget_warnings=budget.warnings,
            conversation_summary=effective_summary,
            model=resolved_model,
            upstream_model=upstream_model,
            response_time_seconds=round(elapsed, 3),
        )

    def build_chat_prompt(
        self,
        *,
        question: str,
        retrieved: list[dict[str, Any]],
        length: str,
        model: str,
        placeholder_defs: dict[str, Any] | None = None,
        selections: dict[str, str] | None = None,
        system_prompt: str | None = None,
        user_prompt_template: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        conversation_summary: str | None = None,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
        budget_config: PromptBudgetConfig | None = None,
    ):
        resolved_config = budget_config or PromptBudgetConfig.from_settings(self.settings)
        effective_history, effective_summary, summary_warning = self._resolve_conversation_context(
            conversation_history or [],
            conversation_summary=conversation_summary,
            model=model,
            budget_config=resolved_config,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        budget = prepare_prompt_budget(
            question=question,
            retrieved_chunks=retrieved,
            length=length,
            model=model,
            config=resolved_config,
            placeholder_defs=placeholder_defs,
            selections=selections,
            conversation_history=effective_history,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
        )
        if summary_warning:
            budget.warnings.append(summary_warning)
        budget.conversation_summary_used = bool(effective_summary)
        return budget, effective_summary

    def rewrite_query_for_retrieval(
        self,
        question: str,
        *,
        conversation_history: list[dict[str, str]] | None,
        conversation_summary: str | None,
        enabled: bool,
        model: str,
        api_key: str | None,
        base_url: str | None,
    ) -> str:
        clean_question = question.strip()
        if not enabled or not clean_question or not conversation_history:
            return clean_question

        context_parts: list[str] = []
        clean_summary = (conversation_summary or "").strip()
        if clean_summary:
            context_parts.append(f"Shrnutí konverzace:\n{clean_summary}")

        recent_turns = []
        for turn in conversation_history[-8:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                label = "Uživatel" if role == "user" else "Avatar"
                recent_turns.append(f"{label}: {content}")
        if recent_turns:
            context_parts.append("Nedávné zprávy:\n" + "\n".join(recent_turns))
        if not context_parts:
            return clean_question

        messages = [
            {
                "role": "system",
                "content": (
                    "Rewrite the latest user message into one standalone search query for document retrieval. "
                    "Use only the provided conversation context. Include relevant names, events, dates, places, "
                    "and concepts only when they appear in the context or are directly referred to by the latest "
                    "message. Do not answer the question. Do not add outside facts or assumptions. Keep the same "
                    "language as the latest user message. Return only the query text. If the latest message is "
                    "already standalone, return it unchanged."
                ),
            },
            {
                "role": "user",
                "content": "\n\n".join(context_parts) + f"\n\nNejnovější zpráva uživatele:\n{clean_question}",
            },
        ]
        try:
            generation = self.llm.generate(messages, model=model, api_key=api_key, base_url=base_url)
        except Exception as exc:
            logger.warning("Retrieval query rewrite failed for question=%r: %s", clean_question, exc)
            return clean_question

        rewritten = _clean_retrieval_query(generation.answer)
        if not rewritten:
            return clean_question
        return rewritten

    def close(self) -> None:
        if self._vector_store is not None:
            logger.info("Closing vector store")
            self._vector_store.close()
            self._vector_store = None

    def _resolve_conversation_context(
        self,
        history: list[dict[str, str]],
        *,
        conversation_summary: str | None,
        model: str,
        budget_config: PromptBudgetConfig,
        api_key: str | None,
        base_url: str | None,
    ) -> tuple[list[dict[str, str]], str | None, str | None]:
        clean_summary = (conversation_summary or "").strip()
        history_tokens = conversation_history_tokens(history, model)
        if clean_summary and history_tokens < budget_config.conversation_summary_trigger_tokens:
            return summarized_history(clean_summary, history), clean_summary, None
        if not clean_summary and history_tokens < budget_config.conversation_summary_trigger_tokens:
            return history, None, None
        try:
            summary = self._summarize_conversation(history, model=model, api_key=api_key, base_url=base_url)
        except Exception as exc:
            if clean_summary:
                return (
                    summarized_history(clean_summary, history),
                    clean_summary,
                    f"Conversation compression failed; the previous compressed summary was used instead: {exc}",
                )
            return history, None, f"Conversation compression failed; raw recent history was used instead: {exc}"
        return summarized_history(summary, history), summary, None

    def _summarize_conversation(
        self,
        history: list[dict[str, str]],
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
    ) -> str:
        turns = []
        for turn in history:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                label = "Uživatel" if role == "user" else "Avatar"
                turns.append(f"{label}: {content}")
        messages = [
            {
                "role": "system",
                "content": (
                    "Compress the conversation for a RAG assistant. Preserve user preferences, unresolved "
                    "references, named entities, constraints, and commitments from previous answers. Do not "
                    "invent facts. Write a concise Czech summary unless the conversation is clearly in another language."
                ),
            },
            {
                "role": "user",
                "content": "\n\n".join(turns),
            },
        ]
        generation = self.llm.generate(messages, model=model, api_key=api_key, base_url=base_url)
        return generation.answer.strip()


def _retrieved_chunk_from_record(record: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        citation_id=record.get("citation_id", ""),
        chunk_id=record.get("chunk_id", ""),
        text=record.get("text", ""),
        metadata=record.get("metadata", {}),
        score=float(record.get("score") or 0.0),
        dense_score=float(record["dense_score"]) if record.get("dense_score") is not None else None,
        bm25_score=float(record["bm25_score"]) if record.get("bm25_score") is not None else None,
        rerank_score=float(record["rerank_score"]) if record.get("rerank_score") is not None else None,
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
