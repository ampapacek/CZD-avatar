"""Cached answers for first-turn /chat/stream requests.

The key is a hash of the request itself with every default resolved (provider,
model, base URL, prompt templates, placeholder defs, the server's retrieval and
budget settings), so a hit skips retrieval as well as the LLM, and the stored
sources are the ones the answer cites. Only first turns are cached: a
follow-up depends on the whole conversation and would almost never repeat.

Entries expire after a TTL and the least recently used ones are evicted above
a size cap; pinned entries (pinned by scripts/warm_cache.py or in the admin
Cache dialog) are exempt from both. Like the account store, every operation
opens its own short-lived SQLite connection.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import zlib
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

# Bump to invalidate every entry when the key input or payload shape changes.
CACHE_VERSION = 2

# Request fields left out of the key. Everything else is in it: a field added
# to ChatRequest is part of the key unless it is listed here, and
# tests/test_answer_cache.py fails until it is classified.
KEY_EXCLUDED_FIELDS = frozenset(
    {
        # Credentials: the answer does not depend on whose key paid for it.
        # Access to the model is still checked before the lookup.
        "llm_api_key",
        "admin_password",
        # Analytics and display only.
        "query_transform_ms",
        "query_transform_kind",
        "prompt_preset_id",
        # Controls the cache itself.
        "bypass_cache",
    }
)

# Replay speed of a cached answer: about this fast, but never quicker than the
# minimum (it would look like a glitch) nor slower than the maximum.
REPLAY_CHARS_PER_SECOND = 150.0
REPLAY_MIN_SECONDS = 1.5
REPLAY_MAX_SECONDS = 10.0
# Word-sized pieces, keeping the whitespace after each word.
_WORD_RE = re.compile(r"\s*\S+\s*|\s+")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS answers (
    key TEXT PRIMARY KEY,
    key_input TEXT NOT NULL,
    meta TEXT NOT NULL,
    payload BLOB NOT NULL,
    created_at REAL NOT NULL,
    last_hit_at REAL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    pinned INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS answers_last_used ON answers (pinned, coalesce(last_hit_at, created_at));
"""


def is_cacheable(request: Any) -> bool:
    """Only first turns: no history and no summary of an earlier one."""

    return not request.conversation_history and not (request.conversation_summary or "").strip()


def key_input(request: Any, **resolved: Any) -> dict[str, Any]:
    """The request without the excluded fields, with the resolved values on top.

    ``resolved`` overrides request fields of the same name (e.g. ``model``)
    and adds what the server fills in (e.g. ``server`` settings).
    """

    fields = {
        name: value
        for name, value in request.model_dump(mode="json").items()
        if name not in KEY_EXCLUDED_FIELDS
    }
    return {"cache_version": CACHE_VERSION, **fields, **resolved}


