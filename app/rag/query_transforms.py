from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_LINDAT_MODEL_RE = re.compile(r"^[a-z]{2,3}-[a-z]{2,3}$", re.IGNORECASE)


def load_query_transforms(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Load tracked WP defaults and prompt-specific whole-object overrides."""

    empty = {"wp_defaults": {}, "prompt_overrides": {}}
    if not path.exists():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty
    if not isinstance(data, dict):
        return empty
    return {
        "wp_defaults": _normalize_transform_map(data.get("wp_defaults")),
        "prompt_overrides": _normalize_transform_map(data.get("prompt_overrides")),
    }


def resolve_query_transform(
    config: dict[str, dict[str, dict[str, Any]]],
    wp_id: str,
    prompt_preset_id: str | None = None,
) -> dict[str, Any] | None:
    """Resolve prompt override -> WP default without merging action lists.

    A prompt override is a whole object. ``enabled: false`` explicitly disables
    an inherited WP transform; a missing prompt entry inherits the WP object.
    """

    prompt_id = (prompt_preset_id or "").strip()
    if prompt_id and prompt_id in config["prompt_overrides"]:
        return config["prompt_overrides"][prompt_id]
    return config["wp_defaults"].get(wp_id)


def normalize_query_transform(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    enabled = bool(value.get("enabled", False))
    result: dict[str, Any] = {
        "enabled": enabled,
        "actions": _normalize_actions(value.get("actions")) if enabled else [],
        "use_transformed_for_answer": bool(value.get("use_transformed_for_answer", False)),
    }
    default_action = str(value.get("default_action") or "").strip()
    action_ids = {action["id"] for action in result["actions"]}
    if default_action in action_ids:
        result["default_action"] = default_action
    elif result["actions"]:
        result["default_action"] = result["actions"][0]["id"]
    return result


def valid_lindat_model(model: str) -> bool:
    """Keep the configured model in one URL path segment (no arbitrary URLs)."""

    return bool(_LINDAT_MODEL_RE.fullmatch((model or "").strip()))


def _normalize_transform_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, transform in value.items():
        normalized = normalize_query_transform(transform)
        if normalized is not None:
            result[str(key)] = normalized
    return result


def _normalize_actions(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("id") or "").strip()
        action_type = str(item.get("type") or "").strip().lower()
        if not action_id or action_id in seen or action_type not in {"lindat", "llm"}:
            continue
        action: dict[str, Any] = {
            "id": action_id,
            "label": str(item.get("label") or action_id).strip(),
            "type": action_type,
        }
        if action_type == "lindat":
            model = str(item.get("model") or "").strip()
            if not valid_lindat_model(model):
                continue
            action.update(
                {
                    "model": model,
                    "source_language": str(item.get("source_language") or "").strip(),
                    "target_language": str(item.get("target_language") or "").strip(),
                }
            )
        else:
            action["prompt"] = str(item.get("prompt") or "").strip()
        seen.add(action_id)
        result.append(action)
    return result
