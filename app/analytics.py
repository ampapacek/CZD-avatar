from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import math
import os
import re
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from fastapi import Request

logger = logging.getLogger(__name__)
SCHEMA_VERSION = 1
_last_write_warning = 0.0


@dataclass(frozen=True, slots=True)
class AnalyticsContext:
    request_id: str
    turn_id: str | None
    client_id: str | None
    session_id: str | None
    source: str
    instance_id: str
    provider: str | None = None
    key_source: str | None = None
    purpose: str = "other"


_context: ContextVar[AnalyticsContext | None] = ContextVar("analytics_context", default=None)
_writer: "AnalyticsWriter | None" = None


class AnalyticsWriter:
    def __init__(self, enabled: bool, directory: Path, instance_id: str) -> None:
        self.enabled = enabled
        self.directory = Path(directory)
        self.instance_id = instance_id

    def event(self, event: str, context: AnalyticsContext | None = None, **fields: Any) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        ctx = context or _context.get()
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "event_id": str(uuid.uuid4()),
            "event": event,
            "ts": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "instance_id": ctx.instance_id if ctx else self.instance_id,
            "request_id": ctx.request_id if ctx else str(uuid.uuid4()),
            "turn_id": ctx.turn_id if ctx else None,
            "client_id": ctx.client_id if ctx else None,
            "session_id": ctx.session_id if ctx else None,
            "source": ctx.source if ctx else "api",
            **fields,
        }
        self.write(record, now=now)
        return record

    def write(self, record: dict[str, Any], *, now: datetime | None = None) -> None:
        if not self.enabled:
            return
        try:
            timestamp = now or _parse_timestamp(record.get("ts")) or datetime.now(timezone.utc)
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(self.directory, 0o700)
            path = self.directory / f"usage-{timestamp:%Y-%m}.jsonl"
            line = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.fchmod(fd, 0o600)
                fcntl.flock(fd, fcntl.LOCK_EX)
                remaining = memoryview(line)
                while remaining:
                    written = os.write(fd, remaining)
                    if written <= 0:
                        raise OSError("analytics append made no progress")
                    remaining = remaining[written:]
            finally:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)
        except Exception:
            global _last_write_warning
            current = time.monotonic()
            if current - _last_write_warning >= 60:
                _last_write_warning = current
                logger.warning("Could not append usage analytics event", exc_info=True)


def configure(enabled: bool, directory: Path, instance_id: str) -> AnalyticsWriter:
    global _writer
    _writer = AnalyticsWriter(enabled, directory, instance_id)
    return _writer


def emit(event: str, **fields: Any) -> dict[str, Any] | None:
    if _writer is None:
        return None
    return _writer.event(event, **fields)


def request_context(request: Request, instance_id: str) -> AnalyticsContext:
    client_id = _clean_header(request.headers.get("x-client-id"))
    session_id = _clean_header(request.headers.get("x-session-id"))
    return AnalyticsContext(
        request_id=str(uuid.uuid4()),
        turn_id=_clean_header(request.headers.get("x-turn-id")),
        client_id=client_id,
        session_id=session_id,
        source="ui" if client_id or session_id else "api",
        instance_id=instance_id,
    )


@contextmanager
def bind_context(context: AnalyticsContext, **updates: Any) -> Iterator[AnalyticsContext]:
    effective = replace(context, **updates) if updates else context
    token = _context.set(effective)
    try:
        yield effective
    finally:
        _context.reset(token)


def current_context() -> AnalyticsContext | None:
    return _context.get()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def text_lengths(text: str, prefix: str) -> dict[str, int]:
    clean = text.strip()
    return {
        f"{prefix}_chars": len(clean),
        f"{prefix}_words": len(re.findall(r"\S+", clean)),
    }


def estimated_tokens(text: str) -> int:
    clean = text.strip()
    return 0 if not clean else max(1, math.ceil(len(clean) / 3.2))


def question_metadata(question: str, questions: list[str] | None) -> dict[str, Any]:
    clean = question.strip()
    normalized = [item.strip() for item in (questions or []) if item.strip()]
    index = next((i for i, item in enumerate(normalized, 1) if item == clean), None)
    return {
        "question_hash": sha256_text(clean),
        **text_lengths(clean, "question"),
        "is_prepared_question": index is not None,
        "prepared_question_index": index,
        "is_default_question": index == 1,
        "question_list_hash": sha256_text("\n".join(normalized)) if normalized else None,
    }


def endpoint_host(base_url: str | None) -> str | None:
    return urlparse((base_url or "").strip()).hostname


def error_code(exc: BaseException, http_status: int | None = None) -> str:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    status = http_status or getattr(getattr(exc, "response", None), "status_code", None)
    if "promptbudget" in name or "token budget" in message or "prompt is too long" in message:
        return "token_budget"
    if "context length" in message or "context_window" in message:
        return "context_length"
    if status == 429 or "rate limit" in message:
        return "upstream_rate_limit"
    if "timeout" in name or "timed out" in message:
        return "upstream_timeout"
    if status and status >= 500:
        return "upstream_http_error"
    if status in {400, 401, 403}:
        return "policy_rejected"
    return "internal_error"


def ms(seconds: float) -> int:
    return max(0, round(seconds * 1000))


def _clean_header(value: str | None) -> str | None:
    clean = (value or "").strip()
    return clean[:200] or None


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
