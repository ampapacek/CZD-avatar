from __future__ import annotations

import re
from typing import Any


_LINDAT_MODEL_RE = re.compile(r"^[a-z]{2,3}-[a-z]{2,3}$", re.IGNORECASE)
_QUERY_TRANSFORM_TOKEN_RE = re.compile(r"\{question\}|\{instruction\}")


def render_query_transform_prompt(template: str, question: str, instruction: str) -> str:
    """Fill the ``{question}``/``{instruction}`` tokens in a single pass.

    Chained ``template.replace("{question}", question).replace("{instruction}",
    instruction)`` would rescan the already-substituted string for the second
    token, so a literal ``{instruction}`` inside the user's question gets
    clobbered by the instruction text. A single regex pass only ever matches
    tokens that were in the original template.
    """

    values = {"{question}": question, "{instruction}": instruction}
    return _QUERY_TRANSFORM_TOKEN_RE.sub(lambda match: values[match.group(0)], template)


def normalize_query_transform(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    enabled = bool(value.get("enabled", False))
    result: dict[str, Any] = {
        "enabled": enabled,
        "actions": _normalize_actions(value.get("actions")) if enabled else [],
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
        description = str(item.get("description") or "").strip()
        if not action_id or not description or action_id in seen or action_type not in {"lindat", "llm"}:
            continue
        action: dict[str, Any] = {
            "id": action_id,
            "label": str(item.get("label") or action_id).strip(),
            "description": description,
            "type": action_type,
            "use_transformed_for_answer": bool(item.get("use_transformed_for_answer", False)),
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
            action["prompt_template"] = str(item.get("prompt_template") or "").strip()
        seen.add(action_id)
        result.append(action)
    return result
