from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import hmac
import math
import random
import re
import threading
import time
import httpx
from html import escape
from pathlib import Path
from contextlib import asynccontextmanager, suppress
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.answer_cache import (
    CACHE_VERSION as ANSWER_CACHE_VERSION,
    AnswerCache,
    cache_key as answer_cache_key,
    is_cacheable as answer_is_cacheable,
    key_input as answer_cache_key_input,
    replay_pieces,
)
from app.auth import (
    AuthMiddleware,
    account_payload,
    count_request,
    current_user,
    get_store as get_account_store,
    is_admin_user,
    router as auth_router,
)
from app.admin_password_guard import AdminPasswordGuard
from app.config import get_settings
from app.analytics import (
    AnalyticsWriter,
    bind_context,
    configure as configure_analytics,
    endpoint_host,
    error_code as analytics_error_code,
    estimated_tokens,
    ms,
    question_metadata,
    request_context,
    text_lengths,
)
from app.logging_config import configure_logging
from app.models import (
    AnswerCacheFilter,
    AnswerCachePinRequest,
    BuiltinPromptOverride,
    BuiltinPromptOverrideSaveRequest,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Placeholder,
    PlaceholderSaveRequest,
    PromptPreset,
    PromptPresetSaveRequest,
    QueryTransformRequest,
    QueryTransformResponse,
    RetrieveRequest,
    RetrieveResponse,
    SharedHistoryItem,
    SharedHistorySaveRequest,
    SharedHistoryUpdateRequest,
    UnlockRequest,
    UnlockResponse,
)
from app.rag.answer_cleanup import strip_model_source_list
from app.rag.msearch import clear_collections_cache
from app.rag.model_metadata import (
    ReasoningSupport,
    load_model_metadata,
    resolve_reasoning_support,
)
from app.rag.pipeline import RAGPipeline
from app.rag.reranker import reranker_model_available
from app.rag.prompt_presets import (
    delete_builtin_prompt_override,
    delete_prompt_preset,
    load_builtin_prompt_overrides,
    load_prompt_presets,
    save_builtin_prompt_override,
    save_prompt_preset,
)
from app.rag.query_transforms import render_query_transform_prompt, valid_lindat_model
from app.rag.shared_history import (
    delete_shared_history_item,
    load_shared_history,
    save_shared_history_item,
    update_shared_history_item,
)
from app.rag.placeholders import (
    DEFAULT_PLACEHOLDERS,
    delete_placeholder,
    effective_global_placeholders,
    load_placeholders,
    placeholder_def_from_record,
    placeholder_defs_from_records,
    placeholder_name,
    save_placeholder,
)
from app.rag.llm_providers import (
    load_provider_configs,
    provider_default_model,
    provider_api_key,
    provider_preset,
    provider_public_models,
    resolve_llm_provider,
)
from app.rag.llm import REASONING, check_public_base_url, validate_api_key
from app.rag.prompts import (
    default_system_prompt_template,
    default_user_prompt_template,
    resolve_placeholder_defs,
    substitute_value,
    template_placeholder_names,
)
from app.rag.token_budget import PromptBudgetConfig, PromptBudgetError
from app.rag.wp_config import (
    WP_CONFIGS,
    default_wp_id,
    gated_msearch_collection_ids,
    get_wp_config,
    resolve_wp_id,
    wp_collection_prefix,
    wp_public_payload,
    wp_requires_aiufal,
)


logger = logging.getLogger(__name__)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


settings = get_settings()
admin_password_guard = AdminPasswordGuard()
analytics = AnalyticsWriter(
    False,
    settings.analytics_dir,
    settings.analytics_instance_id,
)
model_metadata = load_model_metadata(settings.model_metadata_path)
provider_presets: list[dict[str, object]] = []
default_provider = ""
default_provider_preset: dict[str, object] = {}
all_llm_models: list[str] = []
default_model = ""
# `data/models.json` plus whatever the providers' own catalogues added. Keyed by
# model name across every provider, the same way the declared map always was: in
# practice the names are provider-qualified (`openai/gpt-oss-120b` on OpenRouter
# against `gpt-oss-120b` on e-infra), so they do not collide.
model_reasoning: dict[str, ReasoningSupport] = {}
_provider_state_ready = False
# One refresh at a time. The startup prewarm below runs in a worker thread while
# requests are served from other threadpool threads, and a refresh rebuilds
# several module globals in place — two of them running at once could leave a
# request reading a half-replaced set.
_provider_state_lock = threading.Lock()


def _refresh_provider_state(force_model_refresh: bool = False) -> None:
    with _provider_state_lock:
        _refresh_provider_state_locked(force_model_refresh)


def _refresh_provider_state_locked(force_model_refresh: bool) -> None:
    global model_metadata, model_reasoning, _provider_state_ready
    global provider_presets, default_provider, default_provider_preset, all_llm_models, default_model
    model_metadata = load_model_metadata(settings.model_metadata_path)
    provider_configs = load_provider_configs(
        force_model_refresh=force_model_refresh,
        model_context_windows=model_metadata.context_windows,
        provider_context_window_defaults=model_metadata.provider_context_windows,
        provider_context_window_ceilings=model_metadata.provider_context_window_ceilings,
        model_reasoning=model_metadata.reasoning,
    )
    provider_presets = [provider.to_dict() for provider in provider_configs]
    model_reasoning = {
        model: support
        for provider in provider_configs
        for model, support in (provider.model_reasoning or {}).items()
    }
    default_provider = resolve_llm_provider(settings.llm_provider, provider_presets)
    default_provider_preset = provider_preset(default_provider, provider_presets)
    provider_model_presets = _dedupe_preserve_order(
        [model for provider in provider_presets for model in provider["model_presets"]]
    )
    default_model = provider_default_model(default_provider, provider_presets)
    all_llm_models = _dedupe_preserve_order(provider_model_presets)
    _provider_state_ready = True
    logger.info(
        "Loaded settings: provider=%s model=%s providers=%s admin_password=%s",
        default_provider,
        default_model,
        [provider["id"] for provider in provider_presets],
        "set" if settings.admin_password else "missing",
    )


def _ensure_provider_state() -> None:
    """Lazily trigger the first provider-state refresh on demand.

    Discovery is deliberately not run at *import* time: it involves slow
    network round-trips, and running it on import means uvicorn's --reload
    doubles the cost (its validation import in the parent process and the real
    import in the spawned worker both trigger it). The lifespan prewarm below
    starts it in the worker process only, off the request path; this remains
    the fallback for anything that reaches a route before that finishes, and
    for tests and scripts that never run the lifespan at all.
    """

    if not _provider_state_ready:
        _refresh_provider_state()


def _reasoning_payload(model: str | None, provider_id: str | None, effort: str | None) -> dict[str, object]:
    """Request fragment for the model's reasoning setting, or {} to send nothing.

    An effort the model does not declare is dropped rather than forwarded: a
    stale client or a hand-made request must not be able to put an arbitrary
    value into the upstream payload.
    """

    label = str(provider_preset(provider_id or "", provider_presets).get("label") or "")
    support = resolve_reasoning_support(
        model,
        provider_label=label,
        model_reasoning=model_reasoning,
        provider_reasoning_defaults=model_metadata.provider_reasoning,
    )
    if support is None:
        return {}
    return support.payload(effort)


def _llm_settings_payload() -> dict[str, object]:
    selected_provider = default_provider_preset
    return {
        "llm_provider": default_provider,
        "llm_base_url": selected_provider["base_url"],
        "llm_model": selected_provider["default_model"],
        "llm_providers": provider_presets,
        "model_presets": selected_provider["model_presets"],
        "all_model_presets": all_llm_models,
        "model_context_windows": model_metadata.context_windows,
        "provider_context_window_defaults": model_metadata.provider_context_windows,
        "model_reasoning": {name: support.as_dict() for name, support in model_reasoning.items()},
        "provider_reasoning_defaults": {
            name: support.as_dict() for name, support in model_metadata.provider_reasoning.items()
        },
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


pipeline = RAGPipeline(settings)


def _refresh_provider_state_in_background() -> None:
    """Re-fetch every provider catalogue, then swap the result in.

    `/settings` takes `_provider_state_lock` on every call, so the slow forced
    fetch runs outside it and only fills the discovery caches; the locked
    rebuild that follows reads those caches and is quick. A provider that fails
    keeps its previous list (the caches fall back to the last good entry).
    """

    load_provider_configs(
        force_model_refresh=True,
        model_context_windows=model_metadata.context_windows,
        provider_context_window_defaults=model_metadata.provider_context_windows,
        provider_context_window_ceilings=model_metadata.provider_context_window_ceilings,
        model_reasoning=model_metadata.reasoning,
    )
    _refresh_provider_state()


async def _run_discovery(phase: str, jobs) -> None:
    for label, work in jobs:
        started = time.perf_counter()
        try:
            await asyncio.to_thread(work)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("%s %s failed; keeping the previous result", phase, label)
        else:
            logger.info("%s %s finished in %.2fs", phase, label, time.perf_counter() - started)


async def _prewarm_discovery() -> None:
    """Fill the discovery caches at startup instead of on the first request.

    `/settings` needs the provider catalogues and the live mSearch collection
    list, and both were fetched by whichever request asked for them first —
    measured at roughly 4.8s and 0.6s on a cold worker, which is exactly the
    delay before the WP, prompt and collection controls can be populated.
    Warming them here means the browser's first `/settings` usually finds them
    ready.

    This does not make `/settings` non-blocking: a request that arrives before
    the prewarm finishes still waits, now on the same work already in flight.
    Failures are logged and left to the request path to retry.
    """

    await _run_discovery(
        "Startup",
        (
            ("provider discovery", _refresh_provider_state),
            ("mSearch collection discovery", pipeline.msearch_retriever.live_collections_by_prefix),
        ),
    )


async def _discovery_loop(interval_seconds: float) -> None:
    """Startup discovery, then a forced re-fetch every `interval_seconds`.

    Keeping the caches fresh here means a request never has to fetch: their
    TTLs (`LLM_MODELS_CACHE_TTL_SECONDS`, `MSEARCH_COLLECTIONS_CACHE_TTL_SECONDS`)
    are set longer than the interval, so they only expire if this refresh has
    been failing for a while. Each uvicorn worker runs its own loop.
    """

    await _prewarm_discovery()
    if interval_seconds <= 0:
        return
    while True:
        await asyncio.sleep(interval_seconds)
        await _run_discovery(
            "Scheduled",
            (
                ("provider discovery", _refresh_provider_state_in_background),
                (
                    "mSearch collection discovery",
                    functools.partial(pipeline.msearch_retriever.live_collections_by_prefix, force_refresh=True),
                ),
            ),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global analytics
    log_path = configure_logging("api")
    logger.info("Starting API; log file: %s", log_path)
    analytics = configure_analytics(
        settings.analytics_enabled,
        settings.analytics_dir,
        settings.analytics_instance_id,
    )
    if settings.auth_enabled:
        # Create the database now, so a bad AUTH_DB_PATH fails the start, not the first login.
        logger.info("User accounts enabled; database: %s", get_account_store().path)
    discovery = asyncio.create_task(_discovery_loop(settings.discovery_refresh_interval_seconds))
    yield
    logger.info("Shutting down API")
    discovery.cancel()
    with suppress(asyncio.CancelledError):
        await discovery
    pipeline.close()


app = FastAPI(title="rag-avatar", version="0.1.0", lifespan=lifespan)
app.add_middleware(AuthMiddleware)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError) -> Response:
    """FastAPI's 422, but with ASCII escapes: the default echoes the input, and
    a lone surrogate from JSON cannot be encoded as UTF-8, so the 422 became a 500."""

    body = json.dumps({"detail": jsonable_encoder(exc.errors())}, ensure_ascii=True)
    return Response(body, status_code=422, media_type="application/json")

static_dir = Path(__file__).parent / "static"
project_root = Path(__file__).resolve().parents[1]
ufal_logo_path = static_dir / "logo_ufal_110u.png"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

AI_UFAL_HOST = "ai.ufal.mff.cuni.cz"


def _is_ai_ufal_base_url(base_url: str | None) -> bool:
    parsed = urlparse((base_url or "").strip())
    return parsed.scheme == "https" and parsed.hostname == AI_UFAL_HOST


def _gated_msearch_collection_ids() -> set[str]:
    """mSearch collection ids that are AI-Ufal-only: the live collections of every
    gated WP, plus the static fallback ids when the live list is unavailable."""

    return gated_msearch_collection_ids() | pipeline.msearch_retriever.gated_collection_ids()


def _enforce_msearch_collection_policy(
    wp_id: str | None,
    msearch_collection: str | None,
    llm_base_url: str | None,
) -> None:
    # Gate per WP, but also enforce by collection id so a forged ``wp_id`` cannot
    # smuggle a gated collection in through an ungated WP.
    gated = wp_requires_aiufal(wp_id) or (msearch_collection or "").strip() in _gated_msearch_collection_ids()
    if gated and not _is_ai_ufal_base_url(llm_base_url):
        raise HTTPException(
            status_code=400,
            detail="This mSearch collection is available only with the AI Ufal provider.",
        )


def _enforce_retrieval_backend_policy(wp_id: str | None, retrieval_backend: str | None) -> None:
    if retrieval_backend != "local":
        return
    resolved_wp_id = resolve_wp_id(wp_id)
    wp = get_wp_config(resolved_wp_id)
    if not wp or not wp.local_retrieval_enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Local retrieval is available only for {default_wp_id()}. Use mSearch for {resolved_wp_id}.",
        )


