from __future__ import annotations

import json
import logging
import hashlib
import hmac
import random
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.logging_config import configure_logging
from app.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    PromptPreset,
    PromptPresetSaveRequest,
    RetrieveRequest,
    RetrieveResponse,
    UnlockRequest,
    UnlockResponse,
)
from app.rag.pipeline import RAGPipeline
from app.rag.prompt_presets import delete_prompt_preset, load_prompt_presets, save_prompt_preset
from app.rag.prompts import (
    LENGTH_PROMPTS,
    STYLE_PROMPTS,
    available_lengths,
    available_styles,
    build_messages,
    default_system_prompt_template,
    default_user_prompt_template,
)


log_path = configure_logging("api")
logger = logging.getLogger(__name__)
logger.info("Starting API; log file: %s", log_path)

settings = get_settings()
public_llm_models = settings.public_llm_models()
ALL_MODEL_PRESETS = [
    "openrouter/free",
    "meta-llama/llama-4-scout",
    "meta-llama/llama-4-maverick",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "openai/gpt-5.2",
    "openai/gpt-5.4-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.0-flash-001",
    "google/gemini-3.0-pro",
    "mistralai/mistral-small-3.1-24b-instruct",
]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


all_llm_models = _dedupe_preserve_order([*public_llm_models, *ALL_MODEL_PRESETS, settings.llm_model])
key_fingerprint = (
    hashlib.sha256(settings.llm_api_key.encode()).hexdigest()[:12] if settings.llm_api_key else "missing"
)
logger.info(
    "Loaded settings: model=%s llm_key_sha256=%s public_models=%s unlock_password=%s",
    settings.llm_model,
    key_fingerprint,
    public_llm_models,
    "set" if settings.llm_unlock_password else "missing",
)
pipeline = RAGPipeline(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.info("Shutting down API")
    pipeline.close()


app = FastAPI(title="rag-avatar", version="0.1.0", lifespan=lifespan)

static_dir = Path(__file__).parent / "static"
collection_dir = Path(__file__).resolve().parents[1] / "data" / "collections" / "czech_history"
ufal_logo_path = static_dir / "logo_ufal_110u.png"
questions_path = collection_dir / "questions" / "questions.txt"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _resolve_llm_request(request: ChatRequest) -> tuple[str, str | None, str | None]:
    resolved_model = request.model or settings.llm_model
    browser_api_key = request.llm_api_key.strip() if request.llm_api_key else None
    browser_unlock_password = request.llm_unlock_password.strip() if request.llm_unlock_password else ""
    unlock_enabled = bool(settings.llm_unlock_password) and hmac.compare_digest(
        browser_unlock_password,
        settings.llm_unlock_password,
    )
    public_models = set(public_llm_models)
    if resolved_model not in public_models and not unlock_enabled and not browser_api_key:
        allowed_models = ", ".join(public_llm_models) if public_llm_models else settings.llm_model
        raise HTTPException(
            status_code=400,
            detail=(
                f"Model '{resolved_model}' requires your own API key. "
                f"Use the LLM API panel in the browser to enter one, unlock all models with the shared password, or choose one of the public models: {allowed_models}."
            ),
        )
    resolved_api_key = browser_api_key or settings.llm_api_key or None
    if not resolved_api_key:
        raise HTTPException(
            status_code=400,
            detail="No API key is available. Set LLM_API_KEY on the server or enter your own key in the browser.",
        )
    resolved_base_url = request.llm_base_url or settings.llm_base_url
    return resolved_model, resolved_api_key, resolved_base_url


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
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "model_presets": public_llm_models,
        "all_model_presets": all_llm_models,
        "llm_policy": {
            "public_models": public_llm_models,
            "all_models": all_llm_models,
            "custom_model_requires_browser_key": True,
            "unlock_password_enabled": bool(settings.llm_unlock_password),
        },
        "collection": settings.qdrant_collection,
        "retrieval_backend": settings.retrieval_backend,
        "retrieval_backends": ["msearch", "local"],
        "retrieval_defaults": {
            "dense_weight": 0.7,
            "bm25_weight": 0.3,
            "min_score": settings.min_score,
            "min_relative_score": settings.min_relative_score,
            "msearch_min_confidence": settings.msearch_min_confidence,
            "top_k_min": 0,
            "top_k_max": 50,
        },
        "msearch_defaults": {
            "collection": settings.msearch_collection,
            "collection_presets": pipeline.msearch_retriever.collection_presets(),
            "mode": settings.msearch_mode,
            "modes": ["hybrid", "semantic", "keyword"],
            "max_results": settings.msearch_max_results,
            "min_confidence": settings.msearch_min_confidence,
        },
        "prompt_defaults": {
            "system_prompt": default_system_prompt_template(),
            "user_prompt_template": default_user_prompt_template(),
            "style_prompts": STYLE_PROMPTS,
            "length_prompts": LENGTH_PROMPTS,
        },
    }


