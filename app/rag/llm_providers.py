from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import logging
import re
import time
from typing import Any

import httpx

from app.config import load_env_values
from app.rag.model_metadata import filter_model_context_windows


logger = logging.getLogger(__name__)

_PROVIDER_ENV_PATTERN = re.compile(
    r"^LLM_PROVIDER_([A-Z0-9_]+)_(NAME|BASE_URL|API_KEY|DEFAULT_MODEL|PUBLIC_MODELS|MODELS|MODELS_URL|MODEL_INFO_URL|DISCOVER_MODELS|SUPPORTS_STREAMING|API_KEY_LABEL|MODELS_CACHE_TTL_SECONDS)$"
)
_EXCLUDED_MODEL_PATTERNS = (
    "rag-*",
    "openwebdocs",
    "openwebuidocs",
    "llm6-2xrtx5000.gemma3:12b-it-qat",
)
_DEFAULT_MODELS_CACHE_TTL_SECONDS = 3600.0
_PUBLIC_ALL_MODELS = "*"


@dataclass(slots=True)
class ModelDiscoveryCacheEntry:
    models: tuple[str, ...]
    refreshed_at: float
    error: str = ""


@dataclass(slots=True)
class ModelContextDiscoveryCacheEntry:
    context_windows: dict[str, int]
    refreshed_at: float
    error: str = ""


_model_discovery_cache: dict[str, ModelDiscoveryCacheEntry] = {}
_model_context_discovery_cache: dict[str, ModelContextDiscoveryCacheEntry] = {}


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        parsed = float(value.strip())
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def _normalize_provider_id(value: str | None) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", (value or "").strip().lower()).strip("_")


def _env_key(provider_id: str, suffix: str) -> str:
    return f"LLM_PROVIDER_{provider_id.upper()}_{suffix}"


def _env_value(env: dict[str, str], provider_id: str, suffix: str, default: str = "") -> str:
    return env.get(_env_key(provider_id, suffix), default).strip()


@dataclass(frozen=True, slots=True)
class LLMProviderConfig:
    id: str
    label: str
    base_url: str
    api_key: str
    default_model: str
    public_models: tuple[str, ...]
    model_presets: tuple[str, ...]
    supports_streaming: bool
    api_key_label: str
    discover_models: bool
    models_url: str | None = None
    model_context_windows: dict[str, int] | None = None
    default_context_window_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "base_url": self.base_url,
            "api_key_label": self.api_key_label,
            "default_model": self.default_model,
            "public_models": list(self.public_models),
            "model_presets": list(self.model_presets),
            "supports_streaming": self.supports_streaming,
            "discover_models": self.discover_models,
            "models_url": self.models_url,
            "model_context_windows": dict(self.model_context_windows or {}),
            "default_context_window_tokens": self.default_context_window_tokens,
        }


def _discover_provider_ids(env: dict[str, str]) -> list[str]:
    explicit_ids = _split_csv(env.get("LLM_PROVIDERS"))
    if explicit_ids:
        return [_normalize_provider_id(provider_id) for provider_id in explicit_ids if _normalize_provider_id(provider_id)]

    discovered: set[str] = set()
    for key in env:
        match = _PROVIDER_ENV_PATTERN.match(key)
        if match:
            provider_id = _normalize_provider_id(match.group(1))
            if provider_id:
                discovered.add(provider_id)
    return sorted(discovered)