def _resolve_llm_request(request: ChatRequest) -> tuple[str, str, str | None, str | None]:
    _ensure_provider_state()
    resolved_provider = resolve_llm_provider(request.llm_provider, provider_presets, request.llm_base_url)
    provider_config = provider_preset(resolved_provider, provider_presets, request.llm_base_url)
    resolved_model = request.model or provider_config["default_model"] or (
        provider_config["model_presets"][0] if provider_config["model_presets"] else ""
    )
    browser_api_key = request.llm_api_key.strip() if request.llm_api_key else None
    requested_base_url = request.llm_base_url.strip().rstrip("/") if request.llm_base_url else ""
    provider_base_url = str(provider_config.get("base_url") or "").strip().rstrip("/")
    use_server_api_key = not requested_base_url or requested_base_url == provider_base_url
    # The configured providers are trusted (one may well run on localhost); any
    # other URL comes from the request and must not reach the internal network.
    if not use_server_api_key:
        try:
            check_public_base_url(requested_base_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    server_api_key = provider_api_key(resolved_provider, provider_presets, request.llm_base_url) if use_server_api_key else ""
    resolved_api_key = browser_api_key or server_api_key or None
    public_models = provider_public_models(resolved_provider, provider_presets, request.llm_base_url)
    # Only the browser's own key unlocks a model; the server key pays for public
    # models only. The admin password is checked only when it is needed, so a
    # stale one saved in a browser neither counts as a guess nor, while the
    # shared password is blocked, breaks chats with public models.
    if (
        not browser_api_key
        and resolved_model not in public_models
        and not _admin_authorized(request.admin_password)
    ):
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


_VERSIONED_ASSET_RE = re.compile(r"(static/([\w./-]+))\?v=[^\"']*")


def _asset_version(path: Path) -> str:
    """Short content hash of a static file, cached until the file changes."""

    stat = path.stat()
    return _hash_file(path, stat.st_mtime_ns, stat.st_size)


@functools.lru_cache(maxsize=64)
def _hash_file(path: Path, mtime_ns: int, size: int) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _render_page(name: str = "index.html") -> str:
    """A static page with every `static/<file>?v=...` pointed at that file's content hash.

    The hash changes exactly when the file does, so a deploy never has to bump a
    version by hand and a browser never keeps running last week's app.js.
    """

    def versioned(match: re.Match[str]) -> str:
        asset = static_dir / match.group(2)
        try:
            return f"{match.group(1)}?v={_asset_version(asset)}"
        except OSError:
            return match.group(0)

    html = (static_dir / name).read_text(encoding="utf-8")
    html = html.replace("{{APP_TITLE}}", escape(settings.app_title))
    return _VERSIONED_ASSET_RE.sub(versioned, html)


@app.get("/", include_in_schema=False)
def index() -> HTMLResponse:
    # no-cache: the browser may store the page but must revalidate it on every
    # load. A heuristically cached index.html pinned old asset versions and
    # served a stale UI long after a deploy.
    return HTMLResponse(_render_page(), headers={"Cache-Control": "no-cache"})


@app.get("/login", include_in_schema=False)
def login_page() -> Response:
    # AuthMiddleware sends logged-out visitors of "/" here; anyone else belongs in the app.
    if not settings.auth_enabled or current_user.get() is not None:
        return RedirectResponse("./", status_code=303)
    return HTMLResponse(_render_page("login.html"), headers={"Cache-Control": "no-cache"})


@app.get("/logo_ufal_110u.png", include_in_schema=False)
def ufal_logo() -> FileResponse:
    return FileResponse(ufal_logo_path)


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/apple-touch-icon.png", include_in_schema=False)
@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def site_icon() -> FileResponse:
    # Browsers and iOS request these legacy root paths regardless of the
    # <link rel="icon"> tag; serve the SVG mark so they stop 404ing.
    return FileResponse(static_dir / "favicon.svg", media_type="image/svg+xml")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", collection=settings.qdrant_collection)


@app.get("/settings")
def get_public_settings(request: Request, owner_id: str | None = None) -> dict[str, object]:
    if request.headers.get("x-app-open") == "1":
        analytics.event(
            "app_open",
            request_context(request, settings.analytics_instance_id),
            status="ok",
            duration_ms=None,
        )
    _refresh_provider_state()
    return {
        "placeholders": [
            _for_requester(record, owner_id)
            for record in effective_global_placeholders(settings.placeholders_path)
        ],
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
            # Server-side mSearch cross-encoder rescoring is always available (no
            # local model needed); only meaningful for the mSearch backend.
            "msearch_rescore": settings.msearch_rescore,
        },
        "token_budget_defaults": {
            "context_window_tokens": settings.context_window_tokens,
            "output_token_budget_short": settings.output_token_budget_short,
            "output_token_budget_medium": settings.output_token_budget_medium,
            "output_token_budget_long": settings.output_token_budget_long,
            "min_prompt_chunks": settings.min_prompt_chunks,
            "token_budget_safety_margin": settings.token_budget_safety_margin,
            "conversation_summary_trigger_tokens": settings.conversation_summary_trigger_tokens,
            "conversation_summary_trigger_messages": settings.conversation_summary_trigger_messages,
            "conversation_recent_messages": settings.conversation_recent_messages,
        },
        "msearch_defaults": {
            "collection": settings.msearch_collection,
            "mode": settings.msearch_mode,
            "modes": ["hybrid", "semantic", "keyword"],
            "max_results": settings.msearch_max_results,
            "min_confidence": settings.msearch_min_confidence,
        },
        "prompt_defaults": {
            "system_prompt": default_system_prompt_template(),
            "user_prompt_template": default_user_prompt_template(),
        },
        "wps": _wps_payload_with_live_collections(),
        "default_wp": default_wp_id(),
        "account": account_payload(current_user.get()),
        "answer_cache_enabled": settings.answer_cache_enabled,
    }


def _wps_payload_with_live_collections() -> list[dict[str, object]]:
    """WP payload with each WP's collections replaced by the live mSearch list.

    The live list (cached 1h) holds every collection version for the WP, newest
    first. When it is unavailable the static WP config collections are kept as the
    offline fallback.
    """

    grouped = pipeline.msearch_retriever.live_collections_by_prefix()
    payload = wp_public_payload()
    builtin_overrides = load_builtin_prompt_overrides(settings.prompt_presets_path)
    for wp in payload:
        for prompt in wp["builtin_prompts"]:
            override = builtin_overrides.get(prompt["id"])
            if override is not None:
                prompt["query_transform"] = override["query_transform"]
        live = grouped.get(wp_collection_prefix(wp["id"])) or []
        if not live:
            continue
        static_collections = wp["collections"]
        configured_default = next(
            (
                collection
                for collection in static_collections
                if collection["id"] == wp["default_collection_id"]
            ),
            None,
        )
        wp["collections"] = [
            {
                "id": entry["collection_id"],
                "label": entry["collection_name"],
                "msearch_collection_id": entry["collection_id"],
            }
            for entry in live
        ]
        default_live = _configured_default_live_collection(configured_default, live)
        # Prefer the configured default when it is present in the live list;
        # otherwise default to the newest live version.
        wp["default_collection_id"] = (default_live or live[0])["collection_id"]
    return payload


def _configured_default_live_collection(
    configured: object,
    live: list[dict[str, str]],
) -> dict[str, str] | None:
    if not isinstance(configured, dict):
        return None

    configured_label = str(configured.get("label") or "").strip()
    configured_msearch_id = str(configured.get("msearch_collection_id") or "").strip()
    for entry in live:
        if configured_label and entry["collection_name"] == configured_label:
            return entry
        if configured_msearch_id and entry["collection_id"] == configured_msearch_id:
            return entry
    return None