def cache_key(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def replay_pieces(answer: str) -> tuple[list[str], float]:
    """Split an answer into word-sized pieces and the pause between them."""

    pieces = _WORD_RE.findall(answer)
    if not pieces:
        return [], 0.0
    total = min(max(len(answer) / REPLAY_CHARS_PER_SECOND, REPLAY_MIN_SECONDS), REPLAY_MAX_SECONDS)
    return pieces, total / len(pieces)


def _encode(value: Any) -> bytes:
    return zlib.compress(json.dumps(value, ensure_ascii=False).encode("utf-8"), 6)


def _decode(blob: bytes) -> Any:
    return json.loads(zlib.decompress(blob).decode("utf-8"))


class AnswerCache:
    def __init__(self, path: Path, *, ttl_seconds: float, max_entries: int) -> None:
        self.path = Path(path)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self):
        """One connection per operation, committed on success, always closed."""

        with closing(sqlite3.connect(self.path, timeout=10)) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn

    def _expired(self, row: sqlite3.Row, now: float) -> bool:
        return not row["pinned"] and now - row["created_at"] > self.ttl_seconds

    def get(self, key: str, *, now: float | None = None) -> dict[str, Any] | None:
        """The stored payload, counting the hit; None when missing or expired."""

        now = time.time() if now is None else now
        with self._connect() as conn:
            row = conn.execute("SELECT payload, created_at, pinned FROM answers WHERE key = ?", (key,)).fetchone()
            if row is None:
                return None
            if self._expired(row, now):
                conn.execute("DELETE FROM answers WHERE key = ?", (key,))
                return None
            conn.execute(
                "UPDATE answers SET last_hit_at = ?, hit_count = hit_count + 1 WHERE key = ?",
                (now, key),
            )
        payload = _decode(row["payload"])
        payload["cached_at"] = row["created_at"]
        return payload

    def contains(self, key: str, *, now: float | None = None) -> bool:
        """Whether a live entry exists, without counting it as a hit."""

        now = time.time() if now is None else now
        with self._connect() as conn:
            row = conn.execute("SELECT created_at, pinned FROM answers WHERE key = ?", (key,)).fetchone()
        return row is not None and not self._expired(row, now)

    def put(
        self,
        key: str,
        key_input: dict[str, Any],
        payload: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
        pinned: bool = False,
        now: float | None = None,
    ) -> None:
        """Store or overwrite an entry. An entry once pinned stays pinned, so
        regenerating a warmed answer does not expose it to eviction."""

        now = time.time() if now is None else now
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO answers (key, key_input, meta, payload, created_at, pinned)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (key) DO UPDATE SET
                    key_input = excluded.key_input,
                    meta = excluded.meta,
                    payload = excluded.payload,
                    created_at = excluded.created_at,
                    pinned = max(answers.pinned, excluded.pinned)
                """,
                (
                    key,
                    json.dumps(key_input, ensure_ascii=False, default=str),
                    json.dumps(meta or {}, ensure_ascii=False, default=str),
                    _encode(payload),
                    now,
                    int(pinned),
                ),
            )
            self._evict(conn, now)

    def _evict(self, conn: sqlite3.Connection, now: float) -> None:
        conn.execute("DELETE FROM answers WHERE pinned = 0 AND created_at < ?", (now - self.ttl_seconds,))
        count = conn.execute("SELECT count(*) FROM answers WHERE pinned = 0").fetchone()[0]
        excess = count - self.max_entries
        if excess > 0:
            conn.execute(
                """
                DELETE FROM answers WHERE key IN (
                    SELECT key FROM answers WHERE pinned = 0
                    ORDER BY coalesce(last_hit_at, created_at) LIMIT ?
                )
                """,
                (excess,),
            )

    def pin(self, key: str) -> bool:
        """Exempt an entry from expiry and eviction; False when it is missing."""

        with self._connect() as conn:
            return conn.execute("UPDATE answers SET pinned = 1 WHERE key = ?", (key,)).rowcount > 0

    def unpin(self, key: str) -> bool:
        """Let an entry expire and be evicted again; False when it is missing."""

        with self._connect() as conn:
            return conn.execute("UPDATE answers SET pinned = 0 WHERE key = ?", (key,)).rowcount > 0

    def entries(self, *, now: float | None = None) -> list[dict[str, Any]]:
        """Every live entry without its payload, newest first, for the admin view.

        ``server`` and ``cache_version`` are the ones the key was made with.
        """

        now = time.time() if now is None else now
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT key, created_at, last_hit_at, hit_count, pinned, meta,
                       length(payload) AS size,
                       json_extract(key_input, '$.question') AS question,
                       json_extract(key_input, '$.wp_id') AS wp_id,
                       json_extract(key_input, '$.llm_provider') AS llm_provider,
                       json_extract(key_input, '$.model') AS model,
                       json_extract(key_input, '$.cache_version') AS cache_version,
                       json_extract(key_input, '$.server') AS server
                FROM answers ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            {
                "key": row["key"],
                "question": row["question"] or "",
                "wp_id": row["wp_id"],
                "llm_provider": row["llm_provider"],
                "model": row["model"],
                "prompt_preset_id": json.loads(row["meta"]).get("prompt_preset_id"),
                "created_at": row["created_at"],
                "last_hit_at": row["last_hit_at"],
                "hit_count": row["hit_count"],
                "pinned": bool(row["pinned"]),
                "size": row["size"],
                "cache_version": row["cache_version"],
                "server": json.loads(row["server"]) if row["server"] else None,
            }
            for row in rows
            if not self._expired(row, now)
        ]

    def peek(self, key: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """The key input and payload of an entry, without counting a hit."""

        with self._connect() as conn:
            row = conn.execute("SELECT key_input, payload FROM answers WHERE key = ?", (key,)).fetchone()
        return None if row is None else (json.loads(row["key_input"]), _decode(row["payload"]))

    def delete(self, key: str) -> bool:
        with self._connect() as conn:
            return conn.execute("DELETE FROM answers WHERE key = ?", (key,)).rowcount > 0

    def delete_many(self, keys: list[str]) -> int:
        with self._connect() as conn:
            return conn.executemany("DELETE FROM answers WHERE key = ?", [(key,) for key in keys]).rowcount

    def size_bytes(self) -> int:
        """The database file size, including the write-ahead log."""

        return sum(path.stat().st_size for path in (self.path, self.path.with_name(self.path.name + "-wal")) if path.exists())

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT count(*) FROM answers").fetchone()[0]