def _extract_model_names(payload: Any) -> list[str]:
    names: list[str] = []
    if isinstance(payload, dict):
        for key in ("models", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                names.extend(_extract_model_names(value))
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                name = item.strip()
                if name:
                    names.append(name)
                continue
            if isinstance(item, dict):
                for key in ("id", "name", "model", "slug"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        names.append(value.strip())
                        break
    return names


def _model_name_from_record(record: dict[str, Any]) -> str:
    for key in ("id", "name", "model", "model_name", "model_id", "base_model_id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _context_size_from_model_info(record: dict[str, Any]) -> int | None:
    model_info = record.get("model_info")
    if isinstance(model_info, dict):
        raw_tokens = model_info.get("context_size")
        try:
            tokens = int(raw_tokens)
        except (TypeError, ValueError):
            return None
        if tokens >= 1024:
            return tokens
    return None


def _extract_model_context_windows(payload: Any, model_names: list[str] | tuple[str, ...]) -> dict[str, int]:
    windows: dict[str, int] = {}
    known_models = tuple(dict.fromkeys(model for model in model_names if model))
    known_model_set = set(known_models)

    def visit(value: Any, inherited_name: str = "") -> None:
        if isinstance(value, list):
            for item in value:
                visit(item, inherited_name)
            return
        if not isinstance(value, dict):
            return

        name = _model_name_from_record(value) or inherited_name
        context_size = _context_size_from_model_info(value)
        if context_size is not None:
            if name and name in known_model_set:
                windows[name] = context_size
            elif not name and len(known_models) == 1:
                windows[known_models[0]] = context_size

        for key in ("data", "models", "items"):
            child = value.get(key)
            if isinstance(child, (list, dict)):
                visit(child, name)

    visit(payload)
    return windows


def _is_excluded_model_name(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return any(fnmatchcase(normalized, pattern) for pattern in _EXCLUDED_MODEL_PATTERNS)


def _filter_model_names(model_names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for name in model_names if name and not _is_excluded_model_name(name)))


def _discover_models(base_url: str, api_key: str, timeout: float = 20.0, models_url: str | None = None) -> tuple[str, ...]:
    resolved_url = (models_url or f"{base_url.rstrip('/')}/models").rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "rag-avatar",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.get(resolved_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        names = _extract_model_names(response.json())
        return _filter_model_names(names)
    except Exception as exc:
        raise RuntimeError(f"Could not discover models from {resolved_url}: {exc}") from exc


def _discover_model_context_windows(
    base_url: str,
    api_key: str,
    model_names: list[str] | tuple[str, ...],
    timeout: float = 20.0,
    model_info_url: str | None = None,
) -> dict[str, int]:
    resolved_url = (model_info_url or f"{base_url.rstrip('/')}/model/info").rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "rag-avatar",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.get(resolved_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return _extract_model_context_windows(response.json(), model_names)
    except Exception as exc:
        raise RuntimeError(f"Could not discover model context windows from {resolved_url}: {exc}") from exc


def _discovery_cache_key(provider_id: str, base_url: str, endpoint_url: str | None) -> str:
    return "|".join([provider_id, base_url.strip().rstrip("/"), (endpoint_url or "").strip().rstrip("/")])


def _models_cache_ttl_seconds(env: dict[str, str], provider_id: str) -> float:
    return _parse_float(
        env.get(_env_key(provider_id, "MODELS_CACHE_TTL_SECONDS")),
        _parse_float(env.get("LLM_MODELS_CACHE_TTL_SECONDS"), _DEFAULT_MODELS_CACHE_TTL_SECONDS),
    )


def _discover_models_cached(
    provider_id: str,
    base_url: str,
    api_key: str,
    models_url: str | None,
    ttl_seconds: float,
    force_refresh: bool,
) -> ModelDiscoveryCacheEntry:
    cache_key = _discovery_cache_key(provider_id, base_url, models_url)
    cached = _model_discovery_cache.get(cache_key)
    now = time.time()
    if cached and not force_refresh and now - cached.refreshed_at < ttl_seconds:
        return cached

    try:
        models = _discover_models(base_url, api_key, models_url=models_url)
        entry = ModelDiscoveryCacheEntry(models=models, refreshed_at=now)
        _model_discovery_cache[cache_key] = entry
        return entry
    except RuntimeError as exc:
        logger.debug("%s", exc)
        if cached:
            return ModelDiscoveryCacheEntry(models=cached.models, refreshed_at=cached.refreshed_at, error=str(exc))
        return ModelDiscoveryCacheEntry(models=(), refreshed_at=now, error=str(exc))


def _discover_model_context_windows_cached(
    provider_id: str,
    base_url: str,
    api_key: str,
    model_names: list[str] | tuple[str, ...],
    model_info_url: str | None,
    ttl_seconds: float,
    force_refresh: bool,
) -> ModelContextDiscoveryCacheEntry:
    cache_key = _discovery_cache_key(provider_id, base_url, model_info_url)
    cached = _model_context_discovery_cache.get(cache_key)
    now = time.time()
    if cached and not force_refresh and now - cached.refreshed_at < ttl_seconds:
        return cached

    try:
        context_windows = _discover_model_context_windows(
            base_url,
            api_key,
            model_names,
            model_info_url=model_info_url,
        )
        entry = ModelContextDiscoveryCacheEntry(context_windows=context_windows, refreshed_at=now)
        _model_context_discovery_cache[cache_key] = entry
        return entry
    except RuntimeError as exc:
        logger.debug("%s", exc)
        if cached:
            return ModelContextDiscoveryCacheEntry(
                context_windows=cached.context_windows,
                refreshed_at=cached.refreshed_at,
                error=str(exc),
            )
        return ModelContextDiscoveryCacheEntry(context_windows={}, refreshed_at=now, error=str(exc))


def clear_model_discovery_cache() -> None:
    _model_discovery_cache.clear()
    _model_context_discovery_cache.clear()


def _supports_model_info_context_discovery(provider_id: str, label: str, base_url: str, model_info_url: str | None) -> bool:
    if model_info_url:
        return True
    provider_keys = {_normalize_provider_id(provider_id), _normalize_provider_id(label)}
    base_url_lower = base_url.lower()
    return (
        "einfra" in provider_keys
        or "e_infra" in provider_keys
        or "chat.ai.e-infra.cz" in base_url_lower
        or "llm.ai.e-infra.cz" in base_url_lower
    )


def _provider_context_window_default(
    provider_context_window_defaults: dict[str, int] | None,
    provider_id: str,
    label: str,
) -> int | None:
    defaults = provider_context_window_defaults or {}
    for key in (provider_id, label, _normalize_provider_id(provider_id), _normalize_provider_id(label)):
        tokens = defaults.get(key)
        if tokens:
            return tokens
    normalized_defaults = {_normalize_provider_id(key): value for key, value in defaults.items()}
    return normalized_defaults.get(_normalize_provider_id(provider_id)) or normalized_defaults.get(_normalize_provider_id(label))


def load_provider_configs(
    env: dict[str, str] | None = None,
    force_model_refresh: bool = False,
    model_context_windows: dict[str, int] | None = None,
    provider_context_window_defaults: dict[str, int] | None = None,
) -> list[LLMProviderConfig]:
    resolved_env = env or load_env_values()
    provider_ids = _discover_provider_ids(resolved_env)
    providers: list[LLMProviderConfig] = []

    for provider_id in provider_ids:
        label = _env_value(resolved_env, provider_id, "NAME", provider_id)
        base_url = _env_value(resolved_env, provider_id, "BASE_URL")
        api_key = _env_value(resolved_env, provider_id, "API_KEY")
        default_model = _env_value(resolved_env, provider_id, "DEFAULT_MODEL")
        public_models_raw = _env_value(resolved_env, provider_id, "PUBLIC_MODELS")
        public_all_models = public_models_raw == _PUBLIC_ALL_MODELS
        public_models = _filter_model_names(_split_csv(public_models_raw)) if not public_all_models else ()
        static_models = _filter_model_names(_split_csv(_env_value(resolved_env, provider_id, "MODELS")))
        models_url = _env_value(resolved_env, provider_id, "MODELS_URL") or None
        model_info_url = _env_value(resolved_env, provider_id, "MODEL_INFO_URL") or None
        discover_models = _parse_bool(resolved_env.get(_env_key(provider_id, "DISCOVER_MODELS")), default=False)
        cache_ttl_seconds = _models_cache_ttl_seconds(resolved_env, provider_id)
        supports_streaming = _parse_bool(
            resolved_env.get(_env_key(provider_id, "SUPPORTS_STREAMING")),
            default=True,
        )
        api_key_label = _env_value(resolved_env, provider_id, "API_KEY_LABEL") or "API key"

        if discover_models and base_url:
            discovery_entry = _discover_models_cached(
                provider_id,
                base_url,
                api_key,
                models_url,
                cache_ttl_seconds,
                force_model_refresh,
            )
            discovered_models = discovery_entry.models
        else:
            discovered_models = ()

        model_presets = discovered_models or static_models
        if (
            not discovered_models
            and default_model
            and not _is_excluded_model_name(default_model)
            and default_model not in model_presets
        ):
            model_presets = (default_model, *model_presets)
        if public_all_models:
            public_models = model_presets
        elif not public_models and default_model and not _is_excluded_model_name(default_model):
            public_models = (default_model,)
        else:
            public_models = tuple(model for model in public_models if model in model_presets)
        resolved_default_model = default_model if default_model in model_presets else (model_presets[0] if model_presets else "")
        resolved_model_presets = tuple(dict.fromkeys(model_presets))
        default_context_window_tokens = _provider_context_window_default(
            provider_context_window_defaults,
            provider_id,
            label,
        )
        resolved_model_context_windows = filter_model_context_windows(model_context_windows, resolved_model_presets)
        if base_url and resolved_model_presets and _supports_model_info_context_discovery(
            provider_id,
            label,
            base_url,
            model_info_url,
        ):
            context_discovery_entry = _discover_model_context_windows_cached(
                provider_id,
                base_url,
                api_key,
                resolved_model_presets,
                model_info_url,
                cache_ttl_seconds,
                force_model_refresh,
            )
            resolved_model_context_windows.update(context_discovery_entry.context_windows)
        if default_context_window_tokens:
            resolved_model_context_windows = {
                model: resolved_model_context_windows.get(model, default_context_window_tokens)
                for model in resolved_model_presets
            }

        providers.append(
            LLMProviderConfig(
                id=provider_id,
                label=label,
                base_url=base_url,
                api_key=api_key,
                default_model=resolved_default_model,
                public_models=public_models,
                model_presets=resolved_model_presets,
                supports_streaming=supports_streaming,
                api_key_label=api_key_label,
                discover_models=discover_models,
                models_url=models_url,
                model_context_windows=resolved_model_context_windows,
                default_context_window_tokens=default_context_window_tokens,
            )
        )

    return providers


def available_llm_providers(
    env: dict[str, str] | None = None,
    force_model_refresh: bool = False,
    model_context_windows: dict[str, int] | None = None,
    provider_context_window_defaults: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    return [
        provider.to_dict()
        for provider in load_provider_configs(
            env,
            force_model_refresh=force_model_refresh,
            model_context_windows=model_context_windows,
            provider_context_window_defaults=provider_context_window_defaults,
        )
    ]


def resolve_llm_provider(
    provider_id: str | None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> str:
    provider_list = providers or load_provider_configs()
    normalized_id = _normalize_provider_id(provider_id)
    if normalized_id:
        for provider in provider_list:
            if _normalize_provider_id(str(provider["id"] if isinstance(provider, dict) else provider.id)) == normalized_id:
                return normalized_id

    resolved_base_url = (base_url or "").strip().rstrip("/")
    if resolved_base_url:
        for provider in provider_list:
            provider_base_url = (provider["base_url"] if isinstance(provider, dict) else provider.base_url).strip().rstrip("/")
            if provider_base_url and provider_base_url == resolved_base_url:
                return _normalize_provider_id(str(provider["id"] if isinstance(provider, dict) else provider.id))

    if provider_list:
        first = provider_list[0]
        return _normalize_provider_id(str(first["id"] if isinstance(first, dict) else first.id))
    raise RuntimeError("No LLM providers are configured.")


def _provider_record(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> LLMProviderConfig | dict[str, Any]:
    provider_list = providers or load_provider_configs()
    resolved_id = resolve_llm_provider(provider_id, provider_list, base_url)
    for provider in provider_list:
        provider_key = provider["id"] if isinstance(provider, dict) else provider.id
        if _normalize_provider_id(str(provider_key)) == resolved_id:
            return provider
    raise RuntimeError(f"LLM provider '{resolved_id}' was not found.")


def provider_preset(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    provider = _provider_record(provider_id, providers, base_url)
    return provider if isinstance(provider, dict) else provider.to_dict()


def provider_models(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> list[str]:
    return list(provider_preset(provider_id, providers, base_url)["model_presets"])


def provider_default_model(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> str:
    return str(provider_preset(provider_id, providers, base_url)["default_model"])


def provider_public_models(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> list[str]:
    return list(provider_preset(provider_id, providers, base_url)["public_models"])


def provider_api_key(
    provider_id: str | None = None,
    providers: list[LLMProviderConfig] | list[dict[str, Any]] | None = None,
    base_url: str | None = None,
) -> str:
    provider = _provider_record(provider_id, providers, base_url)
    if isinstance(provider, LLMProviderConfig):
        return provider.api_key

    api_key = str(provider.get("api_key") or "")
    if api_key:
        return api_key

    # Public provider dicts intentionally omit secrets. Fall back to a fresh
    # private config lookup so backend calls can still use server-side keys.
    private_provider = _provider_record(provider_id, load_provider_configs(), base_url)
    return private_provider.api_key if isinstance(private_provider, LLMProviderConfig) else str(private_provider.get("api_key") or "")