# Anyone can press the refresh button, so a forced refresh of the provider model
# lists and mSearch collections runs at most this often for the whole server.
PROVIDER_REFRESH_COOLDOWN_SECONDS = 60.0
_provider_refresh_lock = threading.Lock()
_last_forced_provider_refresh = float("-inf")


def _claim_forced_provider_refresh() -> bool:
    global _last_forced_provider_refresh
    now = time.monotonic()
    with _provider_refresh_lock:
        if now - _last_forced_provider_refresh < PROVIDER_REFRESH_COOLDOWN_SECONDS:
            return False
        _last_forced_provider_refresh = now
        return True


@app.post("/llm-providers/refresh")
def refresh_llm_providers() -> dict[str, object]:
    if _claim_forced_provider_refresh():
        _refresh_provider_state(force_model_refresh=True)
        # Drop the cached mSearch collection list and re-fetch it now, so the refresh
        # button updates the per-WP collection options too (not just on next load).
        clear_collections_cache()
    else:
        # Within the cooldown: answer with the lists fetched moments ago.
        _refresh_provider_state()
    return {**_llm_settings_payload(), "wps": _wps_payload_with_live_collections()}


def _questions_path_for_wp(wp_id: str | None) -> tuple[str, Path | None]:
    resolved_wp_id = resolve_wp_id(wp_id)
    wp = get_wp_config(resolved_wp_id)
    if not wp or not wp.questions_path:
        return resolved_wp_id, None
    questions_path = Path(wp.questions_path)
    if not questions_path.is_absolute():
        questions_path = project_root / questions_path
    return resolved_wp_id, questions_path


def _load_questions_for_wp(wp_id: str | None) -> tuple[str, list[str]]:
    resolved_wp_id, questions_path = _questions_path_for_wp(wp_id)
    if questions_path is None:
        raise HTTPException(status_code=404, detail=f"No questions are configured for {resolved_wp_id}.")
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail=f"Questions file for {resolved_wp_id} was not found.")
    questions = [line.strip() for line in questions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not questions:
        raise HTTPException(status_code=404, detail=f"Questions file for {resolved_wp_id} does not contain any questions.")
    return resolved_wp_id, questions


def _questions_for_analytics(wp_id: str | None) -> list[str]:
    try:
        return _load_questions_for_wp(wp_id)[1]
    except (HTTPException, OSError, UnicodeError):
        return []


def _prompt_kind(prompt_id: str | None) -> str:
    clean = (prompt_id or "").strip()
    if any(clean == prompt.id for wp in WP_CONFIGS for prompt in wp.builtin_prompts):
        return "builtin"
    if clean.startswith(("local-", "draft-")) or not clean:
        return "custom"
    return "shared"


def _key_source(request: ChatRequest, resolved_api_key: str | None) -> str:
    if request.llm_api_key and request.llm_api_key.strip():
        return "browser"
    return "server" if resolved_api_key else "none"


def _turn_fields(
    body: ChatRequest | RetrieveRequest,
    *,
    operation: str,
    mode: str,
    provider: str | None = None,
    requested_model: str | None = None,
    base_url: str | None = None,
    key_source: str = "none",
) -> dict[str, object]:
    backend = body.retrieval_backend or settings.retrieval_backend
    return {
        **question_metadata(body.question, _questions_for_analytics(body.wp_id)),
        "wp_id": resolve_wp_id(body.wp_id),
        "operation": operation,
        "mode": mode,
        "provider": provider,
        "requested_model": requested_model,
        "upstream_model": None,
        "endpoint_host": endpoint_host(base_url),
        "key_source": key_source,
        "prompt_kind": _prompt_kind(body.prompt_preset_id),
        "prompt_id": body.prompt_preset_id,
        "retrieval_backend": backend,
        "msearch_collection": body.msearch_collection if backend == "msearch" else None,
        "msearch_mode": body.msearch_mode if backend == "msearch" else None,
        "msearch_rescore": body.msearch_rescore if backend == "msearch" else None,
        "msearch_min_confidence": body.msearch_min_confidence if backend == "msearch" else None,
        "top_k": body.top_k,
        "dense_weight": body.dense_weight,
        "bm25_weight": body.bm25_weight,
        "min_score": body.min_score,
        "min_relative_score": body.min_relative_score,
        "rerank_enabled": body.rerank_enabled,
        "rerank_weight": body.rerank_weight,
        "rerank_candidates": body.rerank_candidates,
        "query_transform_ms": body.query_transform_ms,
        "query_transform_kind": body.query_transform_kind,
        "retrieval_query_was_rewritten": None,
    }


@app.get("/questions/random")
def random_question(wp_id: str | None = None) -> dict[str, str]:
    resolved_wp_id, questions = _load_questions_for_wp(wp_id)
    return {"question": random.choice(questions), "wp_id": resolved_wp_id}


@app.get("/questions")
def list_questions(wp_id: str | None = None) -> dict[str, object]:
    resolved_wp_id, questions = _load_questions_for_wp(wp_id)
    return {"questions": questions, "wp_id": resolved_wp_id}


PROMPT_PRESET_FORBIDDEN_DETAIL = (
    "Tento sdílený prompt patří jinému prohlížeči. Odemkni ho sdíleným heslem, abys ho mohl změnit."
)


def _secure_eq(a: str, b: str) -> bool:
    """Constant-time string compare that tolerates non-ASCII input.

    hmac.compare_digest raises TypeError on str args containing non-ASCII
    characters, so compare the UTF-8 encoded bytes instead.
    """
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _find_prompt_preset(preset_id: str) -> dict[str, object] | None:
    return next(
        (preset for preset in load_prompt_presets(settings.prompt_presets_path) if preset["id"] == preset_id),
        None,
    )


def _owned_by(record: dict[str, object], owner_id: str | None) -> bool:
    owner = str(record.get("owner_id") or "").strip()
    requester = (owner_id or "").strip()
    return bool(owner and requester) and _secure_eq(owner, requester)


def _for_requester(record: dict[str, object], owner_id: str | None) -> dict[str, object]:
    """A stored record as sent to a browser.

    The owner id is what proves ownership on writes, so it never leaves the
    server; the browser learns only whether the record is its own.
    """

    public = {key: value for key, value in record.items() if key != "owner_id"}
    public["mine"] = _owned_by(record, owner_id)
    return public


# What anyone can store through the shared lists. Each save rewrites the whole
# JSON file, so the file is capped as well as each item. A per-browser count
# would not help: the browser makes up its own id, so a script just uses new ones.
SHARED_HISTORY_LIMITS = {"max_item_bytes": 1_000_000, "max_file_bytes": 50_000_000}
PROMPT_PRESET_LIMITS = {"max_item_bytes": 200_000, "max_file_bytes": 10_000_000}
PLACEHOLDER_LIMITS = {"max_item_bytes": 50_000, "max_file_bytes": 5_000_000}


def _stored_fields(request: BaseModel) -> dict[str, object]:
    # Everything that gets stored counts, the owner id included.
    return request.model_dump(exclude={"admin_password"})


def _check_saved_item(path: Path, item: dict[str, object], *, max_item_bytes: int, max_file_bytes: int) -> None:
    # Measured as the files are written (indented): compact JSON would undercount
    # a deeply nested value many times over.
    size = len(json.dumps(item, ensure_ascii=False, indent=2).encode("utf-8"))
    if size > max_item_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Položka je příliš velká ({size // 1000} kB, nejvýš {max_item_bytes // 1000} kB).",
        )
    try:
        file_size = path.stat().st_size
    except OSError:
        file_size = 0
    if file_size + size > max_file_bytes:
        raise HTTPException(
            status_code=409,
            detail="Na serveru už není místo pro další položky. Smaž nějaké staré, nebo dej vědět správci.",
        )


def _can_modify_prompt_preset(
    preset: dict[str, object],
    owner_id: str | None,
    password: str | None,
) -> bool:
    return _owned_by(preset, owner_id) or _admin_authorized(password)


def _shared_password_ok(password: str | None) -> bool:
    """Check the shared ADMIN_PASSWORD, counting wrong guesses server-wide."""

    supplied = (password or "").strip()
    if not settings.admin_password or not supplied:
        return False
    ok, wait = admin_password_guard.check(supplied, settings.admin_password)
    if wait:
        raise HTTPException(
            status_code=429,
            detail=(
                "Sdílené admin heslo je kvůli opakovaným chybným pokusům dočasně zablokované. "
                f"Zkus to znovu za {math.ceil(wait / 60)} min."
            ),
        )
    return ok


def _admin_authorized(password: str | None) -> bool:
    """The shared ADMIN_PASSWORD, or a logged-in admin account, which needs none."""

    return is_admin_user() or _shared_password_ok(password)


def _require_admin_password(password: str | None) -> None:
    if not _admin_authorized(password):
        raise HTTPException(
            status_code=403,
            detail="Úpravy vestavěných profilů vyžadují admin přístup.",
        )


def _builtin_prompt_exists(prompt_id: str) -> bool:
    return any(
        prompt.id == prompt_id
        for wp in WP_CONFIGS
        for prompt in wp.builtin_prompts
    )


@app.get("/prompt-presets", response_model=list[PromptPreset])
def get_prompt_presets(owner_id: str | None = None) -> list[PromptPreset]:
    return [
        PromptPreset(**_for_requester(preset, owner_id))
        for preset in load_prompt_presets(settings.prompt_presets_path)
    ]


@app.post("/unlock", response_model=UnlockResponse)
def unlock_models(request: UnlockRequest) -> UnlockResponse:
    return UnlockResponse(unlocked=_shared_password_ok(request.password))


@app.post("/prompt-presets", response_model=PromptPreset)
def post_prompt_preset(request: PromptPresetSaveRequest) -> PromptPreset:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Prompt preset name is required.")
    existing = _find_prompt_preset(request.id) if request.id else None
    if existing is not None and not _can_modify_prompt_preset(existing, request.owner_id, request.admin_password):
        raise HTTPException(status_code=403, detail=PROMPT_PRESET_FORBIDDEN_DETAIL)
    _check_saved_item(settings.prompt_presets_path, _stored_fields(request), **PROMPT_PRESET_LIMITS)
    try:
        preset = save_prompt_preset(
            settings.prompt_presets_path,
            name=name,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            wp_id=request.wp_id,
            note=request.note,
            placeholders={
                name: definition.model_dump() for name, definition in request.placeholders.items()
            },
            query_transform=(
                request.query_transform.model_dump()
                if request.query_transform is not None
                else None
            ),
            preset_id=request.id,
            owner_id=request.owner_id,
        )
    except OSError as exc:
        logger.exception("Could not save prompt preset to %s", settings.prompt_presets_path)
        raise HTTPException(
            status_code=500,
            detail="Sdílený prompt se nepodařilo uložit na server.",
        ) from exc
    return PromptPreset(**_for_requester(preset, request.owner_id))


@app.put(
    "/prompt-presets/builtin-overrides/{prompt_id}",
    response_model=BuiltinPromptOverride,
)
def put_builtin_prompt_override(
    prompt_id: str,
    request: BuiltinPromptOverrideSaveRequest,
) -> BuiltinPromptOverride:
    _require_admin_password(request.admin_password)
    if not _builtin_prompt_exists(prompt_id):
        raise HTTPException(status_code=404, detail="Vestavěný prompt nebyl nalezen.")
    try:
        override = save_builtin_prompt_override(
            settings.prompt_presets_path,
            prompt_id,
            request.query_transform.model_dump(),
        )
    except OSError as exc:
        logger.exception(
            "Could not save built-in prompt override to %s",
            settings.prompt_presets_path,
        )
        raise HTTPException(
            status_code=500,
            detail="Transformaci vestavěného promptu se nepodařilo uložit.",
        ) from exc
    return BuiltinPromptOverride(prompt_id=prompt_id, **override)


@app.delete(
    "/prompt-presets/builtin-overrides/{prompt_id}",
    status_code=204,
)
def remove_builtin_prompt_override(
    prompt_id: str,
    admin_password: str | None = None,
) -> Response:
    _require_admin_password(admin_password)
    if not _builtin_prompt_exists(prompt_id):
        raise HTTPException(status_code=404, detail="Vestavěný prompt nebyl nalezen.")
    try:
        delete_builtin_prompt_override(settings.prompt_presets_path, prompt_id)
    except OSError as exc:
        logger.exception(
            "Could not delete built-in prompt override from %s",
            settings.prompt_presets_path,
        )
        raise HTTPException(
            status_code=500,
            detail="Výchozí nastavení transformace se nepodařilo obnovit.",
        ) from exc
    return Response(status_code=204)


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


def _effective_query_transform(
    prompt_preset_id: str | None,
) -> dict[str, object] | None:
    prompt_id = (prompt_preset_id or "").strip()
    if prompt_id:
        saved = _find_prompt_preset(prompt_id)
        if saved is not None and saved.get("query_transform") is not None:
            return saved["query_transform"]
        builtin = load_builtin_prompt_overrides(settings.prompt_presets_path).get(prompt_id)
        if builtin is not None:
            return builtin["query_transform"]
    return None


def _resolved_query_transform_action(request: QueryTransformRequest) -> dict[str, object]:
    prompt_id = (request.prompt_preset_id or "").strip()
    # Browser-local/draft prompts are not stored on the server, so their
    # configured action must travel with the request. Server-known and built-in
    # prompts are always resolved from server configuration; do not let a
    # client-supplied action bypass an explicitly disabled prompt.
    if request.action is not None and prompt_id.startswith(("local-", "draft-")):
        return request.action.model_dump()
    transform = _effective_query_transform(request.prompt_preset_id)
    if not transform or not transform.get("enabled"):
        raise HTTPException(status_code=400, detail="Úprava dotazu není pro tento profil povolena.")
    actions = transform.get("actions")
    if not isinstance(actions, list) or not actions:
        raise HTTPException(status_code=400, detail="Profil nemá nakonfigurovanou žádnou úpravu dotazu.")
    action_id = (request.action_id or transform.get("default_action") or "").strip()
    action = next(
        (item for item in actions if isinstance(item, dict) and item.get("id") == action_id),
        None,
    )
    if action is None:
        raise HTTPException(status_code=400, detail="Požadovaná úprava dotazu není v profilu dostupná.")
    return action


def _clean_transformed_query(value: str) -> str:
    query = " ".join((value or "").split()).strip()
    if len(query) >= 2 and query[0] == query[-1] and query[0] in {'"', "'", "`"}:
        query = query[1:-1].strip()
    for prefix in ("Dotaz:", "Query:", "Search query:", "Vyhledávací dotaz:"):
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix) :].strip()
    return query


