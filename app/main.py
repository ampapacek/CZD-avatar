from __future__ import annotations

import json
import logging
import hmac
import random
import time
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse

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
    Placeholder,
    PlaceholderSaveRequest,
    PromptPreset,
    PromptPresetSaveRequest,
    RetrieveRequest,
    RetrieveResponse,
    UnlockRequest,
    UnlockResponse,
)
from app.rag.pipeline import RAGPipeline
from app.rag.reranker import reranker_model_available
from app.rag.prompt_presets import delete_prompt_preset, load_prompt_presets, save_prompt_preset
from app.rag.placeholders import (
    delete_placeholder,
    load_placeholders,
    placeholder_defs_from_records,
    save_placeholder,
)
from app.rag.llm_providers import (
    available_llm_providers,
    provider_default_model,
    provider_api_key,
    provider_preset,
    provider_public_models,
    resolve_llm_provider,
)
from app.rag.llm import validate_api_key
from app.rag.prompts import (
    default_system_prompt_template,
    default_user_prompt_template,
    resolve_placeholder_defs,
    template_placeholder_names,
)
from app.rag.token_budget import PromptBudgetConfig, PromptBudgetError
from app.rag.wp_config import default_wp_id, wp_public_payload


log_path = configure_logging("api")
logger = logging.getLogger(__name__)
logger.info("Starting API; log file: %s", log_path)

def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


settings = get_settings()
provider_presets = available_llm_providers()
default_provider = ""
default_provider_preset: dict[str, object] = {}
all_llm_models: list[str] = []
default_model = ""


def _refresh_provider_state(force_model_refresh: bool = False) -> None:
    global provider_presets, default_provider, default_provider_preset, all_llm_models, default_model
    provider_presets = available_llm_providers(force_model_refresh=force_model_refresh)
    default_provider = resolve_llm_provider(settings.llm_provider, provider_presets)
    default_provider_preset = provider_preset(default_provider, provider_presets)
    provider_model_presets = _dedupe_preserve_order(
        [model for provider in provider_presets for model in provider["model_presets"]]
    )
    default_model = provider_default_model(default_provider, provider_presets)
    all_llm_models = _dedupe_preserve_order(provider_model_presets)


def _llm_settings_payload() -> dict[str, object]:
    selected_provider = default_provider_preset
    return {
        "llm_provider": default_provider,
        "llm_base_url": selected_provider["base_url"],
        "llm_model": selected_provider["default_model"],
        "llm_providers": provider_presets,
        "model_presets": selected_provider["model_presets"],
        "all_model_presets": all_llm_models,
        "llm_policy": {
            "provider": default_provider,
            "providers": provider_presets,
            "public_models": selected_provider["public_models"],
            "model_presets": selected_provider["model_presets"],
            "all_models": all_llm_models,
            "custom_model_requires_browser_key": True,
            "unlock_password_enabled": bool(settings.admin_password),
            "models_cache_ttl_seconds": settings.llm_models_cache_ttl_seconds,
        },
    }


