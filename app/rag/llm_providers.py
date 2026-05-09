from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import logging
import re
from typing import Any

import httpx

from app.config import load_env_values


logger = logging.getLogger(__name__)

_PROVIDER_ENV_PATTERN = re.compile(
    r"^LLM_PROVIDER_([A-Z0-9_]+)_(NAME|BASE_URL|API_KEY|DEFAULT_MODEL|PUBLIC_MODELS|MODELS|MODELS_URL|DISCOVER_MODELS|SUPPORTS_STREAMING|API_KEY_LABEL)$"
)
_EXCLUDED_MODEL_PATTERNS = ("rag-*", "openwebuidocs")


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


def _is_excluded_model_name(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return any(fnmatchcase(normalized, pattern) for pattern in _EXCLUDED_MODEL_PATTERNS)


def _filter_model_names(model_names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for name in model_names if name and not _is_excluded_model_name(name)))


def _discover_models(base_url: str, api_key: str, timeout: float = 20.0, models_url: str | None = None) -> list[str]:
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
        return list(_filter_model_names(names))
    except Exception as exc:
        logger.debug("Could not discover models from %s: %s", resolved_url, exc)
        return []


def load_provider_configs(env: dict[str, str] | None = None) -> list[LLMProviderConfig]:
    resolved_env = env or load_env_values()
    provider_ids = _discover_provider_ids(resolved_env)
    providers: list[LLMProviderConfig] = []

    for provider_id in provider_ids:
        label = _env_value(resolved_env, provider_id, "NAME", provider_id)
        base_url = _env_value(resolved_env, provider_id, "BASE_URL")
        api_key = _env_value(resolved_env, provider_id, "API_KEY")
        default_model = _env_value(resolved_env, provider_id, "DEFAULT_MODEL")
        public_models = _filter_model_names(_split_csv(_env_value(resolved_env, provider_id, "PUBLIC_MODELS")))
        static_models = _filter_model_names(_split_csv(_env_value(resolved_env, provider_id, "MODELS")))
        models_url = _env_value(resolved_env, provider_id, "MODELS_URL") or None
        discover_models = _parse_bool(resolved_env.get(_env_key(provider_id, "DISCOVER_MODELS")), default=False)
        supports_streaming = _parse_bool(
            resolved_env.get(_env_key(provider_id, "SUPPORTS_STREAMING")),
            default=True,
        )
        api_key_label = _env_value(resolved_env, provider_id, "API_KEY_LABEL") or "API key"

        if discover_models and base_url:
            discovered_models = tuple(_discover_models(base_url, api_key, models_url=models_url))
        else:
            discovered_models = ()

        model_presets = discovered_models or static_models
        if default_model and not _is_excluded_model_name(default_model) and default_model not in model_presets:
            model_presets = (default_model, *model_presets)
        if not public_models and default_model and not _is_excluded_model_name(default_model):
            public_models = (default_model,)

        providers.append(
            LLMProviderConfig(
                id=provider_id,
                label=label,
                base_url=base_url,
                api_key=api_key,
                default_model=default_model or (model_presets[0] if model_presets else ""),
                public_models=public_models,
                model_presets=tuple(dict.fromkeys(model_presets)),
                supports_streaming=supports_streaming,
                api_key_label=api_key_label,
                discover_models=discover_models,
                models_url=models_url,
            )
        )

    return providers


def available_llm_providers(env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    return [provider.to_dict() for provider in load_provider_configs(env)]


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