@app.post("/query-transform", response_model=QueryTransformResponse)
def transform_query(request: QueryTransformRequest, http_request: Request) -> QueryTransformResponse:
    context = request_context(http_request, settings.analytics_instance_id)
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Dotaz nesmí být prázdný.")
    action = _resolved_query_transform_action(request)
    action_id = str(action.get("id") or "").strip()
    action_type = str(action.get("type") or "").strip()
    try:
        if action_type == "lindat":
            model = str(action.get("model") or "").strip()
            if not valid_lindat_model(model):
                raise HTTPException(status_code=400, detail="Neplatný model Charles Translatoru.")
            base_url = settings.lindat_translation_base_url.strip().rstrip("/")
            response = httpx.post(
                f"{base_url}/{model}",
                files={"input_text": (None, question)},
                timeout=settings.query_transform_timeout,
            )
            response.raise_for_status()
            transformed = response.text.strip()
        elif action_type == "llm":
            template = str(action.get("prompt_template") or "")
            if "{question}" not in template:
                raise HTTPException(
                    status_code=400,
                    detail="Akce úpravy dotazu nemá platnou šablonu promptu (chybí {question}).",
                )
            instruction = (request.instruction or "").strip()
            rendered_prompt = render_query_transform_prompt(template, question, instruction)
            resolved_provider, resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
            with bind_context(
                context,
                provider=resolved_provider,
                key_source=_key_source(request, resolved_api_key),
                purpose="query_transform",
            ):
                generation = pipeline.llm.generate(
                    [{"role": "user", "content": rendered_prompt}],
                    model=resolved_model,
                    api_key=resolved_api_key,
                    base_url=resolved_base_url,
                )
            transformed = _clean_transformed_query(generation.answer)
            logger.info(
                "Transformed query with provider=%s model=%s action=%s",
                resolved_provider,
                resolved_model,
                action_id,
            )
        else:
            raise HTTPException(status_code=400, detail="Neznámý způsob úpravy dotazu.")
    except HTTPException:
        raise
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        logger.warning("Query transform failed action=%s: %s", action_id, exc)
        raise HTTPException(
            status_code=502,
            detail="Dotaz se nepodařilo upravit. Původní dotaz zůstal beze změny.",
        ) from exc
    if not transformed:
        raise HTTPException(
            status_code=502,
            detail="Úprava dotazu vrátila prázdný výsledek. Původní dotaz zůstal beze změny.",
        )
    return QueryTransformResponse(
        original_question=question,
        transformed_query=transformed,
        action_id=action_id,
        action_type=action_type,
    )


SHARED_HISTORY_FORBIDDEN_DETAIL = (
    "Tento sdílený záznam patří jinému prohlížeči. Odemkni ho sdíleným heslem, abys ho mohl smazat."
)


def _find_shared_history_item(item_id: str) -> dict[str, object] | None:
    return next(
        (item for item in load_shared_history(settings.shared_history_path) if item["id"] == item_id),
        None,
    )


def _can_modify_shared_history_item(
    item: dict[str, object], owner_id: str | None, password: str | None
) -> bool:
    return _owned_by(item, owner_id) or _admin_authorized(password)


@app.get("/shared-history", response_model=list[SharedHistoryItem])
def get_shared_history(owner_id: str | None = None) -> list[SharedHistoryItem]:
    # Link-only items stay out of the list, except for the browser that owns them.
    return [
        SharedHistoryItem(**_for_requester(item, owner_id))
        for item in load_shared_history(settings.shared_history_path)
        if item["visibility"] == "listed" or _owned_by(item, owner_id)
    ]


@app.get("/shared-history/{item_id}", response_model=SharedHistoryItem)
def get_shared_history_item(item_id: str, owner_id: str | None = None) -> SharedHistoryItem:
    item = _find_shared_history_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Sdílená položka nebyla nalezena.")
    return SharedHistoryItem(**_for_requester(item, owner_id))


