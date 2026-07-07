from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def load_shared_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    normalized = [_normalize_item(item) for item in items if isinstance(item, dict)]
    # Newest shared_at first. ISO-8601 UTC timestamps sort lexicographically; a
    # stable sort keeps insertion order (newest-first, see save) for any ties.
    normalized.sort(key=lambda item: item.get("shared_at") or "", reverse=True)
    return normalized


def save_shared_history_item(
    path: Path,
    *,
    owner_id: str | None = None,
    author_name: str = "",
    note: str = "",
    question: str = "",
    answer: str = "",
    mode: str = "",
    settings: dict[str, Any] | None = None,
    sources: list[Any] | None = None,
    retrieved_chunks: list[Any] | None = None,
    source_count: Any = 0,
    created_at: str = "",
) -> dict[str, Any]:
    items = load_shared_history(path)
    record = {
        "id": uuid4().hex,
        "owner_id": (owner_id or "").strip(),
        "author_name": author_name or "",
        "note": note or "",
        "question": question or "",
        "answer": answer or "",
        "mode": mode or "",
        # Stored verbatim so nothing (e.g. the raw request payload in settings)
        # is dropped.
        "settings": settings if isinstance(settings, dict) else {},
        "sources": sources if isinstance(sources, list) else [],
        "retrieved_chunks": retrieved_chunks if isinstance(retrieved_chunks, list) else [],
        "source_count": _coerce_int(source_count),
        "created_at": created_at or "",
        "shared_at": datetime.now(timezone.utc).isoformat(),
    }
    next_items = [record, *items]
    _write_items(path, next_items)
    return record


def delete_shared_history_item(path: Path, item_id: str) -> bool:
    items = load_shared_history(path)
    next_items = [item for item in items if item["id"] != item_id]
    if len(next_items) == len(items):
        return False
    _write_items(path, next_items)
    return True


def _write_items(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    settings = item.get("settings")
    sources = item.get("sources")
    retrieved_chunks = item.get("retrieved_chunks")
    return {
        "id": str(item.get("id") or uuid4().hex),
        "owner_id": str(item.get("owner_id") or ""),
        "author_name": str(item.get("author_name") or ""),
        "note": str(item.get("note") or ""),
        "question": str(item.get("question") or ""),
        "answer": str(item.get("answer") or ""),
        "mode": str(item.get("mode") or ""),
        # Preserve verbatim; only guard against non-container junk.
        "settings": settings if isinstance(settings, dict) else {},
        "sources": sources if isinstance(sources, list) else [],
        "retrieved_chunks": retrieved_chunks if isinstance(retrieved_chunks, list) else [],
        "source_count": _coerce_int(item.get("source_count")),
        "created_at": str(item.get("created_at") or ""),
        "shared_at": str(item.get("shared_at") or ""),
    }


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
