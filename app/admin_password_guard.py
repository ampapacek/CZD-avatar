"""Server-wide limit on wrong shared ADMIN_PASSWORD attempts.

Counted for the whole server, not per client: without accounts there is no
reliable identity to count by. The cost is that someone guessing can keep the
shared password blocked for everyone; logged-in admin accounts are not affected.
"""

from __future__ import annotations

import hashlib
import hmac
import threading
import time


class AdminPasswordGuard:
    """Block the shared password for a while after too many wrong guesses.

    Repeating the same wrong value counts once, so a stale password left in a
    browser (sent with every request) does not use up the attempts. In memory:
    a restart clears the count.
    """

    def __init__(self, max_failures: int = 10, window_seconds: float = 600, lockout_seconds: float = 600) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._failures: dict[str, float] = {}
        self._locked_until = 0.0
        self._lock = threading.Lock()

    def retry_after(self, now: float | None = None) -> float:
        """Seconds until the shared password is accepted again; 0 when it is now."""

        now = time.monotonic() if now is None else now
        with self._lock:
            return max(self._locked_until - now, 0.0)

    def check(self, password: str, expected: str, now: float | None = None) -> tuple[bool, float]:
        """(matches, seconds locked). Checked and counted under one lock, so a
        burst of parallel guesses cannot all slip in before the lock engages.
        While locked, nothing is compared: (False, seconds left).
        """

        now = time.monotonic() if now is None else now
        with self._lock:
            wait = max(self._locked_until - now, 0.0)
            if wait:
                return False, wait
            if hmac.compare_digest(password.encode("utf-8"), expected.encode("utf-8")):
                return True, 0.0
            self._record(password, now)
            return False, 0.0

    def failed(self, password: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        with self._lock:
            self._record(password, now)

    def _record(self, password: str, now: float) -> None:
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self._failures = {key: seen for key, seen in self._failures.items() if now - seen < self.window_seconds}
        self._failures[digest] = now
        if len(self._failures) >= self.max_failures:
            self._locked_until = now + self.lockout_seconds
            self._failures.clear()

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()
            self._locked_until = 0.0