@app.patch("/shared-history/{item_id}", response_model=SharedHistoryItem)
def patch_shared_history_item(item_id: str, request: SharedHistoryUpdateRequest) -> SharedHistoryItem:
    existing = _find_shared_history_item(item_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Sdílená položka nebyla nalezena.")
    if not _can_modify_shared_history_item(existing, request.owner_id, request.admin_password):
        raise HTTPException(
            status_code=403,
            detail="Tento sdílený záznam patří jinému prohlížeči. Odemkni ho sdíleným heslem, abys ho mohl změnit.",
        )
    # The item as it will be stored: an edited note joins the existing answer.
    merged = {**existing, "note": existing.get("note", "") if request.note is None else request.note}
    _check_saved_item(settings.shared_history_path, merged, **SHARED_HISTORY_LIMITS)
    updated = update_shared_history_item(
        settings.shared_history_path,
        item_id,
        visibility=request.visibility,
        note=request.note,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Sdílená položka nebyla nalezena.")
    return SharedHistoryItem(**_for_requester(updated, request.owner_id))


@app.post("/shared-history", response_model=SharedHistoryItem)
def post_shared_history(request: SharedHistorySaveRequest) -> SharedHistoryItem:
    _check_saved_item(settings.shared_history_path, _stored_fields(request), **SHARED_HISTORY_LIMITS)
    item = save_shared_history_item(
        settings.shared_history_path,
        owner_id=request.owner_id,
        author_name=request.author_name,
        note=request.note,
        question=request.question,
        answer=request.answer,
        reasoning=request.reasoning,
        mode=request.mode,
        settings=request.settings,
        sources=request.sources,
        retrieved_chunks=request.retrieved_chunks,
        source_count=request.source_count,
        created_at=request.created_at,
        model_used=request.model_used,
        upstream_model=request.upstream_model,
        response_time_seconds=request.response_time_seconds,
        token_budget=request.token_budget,
        visibility=request.visibility,
    )
    return SharedHistoryItem(**_for_requester(item, request.owner_id))


@app.delete("/shared-history/{item_id}", status_code=204)
def remove_shared_history_item(
    item_id: str,
    owner_id: str | None = None,
    admin_password: str | None = None,
) -> Response:
    existing = _find_shared_history_item(item_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Shared history item not found.")
    if not _can_modify_shared_history_item(existing, owner_id, admin_password):
        raise HTTPException(status_code=403, detail=SHARED_HISTORY_FORBIDDEN_DETAIL)
    delete_shared_history_item(settings.shared_history_path, item_id)
    return Response(status_code=204)


PLACEHOLDER_FORBIDDEN_DETAIL = (
    "Tato sdílená proměnná patří jinému prohlížeči. Odemkni ji sdíleným heslem, abys ji mohl změnit."
)
BUILTIN_PLACEHOLDER_FORBIDDEN_DETAIL = (
    "Vestavěnou sdílenou proměnnou může na serveru změnit jen uživatel se sdíleným heslem."
)


def _find_placeholder(name: str) -> dict[str, object] | None:
    return next(
        (item for item in load_placeholders(settings.placeholders_path) if item["name"] == name),
        None,
    )


def _can_modify_placeholder(placeholder: dict[str, object], owner_id: str | None, password: str | None) -> bool:
    if str(placeholder.get("name") or "") in DEFAULT_PLACEHOLDERS:
        return _admin_authorized(password)
    return _owned_by(placeholder, owner_id) or _admin_authorized(password)


@app.get("/placeholders", response_model=list[Placeholder])
def get_placeholders(owner_id: str | None = None) -> list[Placeholder]:
    return [
        Placeholder(**_for_requester(item, owner_id))
        for item in load_placeholders(settings.placeholders_path)
    ]


@app.post("/placeholders", response_model=Placeholder)
def post_placeholder(request: PlaceholderSaveRequest) -> Placeholder:
    # Checked under the name it will be stored as, so "LENGTH " cannot slip past
    # the checks for "length".
    name = placeholder_name(request.name)
    if not name:
        raise HTTPException(status_code=400, detail="Placeholder name is required.")
    existing = _find_placeholder(name)
    if existing is None and name in DEFAULT_PLACEHOLDERS and not _admin_authorized(request.admin_password):
        raise HTTPException(status_code=403, detail=BUILTIN_PLACEHOLDER_FORBIDDEN_DETAIL)
    if existing is not None and not _can_modify_placeholder(existing, request.owner_id, request.admin_password):
        if name in DEFAULT_PLACEHOLDERS:
            raise HTTPException(status_code=403, detail=BUILTIN_PLACEHOLDER_FORBIDDEN_DETAIL)
        raise HTTPException(status_code=403, detail=PLACEHOLDER_FORBIDDEN_DETAIL)
    _check_saved_item(settings.placeholders_path, _stored_fields(request), **PLACEHOLDER_LIMITS)
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
    return Placeholder(**_for_requester(record, request.owner_id))


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
        if name in DEFAULT_PLACEHOLDERS:
            raise HTTPException(status_code=403, detail=BUILTIN_PLACEHOLDER_FORBIDDEN_DETAIL)
        raise HTTPException(status_code=403, detail=PLACEHOLDER_FORBIDDEN_DETAIL)
    delete_placeholder(settings.placeholders_path, name)
    return Response(status_code=204)


def _resolve_chat_placeholders(request: ChatRequest) -> tuple[dict, dict[str, str]]:
    """Resolve placeholder defs and selections for a chat request.

    As of 14d, ``placeholder_defs`` carries the FULLY RESOLVED effective def for
    each placeholder the prompt uses, already collapsed by the frontend in the
    order inline -> browser-local global -> shared overlay. The server is stateless
    about ``localStorage``, so it treats ``placeholder_defs`` as the highest
    precedence source: this lets browser-local globals (which the server cannot
    see) take effect. The shared overlay (``placeholders.json``) and the
    ``DEFAULT_PLACEHOLDERS`` code floor below it are a harmless fallback for any
    name the request omits. Selections come from the dedicated request fields.
    """

    system_template = (request.system_prompt or "").strip() or default_system_prompt_template()
    user_template = (request.user_prompt_template or "").strip() or default_user_prompt_template()
    names = template_placeholder_names(system_template) | template_placeholder_names(user_template)
    inline_defs = {
        name: placeholder_def_from_record(definition)
        for name, definition in (request.placeholder_defs or {}).items()
        if isinstance(definition, dict)
    }
    shared_global = placeholder_defs_from_records(load_placeholders(settings.placeholders_path))
    defs = resolve_placeholder_defs(
        names,
        inline_defs=inline_defs,
        shared_global_defs=shared_global,
        code_default_defs=DEFAULT_PLACEHOLDERS,
    )
    # The frontend sends a generic ``{placeholderName: value}`` map; the server is
    # agnostic about which names exist (select option name or typed text string).
    selections = {
        str(name): str(value)
        for name, value in (request.selections or {}).items()
        if value is not None
    }
    return defs, selections


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest, http_request: Request) -> RetrieveResponse:
    started = time.perf_counter()
    context = request_context(http_request, settings.analytics_instance_id)
    fields = _turn_fields(request, operation="retrieve_only", mode="blocking")
    try:
        # No mSearch provider gate here: retrieve-only returns chunks to the
        # browser and never sends them to an LLM. The gate exists solely to keep
        # gated (e.g. WP2) content from reaching a provider outside AI Ufal, so
        # the selected provider is irrelevant for retrieval and must not cause a
        # spurious accept/reject based on the server's default provider.
        _enforce_retrieval_backend_policy(request.wp_id, request.retrieval_backend)
        retrieval_query = (
            request.retrieval_query.strip()
            if request.retrieval_query is not None
            else request.question
        )
        if not retrieval_query:
            raise HTTPException(status_code=400, detail="Vyhledávací dotaz nesmí být prázdný.")
        retrieval_timings: dict[str, float | None] = {}
        chunks, baseline_chunks = pipeline.retrieve_with_baseline(
            retrieval_query,
            request.top_k,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight,
            min_score=request.min_score,
            min_relative_score=request.min_relative_score,
            retrieval_backend=request.retrieval_backend,
            msearch_collection=request.msearch_collection,
            msearch_mode=request.msearch_mode,
            msearch_min_confidence=request.msearch_min_confidence,
            msearch_rescore=request.msearch_rescore,
            rerank_enabled=request.rerank_enabled,
            rerank_weight=request.rerank_weight,
            rerank_candidates=request.rerank_candidates,
            timings=retrieval_timings,
        )
        retrieval_ms = ms(retrieval_timings.get("retrieval_seconds") or 0.0)
        rerank_ms = ms(retrieval_timings["rerank_seconds"]) if retrieval_timings.get("rerank_seconds") is not None else None
    except HTTPException as exc:
        analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), http_status=exc.status_code, error_code=analytics_error_code(exc, exc.status_code))
        # Intended 4xx from policy enforcement must keep its status, not become 500.
        raise
    except Exception as exc:
        analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), http_status=500, error_code="retrieval_error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    analytics.event("turn", context, **fields, status="ok", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, http_status=200, error_code=None)
    return RetrieveResponse(
        question=request.question,
        original_question=request.question,
        retrieval_query=retrieval_query,
        retrieved_chunks=[_serialize_retrieved_chunk(chunk) for chunk in chunks],
        baseline_chunks=[_serialize_retrieved_chunk(chunk) for chunk in baseline_chunks],
    )


