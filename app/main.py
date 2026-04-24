from __future__ import annotations

import json
import logging
import hashlib
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.logging_config import configure_logging
from app.models import ChatRequest, ChatResponse, HealthResponse, IngestRequest, IngestResponse, RetrieveRequest, RetrieveResponse
from app.rag.pipeline import RAGPipeline
from app.rag.prompts import available_lengths, available_styles, build_messages


MODEL_PRESETS = [
    "openai/gpt-5.2",
    "openai/gpt-5.4-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "openai/gpt-4o-mini",
    "openai/gpt-4.1-mini",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.0-flash-001",
    "google/gemini-3.0-pro",
    "mistralai/mistral-small-3.1-24b-instruct",
]

log_path = configure_logging("api")
logger = logging.getLogger(__name__)
logger.info("Starting API; log file: %s", log_path)

settings = get_settings()
key_fingerprint = (
    hashlib.sha256(settings.openrouter_api_key.encode()).hexdigest()[:12] if settings.openrouter_api_key else "missing"
)
logger.info("Loaded settings: model=%s openrouter_key_sha256=%s", settings.openrouter_model, key_fingerprint)
pipeline = RAGPipeline(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.info("Shutting down API")
    pipeline.close()


app = FastAPI(title="rag-avatar", version="0.1.0", lifespan=lifespan)

static_dir = Path(__file__).parent / "static"
ufal_logo_path = Path(__file__).resolve().parents[1] / "logo_ufal_110u.png"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/logo_ufal_110u.png", include_in_schema=False)
def ufal_logo() -> FileResponse:
    return FileResponse(ufal_logo_path)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", collection=settings.qdrant_collection)


@app.get("/settings")
def get_public_settings() -> dict[str, object]:
    return {
        "styles": available_styles(),
        "lengths": available_lengths(),
        "default_style": settings.default_style,
        "default_length": settings.default_length,
        "top_k": settings.top_k,
        "embedding_model": settings.embedding_model,
        "llm_model": settings.openrouter_model,
        "model_presets": MODEL_PRESETS,
        "collection": settings.qdrant_collection,
        "retrieval_defaults": {
            "dense_weight": 0.7,
            "bm25_weight": 0.3,
            "min_score": settings.min_score,
            "min_relative_score": settings.min_relative_score,
            "top_k_min": 0,
            "top_k_max": 50,
        },
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    path = Path(request.path) if request.path else settings.raw_data_dir
    try:
        result = pipeline.ingest(path, reset=request.reset)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return IngestResponse(**result)


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    try:
        chunks = pipeline.retrieve(
            request.question,
            request.top_k,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight,
            min_score=request.min_score,
            min_relative_score=request.min_relative_score,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RetrieveResponse(
        question=request.question,
        retrieved_chunks=[_serialize_retrieved_chunk(chunk) for chunk in chunks],
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    style = request.style or settings.default_style
    length = request.length or settings.default_length
    if style not in available_styles():
        raise HTTPException(status_code=400, detail=f"Unknown style: {style}")
    if length not in available_lengths():
        raise HTTPException(status_code=400, detail=f"Unknown length: {length}")
    try:
        return pipeline.chat(
            question=request.question,
            style=style,
            length=length,
            custom_instructions=request.custom_instructions,
            conversation_history=request.conversation_history,
            top_k=request.top_k,
            model=request.model,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight,
            min_score=request.min_score,
            min_relative_score=request.min_relative_score,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    style = request.style or settings.default_style
    length = request.length or settings.default_length
    if style not in available_styles():
        raise HTTPException(status_code=400, detail=f"Unknown style: {style}")
    if length not in available_lengths():
        raise HTTPException(status_code=400, detail=f"Unknown length: {length}")

    def event_stream():
        started = time.perf_counter()
        resolved_model = request.model or settings.openrouter_model
        try:
            retrieved = pipeline.retrieve(
                request.question,
                request.top_k,
                dense_weight=request.dense_weight,
                bm25_weight=request.bm25_weight,
                min_score=request.min_score,
                min_relative_score=request.min_relative_score,
            )
            yield _sse_event(
                "sources",
                {
                    "question": request.question,
                    "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in retrieved],
                    "sources": [_serialize_source(chunk) for chunk in retrieved],
                },
            )

            messages = build_messages(
                request.question,
                retrieved,
                style,
                length,
                request.custom_instructions,
                conversation_history=request.conversation_history,
            )
            answer_parts: list[str] = []
            for token in pipeline.llm.stream_generate(messages, model=resolved_model):
                answer_parts.append(token)
                yield _sse_event("token", {"text": token})

            answer = "".join(answer_parts).strip()
            elapsed = time.perf_counter() - started
            response = {
                "answer": answer,
                "sources": [_serialize_source(chunk) for chunk in retrieved],
                "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in retrieved],
                "model": resolved_model,
                "response_time_seconds": round(elapsed, 3),
            }
            logger.info(
                "Streamed answer question=%r style=%s length=%s model=%s response_time=%.2fs answer=%s",
                request.question,
                style,
                length,
                resolved_model,
                elapsed,
                answer[:280] + ("…" if len(answer) > 280 else ""),
            )
            yield _sse_event("done", response)
        except Exception as exc:
            logger.exception("Streaming chat failed for question=%r", request.question)
            yield _sse_event("error", {"detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event: str, payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    lines = [f"event: {event}"]
    lines.extend(f"data: {line}" for line in data.splitlines() or [""])
    return "\n".join(lines) + "\n\n"


def _serialize_retrieved_chunk(chunk: dict[str, object]) -> dict[str, object]:
    return {
        "citation_id": chunk.get("citation_id", ""),
        "chunk_id": chunk.get("chunk_id", ""),
        "text": chunk.get("text", ""),
        "metadata": chunk.get("metadata", {}),
        "score": float(chunk.get("score") or 0.0),
        "dense_score": float(chunk["dense_score"]) if chunk.get("dense_score") is not None else None,
        "bm25_score": float(chunk["bm25_score"]) if chunk.get("bm25_score") is not None else None,
    }


def _serialize_source(chunk: dict[str, object]) -> dict[str, object]:
    metadata = chunk.get("metadata", {})
    return {
        "citation_id": chunk.get("citation_id", ""),
        "chunk_id": chunk.get("chunk_id", ""),
        "title": metadata.get("title"),
        "source_path": metadata.get("source_path"),
        "source_path_display": metadata.get("source_path_display"),
        "page_number": metadata.get("page_number"),
        "url": metadata.get("url"),
        "document_url": metadata.get("document_url"),
        "source_url": metadata.get("source_url"),
        "source_name": metadata.get("source_name"),
        "score": float(chunk.get("score") or 0.0),
    }
