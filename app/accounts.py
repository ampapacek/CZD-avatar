"""User accounts: SQLite store, password hashing, sessions and the daily quota.

Only used when AUTH_ENABLED is set. There are few users (<100), so every
operation opens its own short-lived connection; SQLite serialises the writes
and no connection is ever shared between threads.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import deque
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from pwdlib import PasswordHash

STATUSES = ("active", "pending", "disabled")
REGISTRATION_MODES = ("open", "approval", "closed")
PASSWORD_MIN_LENGTH = 8
# Argon2 hashes any length, but a megabyte "password" is only a way to burn CPU.
PASSWORD_MAX_LENGTH = 256
EMAIL_MAX_LENGTH = 254
# Something before the @, a domain with at least one dot and a 2+ letter TLD.
# The address is only a unique username (nothing is ever sent to it), so this
# deliberately checks shape, not deliverability.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)*\.[a-z]{2,}$")
# The daily limit resets at midnight where the demo runs, not at UTC midnight.
QUOTA_TIMEZONE = ZoneInfo("Europe/Prague")

_hasher = PasswordHash.recommended()
# Each Argon2 hash or verify takes tens of MB of memory. Requests beyond this
# many at once wait for a slot, so a burst of registrations or logins gets
# slower instead of exhausting the server's memory.
_hash_slots = threading.BoundedSemaphore(4)


def _hash_password(password: str) -> str:
    with _hash_slots:
        return _hasher.hash(password)


def _verify_and_update(password: str, password_hash: str) -> tuple[bool, str | None]:
    with _hash_slots:
        return _hasher.verify_and_update(password, password_hash)


# Verified against when the email is unknown, so a login for a missing account
# takes as long as one with a wrong password and does not reveal which it was.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    -- AUTOINCREMENT: an id is never reused, so an admin acting on a list loaded
    -- before a deletion cannot hit an account registered after it.
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'pending', 'disabled')),
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user_id ON sessions(user_id);
CREATE TABLE IF NOT EXISTS daily_usage (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    requests INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class AccountError(ValueError):
    """A request the store refuses; the message is shown to the user as is."""


class TooManyPendingError(AccountError):
    """Registration refused: too many accounts already wait for approval."""


@dataclass(frozen=True)
class User:
    id: int
    email: str
    status: str
    is_admin: bool
    # Set only by authenticate(): the hash the password was checked against, so
    # create_session() can refuse if the password changed in the meantime.
    password_hash: str | None = field(default=None, repr=False, compare=False)


def normalize_email(email: str) -> str:
    """Lower-cased address, or AccountError when it does not look like one."""

    normalized = (email or "").strip().lower()
    if len(normalized) > EMAIL_MAX_LENGTH or not EMAIL_RE.match(normalized):
        raise AccountError("Zadej platnou e-mailovou adresu.")
    return normalized


def validate_password(password: str) -> str:
    if len(password or "") < PASSWORD_MIN_LENGTH:
        raise AccountError(f"Heslo musí mít alespoň {PASSWORD_MIN_LENGTH} znaků.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise AccountError(f"Heslo může mít nejvýše {PASSWORD_MAX_LENGTH} znaků.")
    return password


def quota_day(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(QUOTA_TIMEZONE).date().isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _token_hash(token: str) -> str:
    # Only the hash is stored, so a copy of the database holds no usable sessions.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user(row: sqlite3.Row) -> User:
    return User(id=row["id"], email=row["email"], status=row["status"], is_admin=bool(row["is_admin"]))


class AccountStore:
    def __init__(self, path: Path, *, default_registration_mode: str = "approval") -> None:
        self.path = Path(path)
        self.default_registration_mode = (
            default_registration_mode if default_registration_mode in REGISTRATION_MODES else "approval"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._restrict_permissions()
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)

    def _restrict_permissions(self) -> None:
        """Owner-only access: the file holds password hashes. SQLite gives the
        -wal and -shm files the database's mode, so they follow it."""

        self.path.touch(mode=0o600, exist_ok=True)
        for path in (self.path, Path(f"{self.path}-wal"), Path(f"{self.path}-shm")):
            if path.exists() and path.stat().st_mode & 0o077:
                os.chmod(path, 0o600)

    @contextmanager
    def _connect(self):
        """One connection per operation, committed on success, always closed."""

        with closing(sqlite3.connect(self.path, timeout=10)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            with conn:
                yield conn

    # Users -----------------------------------------------------------------

    def create_user(
        self, email: str, password: str, *, status: str = "active", is_admin: bool = False, max_pending: int | None = None
    ) -> User:
        """max_pending: refuse a pending account when that many already wait. Checked
        in the INSERT itself, so parallel registrations cannot all slip past it."""

        email = normalize_email(email)
        validate_password(password)
        if status not in STATUSES:
            raise AccountError(f"Unknown status: {status}")
        password_hash = _hash_password(password)
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, password_hash, status, is_admin, created_at) "
                    "SELECT ?, ?, ?, ?, ? WHERE ? IS NULL OR ? != 'pending' "
                    "OR (SELECT COUNT(*) FROM users WHERE status = 'pending') < ?",
                    (email, password_hash, status, int(is_admin), _iso(_now()), max_pending, status, max_pending),
                )
                if cursor.rowcount == 0:
                    raise TooManyPendingError("Na schválení už čeká příliš mnoho registrací.")
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise AccountError("Účet s tímto e-mailem už existuje.") from exc
        # With the hash, the first session (open registration) is created under the
        # same check as a login's: only while the account is unchanged and active.
        return User(id=user_id, email=email, status=status, is_admin=is_admin, password_hash=password_hash)

    def get_user(self, user_id: int) -> User | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user(row) if row else None

    def find_user(self, email: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
        return _user(row) if row else None

    def authenticate(self, email: str, password: str) -> User | None:
        """The user when the password matches, whatever their status; else None."""

        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
        if row is None:
            _verify_and_update(password or "", _DUMMY_HASH)
            return None
        checked_hash = row["password_hash"]
        valid, updated_hash = _verify_and_update(password or "", checked_hash)
        if not valid:
            return None
        with self._connect() as conn:
            # The recommended hashing parameters changed since this hash was made.
            # Only replace it if nobody set a new password during the check.
            if updated_hash and conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ? AND password_hash = ?",
                (updated_hash, row["id"], checked_hash),
            ).rowcount:
                checked_hash = updated_hash
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_iso(_now()), row["id"]))
        user = _user(row)
        return User(user.id, user.email, user.status, user.is_admin, password_hash=checked_hash)

    def set_password(
        self, user_id: int, password: str, *, keep_session: str | None = None, replaces: str | None = None
    ) -> bool:
        """Change the password and end every session except `keep_session`.

        With `replaces` (the hash the user's current password was checked
        against), change it only if that is still the stored hash, so a change
        started before an admin reset cannot overwrite it. False when refused.
        """

        validate_password(password)
        password_hash = _hash_password(password)
        with self._connect() as conn:
            if replaces is None:
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            elif not conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ? AND password_hash = ?",
                (password_hash, user_id, replaces),
            ).rowcount:
                return False
            conn.execute(
                "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
                (user_id, _token_hash(keep_session) if keep_session else ""),
            )
        return True

    def update_user(self, user_id: int, *, status: str | None = None, is_admin: bool | None = None) -> None:
        if status is not None and status not in STATUSES:
            raise AccountError(f"Unknown status: {status}")
        with self._connect() as conn:
            if status is not None:
                conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
                if status != "active":
                    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            if is_admin is not None:
                conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (int(is_admin), user_id))

    def count_users(self, status: str) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM users WHERE status = ?", (status,)).fetchone()[0]

    def delete_user(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def list_users(self, day: str | None = None) -> list[dict[str, object]]:
        """Every user with today's and all-time request counts, newest first."""

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.email, u.status, u.is_admin, u.created_at, u.last_login_at,
                       COALESCE(SUM(CASE WHEN d.day = ? THEN d.requests END), 0) AS requests_today,
                       COALESCE(SUM(d.requests), 0) AS requests_total
                FROM users u LEFT JOIN daily_usage d ON d.user_id = u.id
                GROUP BY u.id
                ORDER BY u.created_at DESC, u.id DESC
                """,
                (day or quota_day(),),
            ).fetchall()
        return [{**dict(row), "is_admin": bool(row["is_admin"])} for row in rows]

    # Sessions --------------------------------------------------------------

    def create_session(self, user_id: int, lifetime: timedelta, *, password_hash: str | None = None) -> str | None:
        """A new session token, or None when `password_hash` is given and is no
        longer the user's, or the user is no longer active.

        A login checks the password against a hash read before the (slow)
        check; a password reset or a block during it must not let it through.
        """

        token = secrets.token_urlsafe(32)
        now = _now()
        values = (_token_hash(token), _iso(now), _iso(now + lifetime), user_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (_iso(now),))
            if password_hash is None:
                conn.execute(
                    "INSERT INTO sessions (token_hash, created_at, expires_at, user_id) VALUES (?, ?, ?, ?)", values
                )
                return token
            inserted = conn.execute(
                """
                INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
                SELECT ?, id, ?, ? FROM users WHERE id = ? AND password_hash = ? AND status = 'active'
                """,
                (*values, password_hash),
            ).rowcount
        return token if inserted else None

    def session_user(self, token: str | None) -> User | None:
        """The active user behind a live session token, else None."""

        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ? AND u.status = 'active'
                """,
                (_token_hash(token), _iso(_now())),
            ).fetchone()
        return _user(row) if row else None

    def delete_session(self, token: str | None) -> None:
        if not token:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))

    # Daily quota -----------------------------------------------------------

    def consume_request(self, user: User, limit: int, day: str | None = None) -> int | None:
        """Count one request; return how many remain today, or None when over the limit.

        Admins and a limit of 0 are unlimited, but still counted for the
        statistics; they get -1 back. The check and the increment are one
        statement, so two parallel requests cannot both take the last slot.
        """

        day = day or quota_day()
        unlimited = user.is_admin or limit <= 0
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO daily_usage (user_id, day, requests) VALUES (?, ?, 1)
                ON CONFLICT (user_id, day) DO UPDATE SET requests = requests + 1
                WHERE ? OR requests < ?
                RETURNING requests
                """,
                (user.id, day, int(unlimited), limit),
            ).fetchone()
        if row is None or (not unlimited and row["requests"] > limit):
            return None
        return -1 if unlimited else limit - row["requests"]

    def requests_today(self, user_id: int, day: str | None = None) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT requests FROM daily_usage WHERE user_id = ? AND day = ?",
                (user_id, day or quota_day()),
            ).fetchone()
        return row["requests"] if row else 0

    # Settings --------------------------------------------------------------

    def registration_mode(self) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = 'registration_mode'").fetchone()
        mode = row["value"] if row else self.default_registration_mode
        return mode if mode in REGISTRATION_MODES else self.default_registration_mode

    def set_registration_mode(self, mode: str) -> None:
        if mode not in REGISTRATION_MODES:
            raise AccountError(f"Unknown registration mode: {mode}")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES ('registration_mode', ?) "
                "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                (mode,),
            )


class LoginThrottle:
    """Refuse further logins for an email after repeated wrong passwords.

    In memory: the app runs as one process, and a restart forgetting the
    counts only gives an attacker a few more guesses against Argon2.
    """

    def __init__(self, max_failures: int = 5, lockout_seconds: float = 300, max_entries: int = 10_000) -> None:
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        # Failures for many made-up emails must not grow the table without bound.
        self.max_entries = max_entries
        self._failures: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, key: str, now: float | None = None) -> float:
        """Seconds until `key` may try again; 0 when it may try now."""

        now = time.monotonic() if now is None else now
        with self._lock:
            return self._retry_after(key, now)

    def begin(self, key: str, now: float | None = None) -> float:
        """Start an attempt: the seconds to wait, or 0 after counting it as a
        failure until `succeeded()`. Counting before the (slow) password check
        stops parallel requests from all passing before any failure is recorded.
        """

        now = time.monotonic() if now is None else now
        with self._lock:
            wait = self._retry_after(key, now)
            if not wait:
                self._record(key, now)
            return wait

    def failed(self, key: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        with self._lock:
            self._record(key, now)

    def _retry_after(self, key: str, now: float) -> float:
        count, last = self._failures.get(key, (0, 0.0))
        if count < self.max_failures:
            return 0.0
        remaining = last + self.lockout_seconds - now
        if remaining <= 0:
            # Lockout over: allow one fresh round of attempts.
            self._failures.pop(key, None)
            return 0.0
        return remaining

    def _record(self, key: str, now: float) -> None:
        # Failures older than a lockout are forgotten, locked or not.
        self._failures = {
            other: entry for other, entry in self._failures.items() if now - entry[1] < self.lockout_seconds
        }
        count, _ = self._failures.get(key, (0, 0.0))
        if key not in self._failures and len(self._failures) >= self.max_entries:
            oldest = min(self._failures, key=lambda other: self._failures[other][1])
            del self._failures[oldest]
        self._failures[key] = (count + 1, now)

    def succeeded(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


class RateWindow:
    """Allow at most `limit` events per sliding `window_seconds`, server-wide."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self, now: float | None = None) -> bool:
        """Record an event and return True, or False when the window is full."""

        now = time.monotonic() if now is None else now
        with self._lock:
            if self._full(now):
                return False
            self._events.append(now)
            return True

    def full(self, now: float | None = None) -> bool:
        """True when the window is full; records nothing."""

        now = time.monotonic() if now is None else now
        with self._lock:
            return self._full(now)

    def record(self, now: float | None = None) -> None:
        """Record an event that already happened, even over the limit."""

        now = time.monotonic() if now is None else now
        with self._lock:
            self._full(now)
            self._events.append(now)

    def _full(self, now: float) -> bool:
        while self._events and now - self._events[0] >= self.window_seconds:
            self._events.popleft()
        return len(self._events) >= self.limit