@app.post("/retrieve/stream")
def retrieve_stream(request: RetrieveRequest, http_request: Request) -> StreamingResponse:
    context = request_context(http_request, settings.analytics_instance_id)
    fields = _turn_fields(request, operation="retrieve_only", mode="streaming")

    def event_stream():
        started = time.perf_counter()
        retrieval_ms = None
        rerank_ms = None
        preliminary_ms = None
        final_sources_ms = None
        try:
            # No mSearch provider gate here for the same reason as /retrieve:
            # retrieve-only never sends chunks to an LLM provider.
            _enforce_retrieval_backend_policy(request.wp_id, request.retrieval_backend)
            retrieval_query = (
                request.retrieval_query.strip()
                if request.retrieval_query is not None
                else request.question
            )
            if not retrieval_query:
                raise HTTPException(status_code=400, detail="Vyhledávací dotaz nesmí být prázdný.")
            retrieval_started = time.perf_counter()
            candidates = pipeline.retrieve_candidates(
                retrieval_query,
                request.top_k,
                dense_weight=request.dense_weight,
                bm25_weight=request.bm25_weight,
                min_score=request.min_score,
                min_relative_score=request.min_relative_score,
                retrieval_backend=request.retrieval_backend,
                msearch_collection=request.msearch_collection,
                msearch_mode=request.msearch_mode,
                msearch_min_confidence=request.msearch_min_confidence,
                msearch_rescore=request.msearch_rescore,
                rerank_enabled=request.rerank_enabled,
                rerank_weight=request.rerank_weight,
                rerank_candidates=request.rerank_candidates,
            )
            retrieval_ms = ms(time.perf_counter() - retrieval_started)
            baseline_payload = [_serialize_retrieved_chunk(chunk) for chunk in candidates.baseline]
            if candidates.rerank_active and candidates.baseline:
                preliminary_ms = ms(time.perf_counter() - started)
                yield _sse_event(
                    "preliminary_sources",
                    {
                        "question": request.question,
                        "original_question": request.question,
                        "retrieval_query": retrieval_query,
                        "retrieved_chunks": baseline_payload,
                        "sources": [_serialize_source(chunk) for chunk in candidates.baseline],
                    },
                )

            retrieved: list = []
            rerank_seconds = 0.0
            for event in pipeline.apply_rerank_iter(retrieval_query, candidates):
                kind = event[0]
                if kind == "eta":
                    yield _sse_event("rerank_progress", {"done": 0, "total": 0, "eta_seconds": event[1]})
                elif kind == "progress":
                    _, done, total, elapsed = event
                    eta = round(elapsed / done * (total - done), 2) if done else None
                    yield _sse_event(
                        "rerank_progress",
                        {"done": done, "total": total, "elapsed": round(elapsed, 3), "eta_seconds": eta},
                    )
                else:  # "result"
                    retrieved, rerank_seconds = event[1], event[2]

            rerank_ms = ms(rerank_seconds) if candidates.rerank_active else None

            payload = {
                "question": request.question,
                "original_question": request.question,
                "retrieval_query": retrieval_query,
                "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in retrieved],
                "baseline_chunks": baseline_payload,
                "sources": [_serialize_source(chunk) for chunk in retrieved],
                "rerank_time_seconds": round(rerank_seconds, 3) if candidates.rerank_active else None,
            }
            final_sources_ms = ms(time.perf_counter() - started)
            yield _sse_event("sources", payload)
            yield _sse_event("done", payload)
            analytics.event(
                "turn", context, **fields, status="ok", duration_ms=ms(time.perf_counter() - started),
                total_ms=ms(time.perf_counter() - started), retrieval_ms=retrieval_ms, rerank_ms=rerank_ms,
                time_to_preliminary_sources_ms=preliminary_ms, time_to_final_sources_ms=final_sources_ms,
                http_status=200, error_code=None,
            )
        except HTTPException as exc:
            yield _sse_event("error", {"detail": exc.detail})
            analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, http_status=200, error_code=analytics_error_code(exc, exc.status_code))
        except GeneratorExit:
            analytics.event("turn", context, **fields, status="cancelled", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, http_status=200, error_code="client_cancelled")
            raise
        except Exception as exc:
            logger.exception("Streaming retrieve failed")
            yield _sse_event("error", {"detail": str(exc)})
            analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, http_status=200, error_code="retrieval_error")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _output_budget_length(placeholder_defs: dict, selections: dict[str, str]) -> str:
    """Pick the short/medium/long key used only for output-token budget sizing.

    Output budget is the one place ``length`` stays slightly special: it keys on
    short/medium/long regardless of what text the ``length`` placeholder renders.
    Derive it from the ``length`` selection, falling back to the resolved
    ``length`` def's default (then ``medium``).
    """

    length_def = placeholder_defs.get("length")
    default = length_def.default if length_def is not None else "medium"
    return selections.get("length") or default or "medium"


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    placeholder_defs, selections = _resolve_chat_placeholders(request)
    length = _output_budget_length(placeholder_defs, selections)
    started = time.perf_counter()
    context = request_context(http_request, settings.analytics_instance_id)
    resolved_provider = request.llm_provider
    resolved_model = request.model
    resolved_api_key = None
    resolved_base_url = request.llm_base_url
    fields = _turn_fields(
        request,
        operation="chat",
        mode="blocking",
        provider=resolved_provider,
        requested_model=resolved_model,
        base_url=resolved_base_url,
        key_source="browser" if request.llm_api_key and request.llm_api_key.strip() else "none",
    )
    try:
        if request.retrieval_query is not None and not _clean_transformed_query(request.retrieval_query):
            raise HTTPException(status_code=400, detail="Vyhledávací dotaz nesmí být prázdný.")
        resolved_provider, resolved_model, resolved_api_key, resolved_base_url = _resolve_llm_request(request)
        key_source = _key_source(request, resolved_api_key)
        fields.update(provider=resolved_provider, requested_model=resolved_model, endpoint_host=endpoint_host(resolved_base_url), key_source=key_source)
        _enforce_msearch_collection_policy(
            request.wp_id, request.msearch_collection or settings.msearch_collection, resolved_base_url
        )
        _enforce_retrieval_backend_policy(request.wp_id, request.retrieval_backend)
        with bind_context(context, provider=resolved_provider, key_source=key_source, purpose="answer"):
            response = pipeline.chat(
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
            msearch_rescore=request.msearch_rescore,
            rerank_enabled=request.rerank_enabled,
            rerank_weight=request.rerank_weight,
            rerank_candidates=request.rerank_candidates,
            rewrite_query_for_retrieval=request.rewrite_query_for_retrieval,
            retrieval_query_override=request.retrieval_query,
                use_retrieval_query_for_answer=request.use_retrieval_query_for_answer,
                reasoning=_reasoning_payload(resolved_model, resolved_provider, request.reasoning_effort),
            )
        # A pydantic model, not a mapping — analytics splats it as kwargs.
        budget = response.token_budget.model_dump() if response.token_budget else {}
        event_fields = {
            **fields,
            "retrieval_query_was_rewritten": response.retrieval_query_was_rewritten,
            "retrieval_query_rewrite_attempted": response.retrieval_query_rewrite_attempted,
            "retrieval_query_rewrite_skip_reason": response.retrieval_query_rewrite_skip_reason,
            "upstream_model": response.upstream_model,
        }
        analytics.event(
            "turn", context, **event_fields, status="ok", duration_ms=ms(time.perf_counter() - started),
            total_ms=ms(time.perf_counter() - started),
            retrieval_ms=ms(response.retrieval_time_seconds) if response.retrieval_time_seconds is not None else None,
            rerank_ms=ms(response.rerank_time_seconds) if response.rerank_time_seconds is not None else None,
            prompt_prepare_ms=ms(response.prompt_prepare_time_seconds) if response.prompt_prepare_time_seconds is not None else None,
            generation_ms=ms(response.generation_time_seconds) if response.generation_time_seconds is not None else None,
            http_status=200, error_code=None,
            **text_lengths(response.answer, "answer"), answer_tokens_estimated=estimated_tokens(response.answer),
            warning_count=len(response.chunk_budget_warnings), **budget,
        )
        return response
    except PromptBudgetError as exc:
        analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), http_status=400, error_code="token_budget")
        raise HTTPException(status_code=400, detail=exc.to_payload()) from exc
    except HTTPException as exc:
        analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), http_status=exc.status_code, error_code=analytics_error_code(exc, exc.status_code))
        # Intended 4xx from policy/model enforcement must keep its status, not become 500.
        raise
    except Exception as exc:
        analytics.event("turn", context, **fields, status="error", duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started), http_status=500, error_code=analytics_error_code(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


_answer_cache: AnswerCache | None = None
_answer_cache_lock = threading.Lock()
# Pause between the pieces of a replayed answer; tests replace it.
_replay_sleep = time.sleep

# The settings a request field falls back to when it is unset, plus the ones
# that shape retrieval and the prompt without a request field. They are part
# of the cache key, so changing one in .env does not serve answers made under
# the old value.
_ANSWER_CACHE_SETTINGS = (
    "retrieval_backend",
    "top_k",
    "min_score",
    "min_relative_score",
    "qdrant_collection",
    "embedding_model",
    "reranker_enabled",
    "reranker_model",
    "reranker_weight",
    "reranker_candidates",
    "reranker_max_length",
    "msearch_base_url",
    "msearch_collection",
    "msearch_max_results",
    "msearch_mode",
    "msearch_min_confidence",
    "msearch_rescore",
    "context_window_tokens",
    "output_token_budget_short",
    "output_token_budget_medium",
    "output_token_budget_long",
    "min_prompt_chunks",
    "token_budget_safety_margin",
)
# Everything of the "sources" event that the stored "done" payload carries too.
_CACHED_SOURCES_FIELDS = (
    "original_question",
    "retrieval_query",
    "answer_question",
    "retrieval_query_was_rewritten",
    "retrieval_query_rewrite_attempted",
    "retrieval_query_rewrite_skip_reason",
    "used_chunks",
    "omitted_chunks",
    "baseline_chunks",
    "sources",
    "token_budget",
    "chunk_budget_warnings",
    "conversation_summary",
    "conversation_folded_message_count",
)


def _get_answer_cache() -> AnswerCache | None:
    global _answer_cache
    if not settings.answer_cache_enabled:
        return None
    with _answer_cache_lock:
        if _answer_cache is None:
            _answer_cache = AnswerCache(
                settings.answer_cache_path,
                ttl_seconds=settings.answer_cache_ttl_days * 86400,
                max_entries=settings.answer_cache_max_entries,
            )
    return _answer_cache


def _chat_cache_key_input(
    request: ChatRequest,
    placeholder_defs: dict,
    selections: dict[str, str],
    length: str,
    provider: str,
    model: str,
    base_url: str | None,
) -> dict[str, object]:
    """The key input with every value as the pipeline will use it.

    An omitted field and the default it stands for give the same key, so a
    request from scripts/warm_cache.py, which leaves most fields out, hits the
    entry of a browser request that sends the defaults explicitly.
    """

    budget = PromptBudgetConfig.from_settings(
        settings,
        context_window_tokens=request.context_window_tokens,
        output_token_budget_short=request.output_token_budget_short,
        output_token_budget_medium=request.output_token_budget_medium,
        output_token_budget_long=request.output_token_budget_long,
        min_prompt_chunks=request.min_prompt_chunks,
        token_budget_safety_margin=request.token_budget_safety_margin,
        conversation_summary_trigger_tokens=request.conversation_summary_trigger_tokens,
    )

    def resolved(value: object, default: object) -> object:
        return default if value is None else value

    return answer_cache_key_input(
        request,
        llm_provider=provider,
        model=model,
        llm_base_url=(base_url or "").rstrip("/"),
        wp_id=resolve_wp_id(request.wp_id),
        system_prompt=(request.system_prompt or "").strip() or default_system_prompt_template(),
        user_prompt_template=(request.user_prompt_template or "").strip() or default_user_prompt_template(),
        # The text each placeholder renders, not its def and selection: a
        # missing selection and its default render the same.
        placeholder_defs=None,
        selections=None,
        placeholder_values={
            name: substitute_value(definition, selections.get(name)) for name, definition in placeholder_defs.items()
        },
        output_length=length,
        reasoning_effort=(request.reasoning_effort or "").strip() or None,
        top_k=resolved(request.top_k, settings.top_k),
        retrieval_backend=request.retrieval_backend or settings.retrieval_backend,
        msearch_collection=request.msearch_collection or settings.msearch_collection,
        msearch_mode=request.msearch_mode or settings.msearch_mode,
        msearch_min_confidence=resolved(request.msearch_min_confidence, settings.msearch_min_confidence),
        msearch_rescore=resolved(request.msearch_rescore, settings.msearch_rescore),
        min_score=resolved(request.min_score, settings.min_score),
        min_relative_score=resolved(request.min_relative_score, settings.min_relative_score),
        rerank_enabled=resolved(request.rerank_enabled, settings.reranker_enabled),
        rerank_weight=resolved(request.rerank_weight, settings.reranker_weight),
        rerank_candidates=resolved(request.rerank_candidates, settings.reranker_candidates),
        context_window_tokens=budget.context_window_tokens,
        output_token_budget_short=budget.output_token_budget_short,
        output_token_budget_medium=budget.output_token_budget_medium,
        output_token_budget_long=budget.output_token_budget_long,
        min_prompt_chunks=budget.min_prompt_chunks,
        token_budget_safety_margin=budget.token_budget_safety_margin,
        conversation_summary_trigger_tokens=budget.conversation_summary_trigger_tokens,
        server=_answer_cache_server_settings(),
    )


def _answer_cache_server_settings() -> dict[str, object]:
    return {name: getattr(settings, name) for name in _ANSWER_CACHE_SETTINGS}


def _cached_answer(cache: AnswerCache, key: str) -> dict[str, object] | None:
    # A broken cache must not break the chat: it only costs a fresh answer.
    try:
        return cache.get(key)
    except Exception:
        logger.exception("Answer cache lookup failed")
        return None


def _store_answer(cache: AnswerCache, key: str, key_input: dict[str, object], response: dict[str, object], request: ChatRequest) -> None:
    # retrieved_chunks repeats used_chunks; the replay restores it.
    payload = {name: value for name, value in response.items() if name != "retrieved_chunks"}
    try:
        cache.put(key, key_input, payload, meta={"prompt_preset_id": request.prompt_preset_id})
    except Exception:
        logger.exception("Answer cache store failed")


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, http_request: Request) -> StreamingResponse:
    placeholder_defs, selections = _resolve_chat_placeholders(request)
    length = _output_budget_length(placeholder_defs, selections)
    context = request_context(http_request, settings.analytics_instance_id)
    initial_fields = _turn_fields(
        request,
        operation="chat",
        mode="streaming",
        provider=request.llm_provider,
        requested_model=request.model,
        base_url=request.llm_base_url,
        key_source="browser" if request.llm_api_key and request.llm_api_key.strip() else "none",
    )
    initial_fields["cache_hit"] = False
    # Resolved before the stream starts, because the cache key needs the
    # resolved model; an error is reported from inside the stream as before.
    resolved_llm: tuple[str, str, str | None, str | None] | None = None
    resolve_error: HTTPException | None = None
    try:
        resolved_llm = _resolve_llm_request(request)
    except HTTPException as exc:
        resolve_error = exc
    cache = _get_answer_cache() if resolved_llm is not None and answer_is_cacheable(request) else None
    cache_input: dict[str, object] | None = None
    cache_key: str | None = None
    cached: dict[str, object] | None = None
    if cache is not None:
        provider, model, _, base_url = resolved_llm
        cache_input = _chat_cache_key_input(request, placeholder_defs, selections, length, provider, model, base_url)
        cache_key = answer_cache_key(cache_input)
        if not request.bypass_cache:
            cached = _cached_answer(cache, cache_key)
    # Only an answer that costs an LLM call counts against the daily limit.
    quota_headers = {} if cached is not None else count_request()

    def cached_event_stream():
        started = time.perf_counter()
        resolved_provider, resolved_model, resolved_api_key, resolved_base_url = resolved_llm
        fields = {
            **initial_fields,
            "provider": resolved_provider,
            "requested_model": resolved_model,
            "endpoint_host": endpoint_host(resolved_base_url),
            "key_source": _key_source(request, resolved_api_key),
            "upstream_model": cached.get("upstream_model"),
            "cache_hit": True,
        }
        answer = str(cached.get("answer") or "")
        try:
            # The policy may have changed since the answer was stored.
            _enforce_msearch_collection_policy(
                request.wp_id, request.msearch_collection or settings.msearch_collection, resolved_base_url
            )
            _enforce_retrieval_backend_policy(request.wp_id, request.retrieval_backend)
            sources = {name: cached.get(name) for name in _CACHED_SOURCES_FIELDS}
            yield _sse_event(
                "sources",
                {
                    "question": request.question,
                    **sources,
                    "retrieved_chunks": cached.get("used_chunks"),
                    "cache_hit": True,
                    "cache_key": cache_key,
                },
            )
            if cached.get("reasoning"):
                yield _sse_event("reasoning", {"text": cached["reasoning"]})
            # Streamed at a steady pace rather than all at once, so it reads
            # like (and an avatar can speak it like) a generated answer.
            pieces, pause = replay_pieces(answer)
            for index, piece in enumerate(pieces):
                if index:
                    _replay_sleep(pause)
                yield _sse_event("token", {"text": piece})
            yield _sse_event(
                "done",
                {
                    **cached,
                    "retrieved_chunks": cached.get("used_chunks"),
                    "response_time_seconds": round(time.perf_counter() - started, 3),
                    "rerank_time_seconds": None,
                    "generation_time_seconds": None,
                    "cache_hit": True,
                    "cache_key": cache_key,
                },
            )
            analytics.event(
                "turn", context, **fields, status="ok",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                http_status=200, error_code=None,
                **text_lengths(answer, "answer"), answer_tokens_estimated=estimated_tokens(answer),
            )
        except HTTPException as exc:
            logger.info("Streaming chat rejected: %s", exc.detail)
            yield _sse_event("error", {"detail": exc.detail})
            analytics.event(
                "turn", context, **fields, status="error",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                http_status=200, error_code=analytics_error_code(exc, exc.status_code),
            )
        except GeneratorExit:
            analytics.event(
                "turn", context, **fields, status="cancelled",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                http_status=200, error_code="client_cancelled",
            )
            raise

    def event_stream():
        started = time.perf_counter()
        fields = dict(initial_fields)
        retrieval_ms = rerank_ms = prompt_prepare_ms = None
        preliminary_ms = final_sources_ms = None
        ttft_ms = token_stream_ms = None
        budget = None
        answer = ""
        try:
            if resolve_error is not None:
                raise resolve_error
            resolved_provider, resolved_model, resolved_api_key, resolved_base_url = resolved_llm
            key_source = _key_source(request, resolved_api_key)
            fields.update(
                provider=resolved_provider,
                requested_model=resolved_model,
                endpoint_host=endpoint_host(resolved_base_url),
                key_source=key_source,
            )
            _enforce_msearch_collection_policy(
                request.wp_id, request.msearch_collection or settings.msearch_collection, resolved_base_url
            )
            _enforce_retrieval_backend_policy(request.wp_id, request.retrieval_backend)
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
            preflight_question = (
                request.retrieval_query
                if request.use_retrieval_query_for_answer and request.retrieval_query is not None
                else request.question
            )
            if not request.use_retrieval_query_for_answer or request.retrieval_query is not None:
                pipeline.preflight_chat_prompt(
                    question=preflight_question,
                    length=length,
                    model=resolved_model,
                    budget_config=budget_config,
                    placeholder_defs=placeholder_defs,
                    selections=selections,
                    system_prompt=request.system_prompt,
                    user_prompt_template=request.user_prompt_template,
                )
            if request.retrieval_query is None:
                rewrite_attempted = pipeline.should_rewrite_query_for_retrieval(
                    request.question,
                    conversation_history=request.conversation_history,
                    enabled=request.rewrite_query_for_retrieval,
                    model=resolved_model,
                )
                rewrite_skip_reason = (
                    None
                    if rewrite_attempted
                    else pipeline.query_rewrite_skip_reason(
                        request.question,
                        conversation_history=request.conversation_history,
                        enabled=request.rewrite_query_for_retrieval,
                        model=resolved_model,
                    )
                )
                if rewrite_attempted:
                    yield _sse_event("status", {"phase": "query_rewrite"})
                with bind_context(context, provider=resolved_provider, key_source=key_source, purpose="query_rewrite"):
                    retrieval_query = pipeline.rewrite_query_for_retrieval(
                        request.question,
                        conversation_history=request.conversation_history,
                        conversation_summary=request.conversation_summary,
                        enabled=request.rewrite_query_for_retrieval,
                        model=resolved_model,
                        api_key=resolved_api_key,
                        base_url=resolved_base_url,
                    )
                yield _sse_event("status", {"phase": "retrieval"})
            else:
                rewrite_attempted = False
                rewrite_skip_reason = None
                retrieval_query = _clean_transformed_query(request.retrieval_query)
                if not retrieval_query:
                    raise HTTPException(status_code=400, detail="Vyhledávací dotaz nesmí být prázdný.")
            answer_question = (
                retrieval_query
                if request.use_retrieval_query_for_answer
                else request.question
            )
            retrieval_started = time.perf_counter()
            candidates = pipeline.retrieve_candidates(
                retrieval_query,
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
                msearch_rescore=request.msearch_rescore,
                rerank_enabled=request.rerank_enabled,
                rerank_weight=request.rerank_weight,
                rerank_candidates=request.rerank_candidates,
            )
            retrieval_ms = ms(time.perf_counter() - retrieval_started)
            baseline_payload = [_serialize_retrieved_chunk(chunk) for chunk in candidates.baseline]
            # When reranking is active, show the first-stage hits immediately so the
            # user is not staring at an empty panel while the cross-encoder runs;
            # the final "sources" event below replaces them with the reranked order.
            if candidates.rerank_active and candidates.baseline:
                preliminary_ms = ms(time.perf_counter() - started)
                yield _sse_event(
                    "preliminary_sources",
                    {
                        "question": request.question,
                        "original_question": request.question,
                        "retrieval_query": retrieval_query,
                        "answer_question": answer_question,
                        "retrieval_query_was_rewritten": retrieval_query != request.question,
                        "retrieval_query_rewrite_attempted": rewrite_attempted,
                        "retrieval_query_rewrite_skip_reason": rewrite_skip_reason,
                        "retrieved_chunks": baseline_payload,
                        "sources": [_serialize_source(chunk) for chunk in candidates.baseline],
                    },
                )
            retrieved: list = []
            rerank_seconds = 0.0
            for event in pipeline.apply_rerank_iter(retrieval_query, candidates):
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
            rerank_ms = ms(rerank_seconds) if candidates.rerank_active else None
            prompt_started = time.perf_counter()
            if pipeline.conversation_compaction_needed(
                request.conversation_history,
                model=resolved_model,
                length=length,
                budget_config=budget_config,
            ):
                yield _sse_event("status", {"phase": "conversation_compaction"})
            with bind_context(context, provider=resolved_provider, key_source=key_source, purpose="conversation_summary"):
                budget, conversation = pipeline.build_chat_prompt(
                    question=answer_question,
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
            prompt_prepare_ms = ms(time.perf_counter() - prompt_started)
            final_sources_ms = ms(time.perf_counter() - started)
            yield _sse_event(
                "sources",
                {
                    "question": request.question,
                    "original_question": request.question,
                    "retrieval_query": retrieval_query,
                    "answer_question": answer_question,
                    "retrieval_query_was_rewritten": retrieval_query != request.question,
                    "retrieval_query_rewrite_attempted": rewrite_attempted,
                    "retrieval_query_rewrite_skip_reason": rewrite_skip_reason,
                    "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                    "used_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                    "omitted_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.omitted_chunks],
                    "baseline_chunks": baseline_payload,
                    "sources": [_serialize_source(chunk) for chunk in budget.used_chunks],
                    "token_budget": budget.metadata(),
                    "chunk_budget_warnings": budget.warnings,
                    "conversation_summary": conversation.summary,
                    "conversation_folded_message_count": conversation.folded_message_count,
                    "cache_hit": False,
                    "cache_key": cache_key,
                },
            )
            answer_parts: list[str] = []
            generation_started = time.perf_counter()
            first_token_at = None
            with bind_context(context, provider=resolved_provider, key_source=key_source, purpose="answer"):
                stream = pipeline.llm.stream_generate(
                    budget.messages,
                    model=resolved_model,
                    api_key=resolved_api_key,
                    base_url=resolved_base_url,
                    reasoning=_reasoning_payload(resolved_model, resolved_provider, request.reasoning_effort),
                )
            # Starlette advances sync response iterators in a worker thread and
            # may resume each yield in a different copied Context.  The stream
            # captures the analytics context above, so do not keep a ContextVar
            # token open while yielding SSE events.
            for kind, text in stream:
                if kind == REASONING:
                    # A separate event, so the trace can be shown as it is
                    # written without ever being mistaken for the answer. Note
                    # that it deliberately does not start the TTFT clock: a
                    # reasoning model sends its whole trace first, and counting
                    # that as "time to first token" would report a model as
                    # faster the longer it thinks.
                    yield _sse_event("reasoning", {"text": text})
                    continue
                if first_token_at is None and text:
                    first_token_at = time.perf_counter()
                    ttft_ms = ms(first_token_at - generation_started)
                answer_parts.append(text)
                answer += text
                yield _sse_event("token", {"text": text})

            generation_seconds = time.perf_counter() - generation_started
            # Tokens went out raw so the client could render them as they
            # arrived; the stored/replayed answer is the cleaned one.
            answer = strip_model_source_list(answer)
            # The whole trace, for history and for a client that missed the
            # deltas (a reconnect, or one that does not handle the event).
            reasoning_text = (getattr(stream, "reasoning_text", "") or "").strip()
            if first_token_at is not None:
                token_stream_ms = ms(time.perf_counter() - first_token_at)
            elapsed = time.perf_counter() - started
            upstream_model = getattr(stream, "upstream_model", None) or resolved_model
            response = {
                "answer": answer,
                "reasoning": reasoning_text,
                "original_question": request.question,
                "retrieval_query": retrieval_query,
                "answer_question": answer_question,
                "retrieval_query_was_rewritten": retrieval_query != request.question,
                "retrieval_query_rewrite_attempted": rewrite_attempted,
                "retrieval_query_rewrite_skip_reason": rewrite_skip_reason,
                "sources": [_serialize_source(chunk) for chunk in budget.used_chunks],
                "retrieved_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                "used_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.used_chunks],
                "omitted_chunks": [_serialize_retrieved_chunk(chunk) for chunk in budget.omitted_chunks],
                "baseline_chunks": baseline_payload,
                "token_budget": budget.metadata(),
                "chunk_budget_warnings": budget.warnings,
                "conversation_summary": conversation.summary,
                "conversation_folded_message_count": conversation.folded_message_count,
                "model": resolved_model,
                "upstream_model": upstream_model,
                "response_time_seconds": round(elapsed, 3),
                "rerank_time_seconds": round(rerank_seconds, 3) if candidates.rerank_active else None,
                "generation_time_seconds": round(generation_seconds, 3),
                "cache_hit": False,
                "cache_key": cache_key,
            }
            logger.info(
                "Streamed answer length=%s model=%s response_time=%.2fs rerank=%.2fs generation=%.2fs answer_chars=%s",
                length,
                resolved_model,
                elapsed,
                rerank_seconds,
                generation_seconds,
                len(answer),
            )
            # Only a finished answer: an aborted or failed stream never gets here.
            # Stored before "done", so the entry exists once a client sees it
            # (scripts/warm_cache.py pins it then).
            if cache_key is not None and answer.strip():
                _store_answer(cache, cache_key, cache_input, response, request)
            yield _sse_event("done", response)
            event_fields = {
                **fields,
                "upstream_model": upstream_model,
                "retrieval_query_was_rewritten": retrieval_query != request.question,
                "retrieval_query_rewrite_attempted": rewrite_attempted,
                "retrieval_query_rewrite_skip_reason": rewrite_skip_reason,
            }
            analytics.event(
                "turn",
                context,
                **event_fields,
                status="ok",
                duration_ms=ms(time.perf_counter() - started),
                total_ms=ms(time.perf_counter() - started),
                retrieval_ms=retrieval_ms,
                rerank_ms=rerank_ms,
                prompt_prepare_ms=prompt_prepare_ms,
                time_to_first_token_ms=ttft_ms,
                token_stream_ms=token_stream_ms,
                generation_ms=None,
                time_to_preliminary_sources_ms=preliminary_ms,
                time_to_final_sources_ms=final_sources_ms,
                http_status=200,
                error_code=None,
                **text_lengths(answer, "answer"),
                answer_tokens_estimated=estimated_tokens(answer),
                warning_count=len(budget.warnings),
                **budget.metadata(),
            )
        except PromptBudgetError as exc:
            logger.info("Streaming chat rejected by token budget: %s", exc)
            yield _sse_event("error", {"detail": exc.to_payload()})
            analytics.event(
                "turn", context, **fields, status="error",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, prompt_prepare_ms=prompt_prepare_ms,
                http_status=200, error_code="token_budget",
            )
        except HTTPException as exc:
            logger.info("Streaming chat rejected: %s", exc.detail)
            yield _sse_event("error", {"detail": exc.detail})
            analytics.event(
                "turn", context, **fields, status="error",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, prompt_prepare_ms=prompt_prepare_ms,
                time_to_first_token_ms=ttft_ms, token_stream_ms=token_stream_ms,
                http_status=200, error_code=analytics_error_code(exc, exc.status_code),
                **text_lengths(answer, "answer"), answer_tokens_estimated=estimated_tokens(answer),
            )
        except GeneratorExit:
            analytics.event(
                "turn", context, **fields, status="cancelled",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, prompt_prepare_ms=prompt_prepare_ms,
                time_to_first_token_ms=ttft_ms, token_stream_ms=token_stream_ms,
                http_status=200, error_code="client_cancelled", **text_lengths(answer, "answer"),
                answer_tokens_estimated=estimated_tokens(answer),
            )
            raise
        except Exception as exc:
            logger.exception("Streaming chat failed")
            yield _sse_event("error", {"detail": str(exc)})
            analytics.event(
                "turn", context, **fields, status="error",
                duration_ms=ms(time.perf_counter() - started), total_ms=ms(time.perf_counter() - started),
                retrieval_ms=retrieval_ms, rerank_ms=rerank_ms, prompt_prepare_ms=prompt_prepare_ms,
                time_to_first_token_ms=ttft_ms, token_stream_ms=token_stream_ms,
                http_status=200, error_code=analytics_error_code(exc), **text_lengths(answer, "answer"),
                answer_tokens_estimated=estimated_tokens(answer),
            )

    return StreamingResponse(
        cached_event_stream() if cached is not None else event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            **quota_headers,
        },
    )