_refresh_provider_state()
logger.info(
    "Loaded settings: provider=%s model=%s providers=%s admin_password=%s",
    default_provider,
    default_model,
    [provider["id"] for provider in provider_presets],
    "set" if settings.admin_password else "missing",
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

AI_UFAL_HOST = "ai.ufal.mff.cuni.cz"
WP2_MSEARCH_COLLECTION = "35a4a85e-4d6e-42a3-a3ff-e1f151ffbd09"


def _is_ai_ufal_base_url(base_url: str | None) -> bool:
    parsed = urlparse((base_url or "").strip())
    return parsed.scheme == "https" and parsed.hostname == AI_UFAL_HOST


def _enforce_msearch_collection_policy(msearch_collection: str | None, llm_base_url: str | None) -> None:
    if (msearch_collection or "").strip() == WP2_MSEARCH_COLLECTION and not _is_ai_ufal_base_url(llm_base_url):
        raise HTTPException(
            status_code=400,
            detail="WP2 mSearch collection is available only with the AI Ufal provider.",
        )


def _resolve_llm_request(request: ChatRequest) -> tuple[str, str, str | None, str | None]:
    resolved_provider = resolve_llm_provider(request.llm_provider, provider_presets, request.llm_base_url)
    provider_config = provider_preset(resolved_provider, provider_presets, request.llm_base_url)
    resolved_model = request.model or provider_config["default_model"] or (
        provider_config["model_presets"][0] if provider_config["model_presets"] else ""
    )
    browser_api_key = request.llm_api_key.strip() if request.llm_api_key else None
    requested_base_url = request.llm_base_url.strip().rstrip("/") if request.llm_base_url else ""
    provider_base_url = str(provider_config.get("base_url") or "").strip().rstrip("/")
    use_server_api_key = not requested_base_url or requested_base_url == provider_base_url
    server_api_key = provider_api_key(resolved_provider, provider_presets, request.llm_base_url) if use_server_api_key else ""
    browser_admin_password = request.admin_password.strip() if request.admin_password else ""
    unlock_enabled = bool(settings.admin_password) and hmac.compare_digest(
        browser_admin_password,
        settings.admin_password,
    )
    resolved_api_key = browser_api_key or server_api_key or None
    public_models = provider_public_models(resolved_provider, provider_presets, request.llm_base_url)
    if not resolved_api_key and resolved_model not in public_models and not unlock_enabled:
        allowed_models = ", ".join(sorted(public_models)) if public_models else provider_config["default_model"]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Model '{resolved_model}' requires your own API key. "
                f"Use Settings in the browser to enter one, unlock all models with the shared password, or choose one of the public models: {allowed_models}."
            ),
        )
    resolved_base_url = request.llm_base_url or provider_config["base_url"]
    if browser_api_key:
        try:
            validate_api_key(browser_api_key, resolved_base_url)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return resolved_provider, resolved_model, resolved_api_key, resolved_base_url


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
    _refresh_provider_state()
    return {
        "placeholders": load_placeholders(settings.placeholders_path),
        "top_k": settings.top_k,
        "embedding_model": settings.embedding_model,
        **_llm_settings_payload(),
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
            "rerank_enabled": settings.reranker_enabled,
            "rerank_weight": settings.reranker_weight,
            "rerank_model": settings.reranker_model,
            "rerank_candidates": settings.reranker_candidates,
            "rerank_available": reranker_model_available(settings.reranker_model),
        },
        "token_budget_defaults": {
            "context_window_tokens": settings.context_window_tokens,
            "output_token_budget_short": settings.output_token_budget_short,
            "output_token_budget_medium": settings.output_token_budget_medium,
            "output_token_budget_long": settings.output_token_budget_long,
            "min_prompt_chunks": settings.min_prompt_chunks,
            "token_budget_safety_margin": settings.token_budget_safety_margin,
            "conversation_summary_trigger_tokens": settings.conversation_summary_trigger_tokens,
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
        },
        "wps": wp_public_payload(),
        "default_wp": default_wp_id(),
    }


@app.post("/llm-providers/refresh")
def refresh_llm_providers() -> dict[str, object]:
    _refresh_provider_state(force_model_refresh=True)
    return _llm_settings_payload()