@app.get("/questions/random")
def random_question() -> dict[str, str]:
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Collection questions file was not found.")
    questions = [line.strip() for line in questions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not questions:
        raise HTTPException(status_code=404, detail="Collection questions file does not contain any questions.")
    return {"question": random.choice(questions)}


@app.get("/prompt-presets", response_model=list[PromptPreset])
def get_prompt_presets() -> list[PromptPreset]:
    return [PromptPreset(**preset) for preset in load_prompt_presets(settings.prompt_presets_path)]


@app.post("/unlock", response_model=UnlockResponse)
def unlock_models(request: UnlockRequest) -> UnlockResponse:
    if not settings.llm_unlock_password:
        return UnlockResponse(unlocked=False)
    unlocked = hmac.compare_digest(request.password.strip(), settings.llm_unlock_password)
    return UnlockResponse(unlocked=unlocked)


@app.post("/prompt-presets", response_model=PromptPreset)
def post_prompt_preset(request: PromptPresetSaveRequest) -> PromptPreset:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Prompt preset name is required.")
    preset = save_prompt_preset(
        settings.prompt_presets_path,
        name=name,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        style_prompts=request.style_prompts,
        length_prompts=request.length_prompts,
        preset_id=request.id,
    )
    return PromptPreset(**preset)


@app.delete("/prompt-presets/{preset_id}", status_code=204)
def remove_prompt_preset(preset_id: str) -> Response:
    if not delete_prompt_preset(settings.prompt_presets_path, preset_id):
        raise HTTPException(status_code=404, detail="Prompt preset not found.")
    return Response(status_code=204)


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
            retrieval_backend=request.retrieval_backend,
            msearch_collection=request.msearch_collection,
            msearch_mode=request.msearch_mode,
            msearch_min_confidence=request.msearch_min_confidence,
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
        resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
        return pipeline.chat(
            question=request.question,
            style=style,
            length=length,
            custom_instructions=request.custom_instructions,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            style_prompts=request.style_prompts,
            length_prompts=request.length_prompts,
            conversation_history=request.conversation_history,
            top_k=request.top_k,
            model=resolved_model,
            llm_api_key=resolved_api_key,
            llm_base_url=resolved_base_url,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight,
            min_score=request.min_score,
            min_relative_score=request.min_relative_score,
            retrieval_backend=request.retrieval_backend,
            msearch_collection=request.msearch_collection,
            msearch_mode=request.msearch_mode,
            msearch_min_confidence=request.msearch_min_confidence,
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
        try:
            resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
            retrieved = pipeline.retrieve(
                request.question,
                request.top_k,
                dense_weight=request.dense_weight,
                bm25_weight=request.bm25_weight,
                min_score=request.min_score,
                min_relative_score=request.min_relative_score,
                retrieval_backend=request.retrieval_backend,
                msearch_collection=request.msearch_collection,
                msearch_mode=request.msearch_mode,
                msearch_min_confidence=request.msearch_min_confidence,
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
                system_prompt=request.system_prompt,
                user_prompt_template=request.user_prompt_template,
                style_prompts=request.style_prompts,
                length_prompts=request.length_prompts,
                conversation_history=request.conversation_history,
            )
            answer_parts: list[str] = []
            stream = pipeline.llm.stream_generate(
                messages,
                model=resolved_model,
                api_key=resolved_api_key,
                base_url=resolved_base_url,
            )
            for token in stream:
                answer_parts.append(token)
                yield _sse_event("token", {"text": token})

            answer = "".join(answer_parts).strip()
            elapsed = time.perf_counter() - started
            upstream_model = stream.upstream_model or resolved_model
            response = {
                "answer": answer,
                "sources": [_serialize_source(chunk) for chunk in retrieved],
                "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in retrieved],
                "model": resolved_model,
                "upstream_model": upstream_model,
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
        "source_kind": metadata.get("source_kind"),
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