# Admin Cache dialog -----------------------------------------------------------
# Admin access as elsewhere: a logged-in admin account, or the shared admin
# password, sent in a header so it stays out of URLs and access logs.

# Rows the list returns; the rest is counted but left out.
ANSWER_CACHE_LIST_LIMIT = 500


def _admin_answer_cache(admin_password: str | None) -> AnswerCache:
    if not _admin_authorized(admin_password):
        raise HTTPException(status_code=403, detail="Správa cache vyžaduje admin přístup.")
    cache = _get_answer_cache()
    if cache is None:
        raise HTTPException(status_code=404, detail="Cache odpovědí je vypnutá (ANSWER_CACHE_ENABLED).")
    return cache


def _answer_cache_entries(cache: AnswerCache) -> list[dict[str, object]]:
    """The live entries, each marked stale when it was made for another server
    configuration or cache version: an identical request now has another key,
    so such an entry is never hit again."""

    # Compared as stored, so Path and similar values match their JSON form.
    server = json.loads(json.dumps(_answer_cache_server_settings(), ensure_ascii=False, default=str))
    names = {
        **{prompt.id: prompt.name for wp in WP_CONFIGS for prompt in wp.builtin_prompts},
        **{preset["id"]: preset.get("name") for preset in load_prompt_presets(settings.prompt_presets_path)},
    }
    entries = cache.entries()
    for entry in entries:
        entry["stale"] = entry.pop("cache_version") != ANSWER_CACHE_VERSION or entry.pop("server") != server
        entry["prompt_preset_name"] = names.get(entry["prompt_preset_id"])
    return entries


