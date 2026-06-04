from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.rag.prompts import OptionDef, PlaceholderDef


VALID_KINDS = {"select", "text"}


def placeholder_def_from_record(record: dict[str, Any]) -> PlaceholderDef:
    return PlaceholderDef(
        label=str(record.get("label") or record.get("name") or ""),
        kind=str(record.get("kind") or "text"),
        help=record.get("help"),
        default=str(record.get("default") or ""),
        options=[
            OptionDef(
                name=str(option.get("name") or ""),
                label=str(option.get("label") or option.get("name") or ""),
                text=str(option.get("text") or ""),
            )
            for option in (record.get("options") or [])
            if isinstance(option, dict)
        ],
    )


def placeholder_defs_from_records(records: list[dict[str, Any]]) -> dict[str, PlaceholderDef]:
    return {
        str(record["name"]): placeholder_def_from_record(record)
        for record in records
        if record.get("name")
    }


def load_placeholders(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    items = data.get("placeholders") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [_normalize_placeholder(item) for item in items if isinstance(item, dict)]


def save_placeholder(
    path: Path,
    name: str,
    label: str,
    kind: str = "text",
    help: str | None = None,
    default: str = "",
    options: list[dict[str, str]] | None = None,
    owner_id: str | None = None,
) -> dict[str, Any]:
    placeholders = load_placeholders(path)
    resolved_name = _slugify(name)
    existing = next((item for item in placeholders if item["name"] == resolved_name), None)
    # Keep ownership stable across updates; an authorized edit of an ownerless
    # placeholder lets the editing browser claim it.
    resolved_owner = (existing.get("owner_id") if existing else "") or (owner_id or "").strip()
    record = _normalize_placeholder(
        {
            "name": resolved_name,
            "label": label,
            "kind": kind,
            "help": help,
            "default": default,
            "options": options or [],
            "owner_id": resolved_owner,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    next_items = [record, *[item for item in placeholders if item["name"] != resolved_name]]
    _write_placeholders(path, next_items)
    return record


def delete_placeholder(path: Path, name: str) -> bool:
    placeholders = load_placeholders(path)
    next_items = [item for item in placeholders if item["name"] != name]
    if len(next_items) == len(placeholders):
        return False
    _write_placeholders(path, next_items)
    return True


def _write_placeholders(path: Path, placeholders: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"placeholders": placeholders}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_placeholder(item: dict[str, Any]) -> dict[str, Any]:
    name = _slugify(str(item.get("name") or ""))
    kind = str(item.get("kind") or "text").strip()
    if kind not in VALID_KINDS:
        kind = "text"
    label = str(item.get("label") or name).strip()
    help_value = item.get("help")
    options = _normalize_options(item.get("options")) if kind == "select" else []
    return {
        "name": name,
        "label": label,
        "kind": kind,
        "help": (str(help_value).strip() if help_value not in (None, "") else None),
        "default": str(item.get("default") or ""),
        "options": options,
        "owner_id": str(item.get("owner_id") or ""),
        "updated_at": str(item.get("updated_at") or ""),
    }


def _normalize_options(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    options: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        options.append(
            {
                "name": name,
                "label": str(item.get("label") or name).strip(),
                "text": str(item.get("text") or ""),
            }
        )
    return options


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return slug or f"placeholder_{int(datetime.now(timezone.utc).timestamp())}"
