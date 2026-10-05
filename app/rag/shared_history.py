from __future__ import annotations

import fcntl
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# "listed" items appear in the shared list; "link" items are reachable only by
# their (unguessable) id, like an unlisted video. Not access control.
VISIBILITIES = ("listed", "link")
DEFAULT_VISIBILITY = "listed"


def normalize_visibility(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in VISIBILITIES else DEFAULT_VISIBILITY


def load_shared_history(path: Path) -> list[dict[str, Any]]:
    try:
        return _read_items(path)
    except (ValueError, OSError):
        return []


def _read_items(path: Path) -> list[dict[str, Any]]:
    """Items newest-first; raises if the file exists but cannot be parsed.

    Readers treat that as empty, but writers must not: writing back "empty plus
    one" would replace every shared item with the new one.
    """
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"{path} has no list of items")
    normalized = [_normalize_item(item) for item in items if isinstance(item, dict)]
    # Newest shared_at first. ISO-8601 UTC timestamps sort lexicographically; a
    # stable sort keeps insertion order (newest-first, see save) for any ties.
    normalized.sort(key=lambda item: item.get("shared_at") or "", reverse=True)
    return normalized


@contextmanager
def _locked_items(path: Path) -> Iterator[list[dict[str, Any]]]:
    """Hold an exclusive lock across a read-modify-write of the file.

    `flock` on a sidecar lock file serializes both request threads (each opens
    its own descriptor) and uvicorn worker processes. Without it two shares at
    once both read the old list and the later write drops the other's item.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path.with_name(path.name + ".lock"), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield _read_items(path)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


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
    model_used: str | None = None,
    upstream_model: str | None = None,
    response_time_seconds: float | None = None,
    token_budget: dict[str, Any] | None = None,
    visibility: str = DEFAULT_VISIBILITY,
) -> dict[str, Any]:
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
        "model_used": model_used or None,
        "upstream_model": upstream_model or None,
        "response_time_seconds": _coerce_float(response_time_seconds),
        "token_budget": token_budget if isinstance(token_budget, dict) else None,
        "visibility": normalize_visibility(visibility),
        "note_edited_at": None,
    }
    with _locked_items(path) as items:
        _write_items(path, [record, *items])
    return record


def update_shared_history_item(
    path: Path,
    item_id: str,
    *,
    visibility: str | None = None,
    note: str | None = None,
) -> dict[str, Any] | None:
    """Apply the given changes; None leaves a field as it is.

    A note change stamps `note_edited_at`. Only the current text is kept, so the
    stamp says that the note changed after sharing, not what it said before.
    """
    with _locked_items(path) as items:
        for item in items:
            if item["id"] != item_id:
                continue
            if visibility is not None:
                item["visibility"] = normalize_visibility(visibility)
            if note is not None and note != item["note"]:
                item["note"] = note
                item["note_edited_at"] = datetime.now(timezone.utc).isoformat()
            _write_items(path, items)
            return item
    return None


def delete_shared_history_item(path: Path, item_id: str) -> bool:
    with _locked_items(path) as items:
        next_items = [item for item in items if item["id"] != item_id]
        if len(next_items) == len(items):
            return False
        _write_items(path, next_items)
    return True


def _write_items(path: Path, items: list[dict[str, Any]]) -> None:
    """Replace the file atomically: a crash mid-write leaves the old file whole."""
    payload = json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(tmp_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise


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
        # Absent on items shared before these were recorded.
        "model_used": str(item.get("model_used") or "") or None,
        "upstream_model": str(item.get("upstream_model") or "") or None,
        "response_time_seconds": _coerce_float(item.get("response_time_seconds")),
        "token_budget": item.get("token_budget") if isinstance(item.get("token_budget"), dict) else None,
        "visibility": normalize_visibility(item.get("visibility")),
        "note_edited_at": str(item.get("note_edited_at") or "") or None,
    }


def _coerce_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
