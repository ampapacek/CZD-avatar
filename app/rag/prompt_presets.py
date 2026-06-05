from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.rag.wp_config import resolve_wp_id


def load_prompt_presets(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    presets = data.get("presets") if isinstance(data, dict) else data
    if not isinstance(presets, list):
        return []
    return [_normalize_preset(item) for item in presets if isinstance(item, dict)]


def save_prompt_preset(
    path: Path,
    name: str,
    system_prompt: str,
    user_prompt_template: str,
    wp_id: str | None = None,
    placeholders: dict[str, Any] | None = None,
    preset_id: str | None = None,
    owner_id: str | None = None,
) -> dict[str, Any]:
    presets = load_prompt_presets(path)
    existing = next((preset for preset in presets if preset["id"] == preset_id), None) if preset_id else None
    resolved_id = preset_id or _slugify(name)
    if any(preset["id"] != preset_id and preset["id"] == resolved_id for preset in presets):
        suffix = 2
        base_id = resolved_id
        while any(preset["id"] != preset_id and preset["id"] == f"{base_id}-{suffix}" for preset in presets):
            suffix += 1
        resolved_id = f"{base_id}-{suffix}"
    # Keep ownership stable across updates. An ownerless preset has no owner_id to
    # match, so reaching this point for one requires the admin password (see
    # _can_modify_prompt_preset); that admin-authorized edit claims it for the
    # editing browser.
    resolved_owner = (existing.get("owner_id") if existing else "") or (owner_id or "").strip()
    resolved_wp_id = resolve_wp_id(wp_id if wp_id is not None else (existing.get("wp_id") if existing else None))
    record = {
        "id": resolved_id,
        "name": name.strip(),
        "wp_id": resolved_wp_id,
        "system_prompt": system_prompt,
        "user_prompt_template": user_prompt_template,
        "placeholders": _normalize_placeholders(placeholders),
        "owner_id": resolved_owner,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    next_presets = [record, *[preset for preset in presets if preset["id"] != resolved_id]]
    _write_presets(path, next_presets)
    return record


def delete_prompt_preset(path: Path, preset_id: str) -> bool:
    presets = load_prompt_presets(path)
    next_presets = [preset for preset in presets if preset["id"] != preset_id]
    if len(next_presets) == len(presets):
        return False
    _write_presets(path, next_presets)
    return True


def _write_presets(path: Path, presets: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"presets": presets}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_preset(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or "Prompt").strip()
    preset_id = str(item.get("id") or _slugify(name)).strip()
    return {
        "id": preset_id,
        "name": name,
        "wp_id": resolve_wp_id(item.get("wp_id")),
        "system_prompt": str(item.get("system_prompt") or ""),
        "user_prompt_template": str(item.get("user_prompt_template") or ""),
        "placeholders": _normalize_placeholders(item.get("placeholders")),
        "owner_id": str(item.get("owner_id") or ""),
        "updated_at": str(item.get("updated_at") or ""),
    }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or f"prompt-{int(datetime.now(timezone.utc).timestamp())}"


def _normalize_placeholders(value: Any) -> dict[str, dict[str, Any]]:
    """Normalize an inline ``name -> PlaceholderDef`` map into stored records.

    Inline defs are the highest-precedence placeholder source. Each value keeps
    the ``PlaceholderDef`` shape (``label``/``kind``/``help``/``default``/
    ``options``); unknown kinds fall back to ``text`` and options are only kept
    for ``select``.
    """

    if not isinstance(value, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for name, definition in value.items():
        if not isinstance(definition, dict):
            continue
        kind = str(definition.get("kind") or "text").strip()
        if kind not in {"select", "text"}:
            kind = "text"
        help_value = definition.get("help")
        result[str(name)] = {
            "label": str(definition.get("label") or name).strip(),
            "kind": kind,
            "help": (str(help_value).strip() if help_value not in (None, "") else None),
            "default": str(definition.get("default") or ""),
            "options": _normalize_inline_options(definition.get("options")) if kind == "select" else [],
        }
    return result


def _normalize_inline_options(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    options: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        option_name = str(item.get("name") or "").strip()
        if not option_name:
            continue
        options.append(
            {
                "name": option_name,
                "label": str(item.get("label") or option_name).strip(),
                "text": str(item.get("text") or ""),
            }
        )
    return options