@app.get("/questions/random")
def random_question() -> dict[str, str]:
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Collection questions file was not found.")
    questions = [line.strip() for line in questions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not questions:
        raise HTTPException(status_code=404, detail="Collection questions file does not contain any questions.")
    return {"question": random.choice(questions)}


PROMPT_PRESET_FORBIDDEN_DETAIL = (
    "Tento sdílený prompt patří jinému prohlížeči. Odemkni ho sdíleným heslem, abys ho mohl změnit."
)


def _find_prompt_preset(preset_id: str) -> dict[str, str] | None:
    return next(
        (preset for preset in load_prompt_presets(settings.prompt_presets_path) if preset["id"] == preset_id),
        None,
    )


def _can_modify_prompt_preset(preset: dict[str, str], owner_id: str | None, password: str | None) -> bool:
    owner = (preset.get("owner_id") or "").strip()
    requester = (owner_id or "").strip()
    if owner and requester and hmac.compare_digest(owner, requester):
        return True
    if settings.admin_password and hmac.compare_digest(
        (password or "").strip(), settings.admin_password
    ):
        return True
    return False


@app.get("/prompt-presets", response_model=list[PromptPreset])
def get_prompt_presets() -> list[PromptPreset]:
    return [PromptPreset(**preset) for preset in load_prompt_presets(settings.prompt_presets_path)]


@app.post("/unlock", response_model=UnlockResponse)
def unlock_models(request: UnlockRequest) -> UnlockResponse:
    if not settings.admin_password:
        return UnlockResponse(unlocked=False)
    unlocked = hmac.compare_digest(request.password.strip(), settings.admin_password)
    return UnlockResponse(unlocked=unlocked)


@app.post("/prompt-presets", response_model=PromptPreset)
def post_prompt_preset(request: PromptPresetSaveRequest) -> PromptPreset:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Prompt preset name is required.")
    existing = _find_prompt_preset(request.id) if request.id else None
    if existing is not None and not _can_modify_prompt_preset(existing, request.owner_id, request.admin_password):
        raise HTTPException(status_code=403, detail=PROMPT_PRESET_FORBIDDEN_DETAIL)
    preset = save_prompt_preset(
        settings.prompt_presets_path,
        name=name,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        wp_id=request.wp_id,
        length_prompts=request.length_prompts,
        preset_id=request.id,
        owner_id=request.owner_id,
    )
    return PromptPreset(**preset)


@app.delete("/prompt-presets/{preset_id}", status_code=204)
def remove_prompt_preset(
    preset_id: str,
    owner_id: str | None = None,
    admin_password: str | None = None,
) -> Response:
    existing = _find_prompt_preset(preset_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Prompt preset not found.")
    if not _can_modify_prompt_preset(existing, owner_id, admin_password):
        raise HTTPException(status_code=403, detail=PROMPT_PRESET_FORBIDDEN_DETAIL)
    delete_prompt_preset(settings.prompt_presets_path, preset_id)
    return Response(status_code=204)


PLACEHOLDER_FORBIDDEN_DETAIL = (
    "Tato sdílená proměnná patří jinému prohlížeči. Odemkni ji sdíleným heslem, abys ji mohl změnit."
)


def _find_placeholder(name: str) -> dict[str, object] | None:
    return next(
        (item for item in load_placeholders(settings.placeholders_path) if item["name"] == name),
        None,
    )


def _can_modify_placeholder(placeholder: dict[str, object], owner_id: str | None, password: str | None) -> bool:
    owner = (str(placeholder.get("owner_id") or "")).strip()
    requester = (owner_id or "").strip()
    if owner and requester and hmac.compare_digest(owner, requester):
        return True
    if settings.admin_password and hmac.compare_digest((password or "").strip(), settings.admin_password):
        return True
    return False


@app.get("/placeholders", response_model=list[Placeholder])
def get_placeholders() -> list[Placeholder]:
    return [Placeholder(**item) for item in load_placeholders(settings.placeholders_path)]


@app.post("/placeholders", response_model=Placeholder)
def post_placeholder(request: PlaceholderSaveRequest) -> Placeholder:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Placeholder name is required.")
    existing = _find_placeholder(name)
    if existing is not None and not _can_modify_placeholder(existing, request.owner_id, request.admin_password):
        raise HTTPException(status_code=403, detail=PLACEHOLDER_FORBIDDEN_DETAIL)
    record = save_placeholder(
        settings.placeholders_path,
        name=name,
        label=request.label,
        kind=request.kind,
        help=request.help,
        default=request.default,
        options=[option.model_dump() for option in request.options],
        owner_id=request.owner_id,
    )
    return Placeholder(**record)


@app.delete("/placeholders/{name}", status_code=204)
def remove_placeholder(
    name: str,
    owner_id: str | None = None,
    admin_password: str | None = None,
) -> Response:
    existing = _find_placeholder(name)
    if existing is None:
        raise HTTPException(status_code=404, detail="Placeholder not found.")
    if not _can_modify_placeholder(existing, owner_id, admin_password):
        raise HTTPException(status_code=403, detail=PLACEHOLDER_FORBIDDEN_DETAIL)
    delete_placeholder(settings.placeholders_path, name)
    return Response(status_code=204)


def _resolve_chat_placeholders(request: ChatRequest) -> tuple[dict, dict[str, str]]:
    """Resolve placeholder defs and selections for a chat request.

    14a only wires the shared server global registry. Inline (preset) defs land
    in 14b and browser-local global defs are carried via the request later.
    Selections come from the dedicated request fields the frontend already sends.
    """

    system_template = (request.system_prompt or "").strip() or default_system_prompt_template()
    user_template = (request.user_prompt_template or "").strip() or default_user_prompt_template()
    names = template_placeholder_names(system_template) | template_placeholder_names(user_template)
    shared_global = placeholder_defs_from_records(load_placeholders(settings.placeholders_path))
    defs = resolve_placeholder_defs(names, shared_global_defs=shared_global)
    selections: dict[str, str] = {}
    if request.length is not None:
        selections["length"] = request.length
    if request.custom_instructions is not None:
        selections["custom_instructions"] = request.custom_instructions
    return defs, selections


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
        _enforce_msearch_collection_policy(
            request.msearch_collection or settings.msearch_collection,
            default_provider_preset["base_url"],
        )
        chunks, baseline_chunks = pipeline.retrieve_with_baseline(
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
            rerank_enabled=request.rerank_enabled,
            rerank_weight=request.rerank_weight,
            rerank_candidates=request.rerank_candidates,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RetrieveResponse(
        question=request.question,
        retrieved_chunks=[_serialize_retrieved_chunk(chunk) for chunk in chunks],
        baseline_chunks=[_serialize_retrieved_chunk(chunk) for chunk in baseline_chunks],
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    length = request.length or "medium"
    placeholder_defs, selections = _resolve_chat_placeholders(request)
    try:
        resolved_provider, resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
        _enforce_msearch_collection_policy(request.msearch_collection or settings.msearch_collection, resolved_base_url)
        return pipeline.chat(
            question=request.question,
            length=length,
            placeholder_defs=placeholder_defs,
            selections=selections,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            conversation_history=request.conversation_history,
            conversation_summary=request.conversation_summary,
            top_k=request.top_k,
            model=resolved_model,
            llm_api_key=resolved_api_key,
            llm_base_url=resolved_base_url,
            llm_provider=resolved_provider,
            context_window_tokens=request.context_window_tokens,
            output_token_budget_short=request.output_token_budget_short,
            output_token_budget_medium=request.output_token_budget_medium,
            output_token_budget_long=request.output_token_budget_long,
            min_prompt_chunks=request.min_prompt_chunks,
            token_budget_safety_margin=request.token_budget_safety_margin,
            conversation_summary_trigger_tokens=request.conversation_summary_trigger_tokens,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight,
            min_score=request.min_score,
            min_relative_score=request.min_relative_score,
            retrieval_backend=request.retrieval_backend,
            msearch_collection=request.msearch_collection,
            msearch_mode=request.msearch_mode,
            msearch_min_confidence=request.msearch_min_confidence,
            rerank_enabled=request.rerank_enabled,
            rerank_weight=request.rerank_weight,
            rerank_candidates=request.rerank_candidates,
        )
    except PromptBudgetError as exc:
        raise HTTPException(status_code=400, detail=exc.to_payload()) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    length = request.length or "medium"
    placeholder_defs, selections = _resolve_chat_placeholders(request)

    def event_stream():
        started = time.perf_counter()
        try:
            resolved_provider, resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
            _enforce_msearch_collection_policy(request.msearch_collection or settings.msearch_collection, resolved_base_url)
            candidates = pipeline.retrieve_candidates(
                request.question,
                request.top_k,
                dense_weight=request.dense_weight,
                bm25_weight=request.bm25_weight,
                min_score=request.min_score,
                min_relative_score=request.min_relative_score,
                retrieval_backend=request.retrieval_backend,
                llm_provider=resolved_provider,
                msearch_collection=request.msearch_collection,
                msearch_mode=request.msearch_mode,
                msearch_min_confidence=request.msearch_min_confidence,
                rerank_enabled=request.rerank_enabled,
                rerank_weight=request.rerank_weight,
                rerank_candidates=request.rerank_candidates,
            )
            baseline_payload = [_serialize_retrieved_chunk(chunk) for chunk in candidates.baseline]
            # When reranking is active, show the first-stage hits immediately so the
            # user is not staring at an empty panel while the cross-encoder runs;
            # the final "sources" event below replaces them with the reranked order.
            if candidates.rerank_active and candidates.baseline:
                yield _sse_event(
                    "preliminary_sources",
                    {
                        "question": request.question,
                        "retrieved_chunks": baseline_payload,
                        "sources": [_serialize_source(chunk) for chunk in candidates.baseline],
                    },
                )
            retrieved: list = []
            rerank_seconds = 0.0
            for event in pipeline.apply_rerank_iter(request.question, candidates):
                kind = event[0]
                if kind == "eta":
                    # Up-front estimate from past runs; None on the first ever run.
                    yield _sse_event("rerank_progress", {"done": 0, "total": 0, "eta_seconds": event[1]})
                elif kind == "progress":
                    _, done, total, elapsed = event
                    # Refine the ETA per batch from observed per-pair cost.
                    eta = round(elapsed / done * (total - done), 2) if done else None
                    yield _sse_event(
                        "rerank_progress",
                        {"done": done, "total": total, "elapsed": round(elapsed, 3), "eta_seconds": eta},
                    )
                else:  # "result"
                    retrieved, rerank_seconds = event[1], event[2]
            budget_config = PromptBudgetConfig.from_settings(
                settings,
                context_window_tokens=request.context_window_tokens,
                output_token_budget_short=request.output_token_budget_short,
                output_token_budget_medium=request.output_token_budget_medium,
                output_token_budget_long=request.output_token_budget_long,
                min_prompt_chunks=request.min_prompt_chunks,
                token_budget_safety_margin=request.token_budget_safety_margin,
                conversation_summary_trigger_tokens=request.conversation_summary_trigger_tokens,
            )
            budget, conversation_summary = pipeline.build_chat_prompt(
                question=request.question,
                retrieved=retrieved,
                length=length,
                model=resolved_model,
                placeholder_defs=placeholder_defs,
                selections=selections,
                system_prompt=request.system_prompt,
                user_prompt_template=request.user_prompt_template,
                conversation_history=request.conversation_history,
                conversation_summary=request.conversation_summary,
                llm_api_key=resolved_api_key,
                llm_base_url=resolved_base_url,
                budget_config=budget_config,
            )
            yield _sse_event(
                "sources",
                {
                    "question": request.question,
                    "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                    "used_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                    "omitted_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.omitted_chunks],
                    "baseline_chunks": baseline_payload,
                    "sources": [_serialize_source(chunk) for chunk in budget.used_chunks],
                    "token_budget": budget.metadata(),
                    "chunk_budget_warnings": budget.warnings,
                    "conversation_summary": conversation_summary,
                },
            )
            answer_parts: list[str] = []
            generation_started = time.perf_counter()
            stream = pipeline.llm.stream_generate(
                budget.messages,
                model=resolved_model,
                api_key=resolved_api_key,
                base_url=resolved_base_url,
            )
            for token in stream:
                answer_parts.append(token)
                yield _sse_event("token", {"text": token})

            generation_seconds = time.perf_counter() - generation_started
            answer = "".join(answer_parts).strip()
            elapsed = time.perf_counter() - started
            upstream_model = stream.upstream_model or resolved_model
            response = {
                "answer": answer,
                "sources": [_serialize_source(chunk) for chunk in budget.used_chunks],
                "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                "used_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                "omitted_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.omitted_chunks],
                "baseline_chunks": baseline_payload,
                "token_budget": budget.metadata(),
                "chunk_budget_warnings": budget.warnings,
                "conversation_summary": conversation_summary,
                "model": resolved_model,
                "upstream_model": upstream_model,
                "response_time_seconds": round(elapsed, 3),
                "rerank_time_seconds": round(rerank_seconds, 3) if candidates.rerank_active else None,
                "generation_time_seconds": round(generation_seconds, 3),
            }
            logger.info(
                "Streamed answer question=%r length=%s model=%s response_time=%.2fs rerank=%.2fs generation=%.2fs answer=%s",
                request.question,
                length,
                resolved_model,
                elapsed,
                rerank_seconds,
                generation_seconds,
                answer[:280] + ("…" if len(answer) > 280 else ""),
            )
            yield _sse_event("done", response)
        except PromptBudgetError as exc:
            logger.info("Streaming chat rejected by token budget for question=%r: %s", request.question, exc)
            yield _sse_event("error", {"detail": exc.to_payload()})
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
        "rerank_score": float(chunk["rerank_score"]) if chunk.get("rerank_score") is not None else None,
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