def _matches(entry: dict[str, object], selection: AnswerCacheFilter) -> bool:
    query = (selection.q or "").strip().casefold()
    return (
        (not selection.wp_id or entry["wp_id"] == selection.wp_id)
        and (selection.pinned is None or entry["pinned"] == selection.pinned)
        and (selection.stale is None or entry["stale"] == selection.stale)
        and (not query or query in str(entry["question"]).casefold())
    )


@app.get("/answer-cache")
def list_answer_cache(
    wp_id: str | None = None,
    pinned: bool | None = None,
    stale: bool | None = None,
    q: str | None = None,
    x_admin_password: str | None = Header(default=None),
) -> dict[str, object]:
    cache = _admin_answer_cache(x_admin_password)
    entries = _answer_cache_entries(cache)
    selection = AnswerCacheFilter(wp_id=wp_id, pinned=pinned, stale=stale, q=q)
    matching = [entry for entry in entries if _matches(entry, selection)]
    return {
        "stats": {
            "entries": len(entries),
            "pinned": sum(entry["pinned"] for entry in entries),
            "stale": sum(entry["stale"] for entry in entries),
            "hits": sum(entry["hit_count"] for entry in entries),
            "size_bytes": cache.size_bytes(),
            "ttl_days": settings.answer_cache_ttl_days,
            "max_entries": settings.answer_cache_max_entries,
        },
        "matching": len(matching),
        "entries": matching[:ANSWER_CACHE_LIST_LIMIT],
    }


@app.get("/answer-cache/{key}")
def get_answer_cache_entry(key: str, x_admin_password: str | None = Header(default=None)) -> dict[str, object]:
    stored = _admin_answer_cache(x_admin_password).peek(key)
    if stored is None:
        raise HTTPException(status_code=404, detail="Záznam v cache neexistuje.")
    key_input, payload = stored
    # Credentials never reach the key input; the prompts are long but are the
    # point of a preview.
    return {"key": key, "settings": key_input, "answer": payload.get("answer", ""), "sources": payload.get("sources", [])}


@app.put("/answer-cache/{key}/pin")
def pin_answer_cache_entry(
    key: str,
    body: AnswerCachePinRequest,
    x_admin_password: str | None = Header(default=None),
) -> dict[str, object]:
    cache = _admin_answer_cache(x_admin_password)
    if not (cache.pin(key) if body.pinned else cache.unpin(key)):
        raise HTTPException(status_code=404, detail="Záznam v cache neexistuje.")
    return {"key": key, "pinned": body.pinned}


@app.delete("/answer-cache/{key}", status_code=204)
def delete_answer_cache_entry(key: str, x_admin_password: str | None = Header(default=None)) -> Response:
    if not _admin_answer_cache(x_admin_password).delete(key):
        raise HTTPException(status_code=404, detail="Záznam v cache neexistuje.")
    return Response(status_code=204)


@app.post("/answer-cache/delete")
def delete_answer_cache_entries(
    selection: AnswerCacheFilter,
    x_admin_password: str | None = Header(default=None),
) -> dict[str, object]:
    """Delete every entry the filter matches, beyond the listed ones too."""

    cache = _admin_answer_cache(x_admin_password)
    keys = [entry["key"] for entry in _answer_cache_entries(cache) if _matches(entry, selection)]
    return {"deleted": cache.delete_many(keys)}


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
        "source_citation": metadata.get("source_citation"),
        "score": float(chunk.get("score") or 0.0),
    }
