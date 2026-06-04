from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    style_prompts: dict[str, str] | None = None,
    length_prompts: dict[str, str] | None = None,
    preset_id: str | None = None,
    owner_id: str | None = None,
) -> dict[str, str]:
    presets = load_prompt_presets(path)
    existing = next((preset for preset in presets if preset["id"] == preset_id), None) if preset_id else None
    resolved_id = preset_id or _slugify(name)
    if any(preset["id"] != preset_id and preset["id"] == resolved_id for preset in presets):
        suffix = 2
        base_id = resolved_id
        while any(preset["id"] != preset_id and preset["id"] == f"{base_id}-{suffix}" for preset in presets):
            suffix += 1
        resolved_id = f"{base_id}-{suffix}"
    # Keep ownership stable across updates; an authorized edit of an ownerless
    # preset lets the editing browser claim it.
    resolved_owner = (existing.get("owner_id") if existing else "") or (owner_id or "").strip()
    record = {
        "id": resolved_id,
        "name": name.strip(),
        "system_prompt": system_prompt,
        "user_prompt_template": user_prompt_template,
        "style_prompts": style_prompts or {},
        "length_prompts": length_prompts or {},
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


def _normalize_preset(item: dict[str, Any]) -> dict[str, str]:
    name = str(item.get("name") or "Prompt").strip()
    preset_id = str(item.get("id") or _slugify(name)).strip()
    return {
        "id": preset_id,
        "name": name,
        "system_prompt": str(item.get("system_prompt") or ""),
        "user_prompt_template": str(item.get("user_prompt_template") or ""),
        "style_prompts": _string_dict(item.get("style_prompts")),
        "length_prompts": _string_dict(item.get("length_prompts")),
        "owner_id": str(item.get("owner_id") or ""),
        "updated_at": str(item.get("updated_at") or ""),
    }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or f"prompt-{int(datetime.now(timezone.utc).timestamp())}"


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}
