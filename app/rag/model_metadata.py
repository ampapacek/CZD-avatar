from __future__ import annotations

import json
import logging
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
