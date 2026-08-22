from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


def _parse_context_window_map(payload: object, path: Path, label: str) -> dict[str, int]:
    if not isinstance(payload, dict):
        logger.warning("Ignoring %s from %s: expected a JSON object.", label, path)
        return {}

    windows: dict[str, int] = {}
    for raw_name, raw_tokens in payload.items():
        name = str(raw_name).strip()
        if not name:
            continue
        try:
            tokens = int(raw_tokens)
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid context window for %s %r in %s.", label, name, path)
            continue
        if tokens < 1024:
            logger.warning("Ignoring too-small context window for %s %r in %s.", label, name, path)
            continue
        windows[name] = tokens
    return windows


def load_model_context_metadata(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """Load known model and provider-default context-window sizes."""
    if not path.exists():
        return {}, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load model context windows from %s: %s", path, exc)
        return {}, {}
    if not isinstance(payload, dict):
        logger.warning("Ignoring model context windows from %s: expected a JSON object.", path)
        return {}, {}

    if "models" in payload or "provider_defaults" in payload:
        return (
            _parse_context_window_map(payload.get("models", {}), path, "model"),
            _parse_context_window_map(payload.get("provider_defaults", {}), path, "provider"),
        )
    return _parse_context_window_map(payload, path, "model"), {}


def load_model_context_windows(path: Path) -> dict[str, int]:
    return load_model_context_metadata(path)[0]


def load_provider_context_window_defaults(path: Path) -> dict[str, int]:
    return load_model_context_metadata(path)[1]


def filter_model_context_windows(
    model_context_windows: dict[str, int] | None,
    model_names: list[str] | tuple[str, ...],
) -> dict[str, int]:
    known_windows = model_context_windows or {}
    return {model: known_windows[model] for model in model_names if model in known_windows}


@dataclass(frozen=True, slots=True)
class ReasoningSupport:
    """What a model accepts for reasoning, declared as data rather than in code.

    Providers disagree on both the request parameter and the effort vocabulary,
    and there is no reliable way to discover either. Rather than hardcode
    per-provider rules, `data/model_reasoning.json` states, per model or per
    provider, which parameter to send and which literal effort values are valid.
    Nothing is sent for a model that declares nothing, which is the old
    behaviour.
    """

    # Request field: "reasoning" sends {"reasoning": {"effort": ...}},
    # "reasoning_effort" sends {"reasoning_effort": ...}.
    param: str
    # Literal values the provider accepts, in the order to show them.
    efforts: tuple[str, ...]
    # What to send when the user has not chosen: usually the cheapest option.
    default: str | None = None
    # True when the model reasons whether or not it is asked to.
    mandatory: bool = False

    def payload(self, effort: str | None) -> dict[str, object]:
        """The request fragment for one effort, or {} when nothing should be sent."""
        chosen = (effort or self.default or "").strip()
        if not chosen or chosen not in self.efforts:
            return {}
        if self.param == "reasoning":
            return {"reasoning": {"effort": chosen}}
        return {self.param: chosen}

    def as_dict(self) -> dict[str, object]:
        return {
            "param": self.param,
            "efforts": list(self.efforts),
            "default": self.default,
            "mandatory": self.mandatory,
        }


VALID_REASONING_PARAMS = ("reasoning", "reasoning_effort")


def _parse_reasoning_entry(payload: object, path: Path, name: str) -> ReasoningSupport | None:
    if not isinstance(payload, dict):
        logger.warning("Ignoring reasoning metadata for %r in %s: expected a JSON object.", name, path)
        return None
    param = str(payload.get("param") or "reasoning_effort").strip()
    if param not in VALID_REASONING_PARAMS:
        logger.warning("Ignoring reasoning metadata for %r in %s: unknown param %r.", name, path, param)
        return None
    raw_efforts = payload.get("efforts")
    if not isinstance(raw_efforts, list) or not raw_efforts:
        logger.warning("Ignoring reasoning metadata for %r in %s: 'efforts' must be a non-empty list.", name, path)
        return None
    efforts = tuple(str(effort).strip() for effort in raw_efforts if str(effort).strip())
    if not efforts:
        logger.warning("Ignoring reasoning metadata for %r in %s: no usable efforts.", name, path)
        return None
    raw_default = payload.get("default")
    default = str(raw_default).strip() if raw_default is not None else None
    if default and default not in efforts:
        logger.warning("Ignoring default effort %r for %r in %s: not among 'efforts'.", default, name, path)
        default = None
    return ReasoningSupport(
        param=param,
        efforts=efforts,
        default=default,
        mandatory=bool(payload.get("mandatory")),
    )


def _parse_reasoning_map(payload: object, path: Path, label: str) -> dict[str, ReasoningSupport]:
    if not isinstance(payload, dict):
        logger.warning("Ignoring %s reasoning metadata from %s: expected a JSON object.", label, path)
        return {}
    parsed: dict[str, ReasoningSupport] = {}
    for raw_name, entry in payload.items():
        name = str(raw_name).strip()
        if not name:
            continue
        support = _parse_reasoning_entry(entry, path, name)
        if support is not None:
            parsed[name] = support
    return parsed


def load_model_reasoning_metadata(
    path: Path,
) -> tuple[dict[str, ReasoningSupport], dict[str, ReasoningSupport]]:
    """Load per-model and per-provider reasoning support. Missing file is fine."""
    if not path.exists():
        return {}, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load model reasoning metadata from %s: %s", path, exc)
        return {}, {}
    if not isinstance(payload, dict):
        logger.warning("Ignoring model reasoning metadata from %s: expected a JSON object.", path)
        return {}, {}
    return (
        _parse_reasoning_map(payload.get("models", {}), path, "model"),
        _parse_reasoning_map(payload.get("provider_defaults", {}), path, "provider"),
    )


def resolve_reasoning_support(
    model: str | None,
    *,
    provider_label: str | None = None,
    model_reasoning: dict[str, ReasoningSupport] | None = None,
    provider_reasoning_defaults: dict[str, ReasoningSupport] | None = None,
) -> ReasoningSupport | None:
    """Most specific declaration wins: the model's own, then its provider's."""
    name = (model or "").strip()
    if name and (model_reasoning or {}).get(name):
        return model_reasoning[name]
    label = (provider_label or "").strip()
    if label and (provider_reasoning_defaults or {}).get(label):
        return provider_reasoning_defaults[label]
    return None
