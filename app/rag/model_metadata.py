from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReasoningSupport:
    """What a model does about reasoning, declared as data rather than in code.

    Providers disagree on both the request parameter and the effort vocabulary,
    and none of it is discoverable, so `data/models.json` states it per model
    (or per provider as a fallback). A model that declares nothing gets nothing
    sent, which is the old behaviour.

    `efforts` may be empty. That is the "reasons, but we cannot steer it" case:
    the model returns a trace whatever we ask, but the effort parameter does not
    reach it — so no control is offered and no parameter is sent, while the
    trace is still shown.
    """

    # Request field: "reasoning" sends {"reasoning": {"effort": ...}},
    # "reasoning_effort" sends {"reasoning_effort": ...}.
    param: str = "reasoning_effort"
    # Literal values the provider accepts, in the order to show them. Empty
    # means the effort cannot be steered.
    efforts: tuple[str, ...] = ()
    # What to send when the user has not chosen: usually the cheapest option.
    default: str | None = None
    # True when the model reasons whether or not it is asked to.
    mandatory: bool = False
    # Free text for humans; never sent anywhere, never parsed.
    note: str = ""

    @property
    def controllable(self) -> bool:
        return bool(self.efforts)

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
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Everything `data/models.json` knows, per model and per provider."""

    context_windows: dict[str, int] = field(default_factory=dict)
    provider_context_windows: dict[str, int] = field(default_factory=dict)
    reasoning: dict[str, ReasoningSupport] = field(default_factory=dict)
    provider_reasoning: dict[str, ReasoningSupport] = field(default_factory=dict)


VALID_REASONING_PARAMS = ("reasoning", "reasoning_effort")

# Effort values that mean "do not reason". Providers spell it differently, and a
# model that reasons unconditionally accepts none of them.
OFF_EFFORTS = ("none", "off")

MIN_CONTEXT_WINDOW_TOKENS = 1024


def _parse_context_window(value: object, path: Path, name: str) -> int | None:
    try:
        tokens = int(value)
    except (TypeError, ValueError):
        logger.warning("Ignoring invalid context window for %r in %s.", name, path)
        return None
    if tokens < MIN_CONTEXT_WINDOW_TOKENS:
        logger.warning("Ignoring too-small context window for %r in %s.", name, path)
        return None
    return tokens


def _parse_reasoning(payload: object, path: Path, name: str) -> ReasoningSupport | None:
    if not isinstance(payload, dict):
        logger.warning("Ignoring reasoning for %r in %s: expected a JSON object.", name, path)
        return None

    param = str(payload.get("param") or "reasoning_effort").strip()
    if param not in VALID_REASONING_PARAMS:
        logger.warning("Ignoring reasoning for %r in %s: unknown param %r.", name, path, param)
        return None

    raw_efforts = payload.get("efforts") or []
    if not isinstance(raw_efforts, list):
        logger.warning("Ignoring reasoning for %r in %s: 'efforts' must be a list.", name, path)
        return None
    efforts = tuple(str(effort).strip() for effort in raw_efforts if str(effort).strip())

    mandatory = bool(payload.get("mandatory"))
    if not efforts and not mandatory:
        # Says neither "you can steer it" nor "it happens anyway" — nothing to act on.
        logger.warning("Ignoring reasoning for %r in %s: no efforts and not mandatory.", name, path)
        return None

    if mandatory:
        # "Mandatory" and an off switch contradict each other, and we shipped the
        # contradiction: `openai/gpt-oss-120b` listed "none", which OpenRouter
        # answers with `400 Reasoning is mandatory for this endpoint and cannot
        # be disabled` — so *every* answer from that model failed. Drop the
        # switch rather than offer one that cannot work. A model that really can
        # be turned off must not claim to be mandatory.
        steerable = tuple(effort for effort in efforts if effort not in OFF_EFFORTS)
        if steerable != efforts:
            logger.warning(
                "Dropping the off switch from mandatory reasoning for %r in %s: %s cannot be disabled.",
                name,
                path,
                ", ".join(effort for effort in efforts if effort in OFF_EFFORTS),
            )
        efforts = steerable

    raw_default = payload.get("default")
    default = str(raw_default).strip() if raw_default is not None else None
    if default and default not in efforts:
        logger.warning("Ignoring default effort %r for %r in %s: not among 'efforts'.", default, name, path)
        default = None

    return ReasoningSupport(
        param=param,
        efforts=efforts,
        default=default,
        mandatory=mandatory,
        note=str(payload.get("note") or "").strip(),
    )


def _parse_entries(
    payload: object,
    path: Path,
    label: str,
) -> tuple[dict[str, int], dict[str, ReasoningSupport]]:
    if not isinstance(payload, dict):
        logger.warning("Ignoring %s metadata from %s: expected a JSON object.", label, path)
        return {}, {}

    windows: dict[str, int] = {}
    reasoning: dict[str, ReasoningSupport] = {}
    for raw_name, entry in payload.items():
        name = str(raw_name).strip()
        if not name:
            continue
        if not isinstance(entry, dict):
            logger.warning("Ignoring %s %r in %s: expected a JSON object.", label, name, path)
            continue
        if "context_window" in entry:
            tokens = _parse_context_window(entry["context_window"], path, name)
            if tokens is not None:
                windows[name] = tokens
        if "reasoning" in entry:
            support = _parse_reasoning(entry["reasoning"], path, name)
            if support is not None:
                reasoning[name] = support
    return windows, reasoning


def load_model_metadata(path: Path) -> ModelMetadata:
    """Load `data/models.json`. A missing or broken file is not fatal."""
    if not path.exists():
        return ModelMetadata()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load model metadata from %s: %s", path, exc)
        return ModelMetadata()
    if not isinstance(payload, dict):
        logger.warning("Ignoring model metadata from %s: expected a JSON object.", path)
        return ModelMetadata()

    model_windows, model_reasoning = _parse_entries(payload.get("models", {}), path, "model")
    provider_windows, provider_reasoning = _parse_entries(
        payload.get("provider_defaults", {}), path, "provider"
    )
    return ModelMetadata(
        context_windows=model_windows,
        provider_context_windows=provider_windows,
        reasoning=model_reasoning,
        provider_reasoning=provider_reasoning,
    )


def filter_model_context_windows(
    model_context_windows: dict[str, int] | None,
    model_names: list[str] | tuple[str, ...],
) -> dict[str, int]:
    known_windows = model_context_windows or {}
    return {model: known_windows[model] for model in model_names if model in known_windows}


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
