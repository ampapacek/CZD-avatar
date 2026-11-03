import os
import stat
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from app.accounts import AccountError, AccountStore, TooManyPendingError, LoginThrottle, RateWindow, normalize_email, quota_day
from scripts import users as users_cli


class EmailValidationTests(unittest.TestCase):
    def test_accepts_and_lowercases_ordinary_addresses(self) -> None:
        self.assertEqual(normalize_email("  Jan.Novak@Seznam.CZ "), "jan.novak@seznam.cz")
        self.assertEqual(normalize_email("a+tag@mff.cuni.cz"), "a+tag@mff.cuni.cz")

    def test_rejects_malformed_addresses(self) -> None:
        for email in ("", "jan", "jan@", "@seznam.cz", "jan@seznam", "jan@seznam.c", "jan@@seznam.cz",
                      "jan novak@seznam.cz", "jan@.cz", "jan@seznam..cz", "jan@seznam.cz.", "a" * 250 + "@x.cz"):
            with self.subTest(email=email), self.assertRaises(AccountError):
                normalize_email(email)


class AccountStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_database_is_readable_by_the_owner_only(self) -> None:
        path = Path(self.tmp.name) / "fresh.sqlite3"
        old_umask = os.umask(0o002)
        try:
            store = AccountStore(path)
            store.create_user("jan@seznam.cz", "user password")
        finally:
            os.umask(old_umask)
        for file in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
            if file.exists():
                self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600, file.name)
        # An existing database from before is tightened on start.
        os.chmod(path, 0o644)
        AccountStore(path)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_ids_of_deleted_accounts_are_not_reused(self) -> None:
        # Otherwise an admin acting on a list loaded before the deletion would
        # change whoever registered next.
        first = self.store.create_user("a@seznam.cz", "user password")
        self.store.delete_user(first.id)
        second = self.store.create_user("b@seznam.cz", "user password")
        self.assertGreater(second.id, first.id)

    def test_pending_cap_is_checked_in_the_insert(self) -> None:
        self.store.create_user("a@seznam.cz", "user password", status="pending", max_pending=1)
        with self.assertRaises(TooManyPendingError):
            self.store.create_user("b@seznam.cz", "user password", status="pending", max_pending=1)
        # Active accounts and calls without a cap are not limited.
        self.store.create_user("c@seznam.cz", "user password", max_pending=1)
        self.store.create_user("d@seznam.cz", "user password", status="pending")
        self.assertEqual(self.store.count_users("pending"), 2)

    def test_create_and_authenticate(self) -> None:
        user = self.store.create_user("Jan@Seznam.cz", "correct horse")
        self.assertEqual(user.email, "jan@seznam.cz")
        self.assertEqual(self.store.authenticate("JAN@seznam.cz", "correct horse"), user)
        self.assertIsNone(self.store.authenticate("jan@seznam.cz", "wrong password"))
        self.assertIsNone(self.store.authenticate("nobody@seznam.cz", "correct horse"))

    def test_rejects_duplicates_and_short_passwords(self) -> None:
        self.store.create_user("jan@seznam.cz", "correct horse")
        with self.assertRaisesRegex(AccountError, "už existuje"):
            self.store.create_user("JAN@seznam.cz", "another password")
        with self.assertRaisesRegex(AccountError, "alespoň"):
            self.store.create_user("eva@seznam.cz", "short")

    def test_password_is_not_stored_in_plain_text(self) -> None:
        self.store.create_user("jan@seznam.cz", "correct horse")
        self.assertNotIn(b"correct horse", (Path(self.tmp.name) / "users.sqlite3").read_bytes())

    def test_sessions_need_an_active_user_and_end_on_status_change(self) -> None:
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        token = self.store.create_session(user.id, timedelta(days=1))
        self.assertEqual(self.store.session_user(token), user)
        self.assertIsNone(self.store.session_user("forged"))
        self.store.update_user(user.id, status="disabled")
        self.assertIsNone(self.store.session_user(token))
        self.store.update_user(user.id, status="active")
        # Blocking ended the session for good, not just while blocked.
        self.assertIsNone(self.store.session_user(token))

    def test_expired_session_is_rejected(self) -> None:
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        token = self.store.create_session(user.id, timedelta(seconds=-1))
        self.assertIsNone(self.store.session_user(token))

    def test_set_password_keeps_only_the_current_session(self) -> None:
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        current = self.store.create_session(user.id, timedelta(days=1))
        other = self.store.create_session(user.id, timedelta(days=1))
        self.store.set_password(user.id, "new password", keep_session=current)
        self.assertEqual(self.store.session_user(current), user)
        self.assertIsNone(self.store.session_user(other))
        self.assertIsNotNone(self.store.authenticate("jan@seznam.cz", "new password"))

    def test_session_needs_the_checked_password_to_be_current(self) -> None:
        self.store.create_user("jan@seznam.cz", "correct horse")
        checked = self.store.authenticate("jan@seznam.cz", "correct horse")
        self.assertIsNotNone(self.store.create_session(checked.id, timedelta(days=1), password_hash=checked.password_hash))
        self.store.set_password(checked.id, "new password")
        self.assertIsNone(self.store.create_session(checked.id, timedelta(days=1), password_hash=checked.password_hash))

    def test_set_password_can_require_the_checked_hash(self) -> None:
        self.store.create_user("jan@seznam.cz", "correct horse")
        checked = self.store.authenticate("jan@seznam.cz", "correct horse")
        self.store.set_password(checked.id, "admin chosen")
        self.assertFalse(self.store.set_password(checked.id, "user chosen", replaces=checked.password_hash))
        self.assertIsNotNone(self.store.authenticate("jan@seznam.cz", "admin chosen"))

    def test_daily_quota(self) -> None:
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        self.assertEqual(self.store.consume_request(user, 2, day="2026-11-12"), 1)
        self.assertEqual(self.store.consume_request(user, 2, day="2026-11-12"), 0)
        self.assertIsNone(self.store.consume_request(user, 2, day="2026-11-12"))
        self.assertEqual(self.store.requests_today(user.id, day="2026-11-12"), 2)
        # A new day starts from zero.
        self.assertEqual(self.store.consume_request(user, 2, day="2026-11-13"), 1)

    def test_admins_and_zero_limit_are_unlimited_but_counted(self) -> None:
        admin = self.store.create_user("admin@seznam.cz", "correct horse", is_admin=True)
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        for _ in range(3):
            self.assertEqual(self.store.consume_request(admin, 1, day="2026-11-12"), -1)
            self.assertEqual(self.store.consume_request(user, 0, day="2026-11-12"), -1)
        self.assertEqual(self.store.requests_today(admin.id, day="2026-11-12"), 3)
        rows = {row["email"]: row for row in self.store.list_users(day="2026-11-12")}
        self.assertEqual(rows["jan@seznam.cz"]["requests_today"], 3)
        self.assertEqual(rows["jan@seznam.cz"]["requests_total"], 3)

    def test_delete_removes_sessions_and_usage(self) -> None:
        user = self.store.create_user("jan@seznam.cz", "correct horse")
        token = self.store.create_session(user.id, timedelta(days=1))
        self.store.consume_request(user, 10)
        self.store.delete_user(user.id)
        self.assertIsNone(self.store.session_user(token))
        self.assertEqual(self.store.requests_today(user.id), 0)

    def test_registration_mode_defaults_and_persists(self) -> None:
        self.assertEqual(self.store.registration_mode(), "approval")
        self.store.set_registration_mode("open")
        reopened = AccountStore(self.store.path)
        self.assertEqual(reopened.registration_mode(), "open")
        with self.assertRaises(AccountError):
            self.store.set_registration_mode("anyone")

    def test_quota_day_uses_prague_midnight(self) -> None:
        from datetime import datetime, timezone

        # 23:30 UTC on 11 Nov is already 12 Nov in Prague (UTC+1 in November).
        self.assertEqual(quota_day(datetime(2026, 11, 11, 23, 30, tzinfo=timezone.utc)), "2026-11-12")


class LoginThrottleTests(unittest.TestCase):
    def test_locks_after_repeated_failures_and_unlocks_later(self) -> None:
        throttle = LoginThrottle(max_failures=3, lockout_seconds=60)
        for _ in range(3):
            self.assertEqual(throttle.retry_after("jan", now=0), 0)
            throttle.failed("jan", now=0)
        self.assertAlmostEqual(throttle.retry_after("jan", now=10), 50)
        self.assertEqual(throttle.retry_after("eva", now=10), 0)
        self.assertEqual(throttle.retry_after("jan", now=61), 0)

    def test_success_resets_the_count(self) -> None:
        throttle = LoginThrottle(max_failures=2, lockout_seconds=60)
        throttle.failed("jan", now=0)
        throttle.succeeded("jan")
        throttle.failed("jan", now=0)
        self.assertEqual(throttle.retry_after("jan", now=0), 0)

    def test_old_failures_are_forgotten_and_the_table_is_bounded(self) -> None:
        throttle = LoginThrottle(max_failures=2, lockout_seconds=60, max_entries=3)
        for index in range(100):
            throttle.failed(f"user{index}", now=0)
        self.assertEqual(len(throttle._failures), 3)
        throttle.failed("late", now=100)
        self.assertEqual(list(throttle._failures), ["late"])
        # A failure from long ago no longer counts towards a lock.
        throttle.failed("late", now=200)
        self.assertEqual(throttle.retry_after("late", now=200), 0)


class LoginThrottleBeginTests(unittest.TestCase):
    def test_begin_counts_the_attempt_before_the_check(self) -> None:
        throttle = LoginThrottle(max_failures=3, lockout_seconds=60)
        # Three attempts started in parallel, none finished yet.
        self.assertEqual([throttle.begin("jan", now=0) for _ in range(3)], [0, 0, 0])
        self.assertAlmostEqual(throttle.begin("jan", now=1), 59)
        throttle.succeeded("jan")
        self.assertEqual(throttle.begin("jan", now=2), 0)


class RateWindowTests(unittest.TestCase):
    def test_allows_up_to_the_limit_per_window(self) -> None:
        window = RateWindow(limit=2, window_seconds=60)
        self.assertTrue(window.allow(now=0))
        self.assertTrue(window.allow(now=10))
        self.assertFalse(window.allow(now=20))
        self.assertTrue(window.allow(now=61))

    def test_full_checks_and_record_counts(self) -> None:
        window = RateWindow(limit=2, window_seconds=60)
        self.assertFalse(window.full(now=0))
        window.record(now=0)
        window.record(now=1)
        self.assertTrue(window.full(now=2))
        self.assertFalse(window.full(now=60))


class UsersCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "users.sqlite3"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_admin_then_promote_and_reset(self) -> None:
        self.assertEqual(users_cli.main(["--db", str(self.db), "create-admin", "Admin@Seznam.cz", "--password", "secret123"]), 0)
        store = AccountStore(self.db)
        admin = store.authenticate("admin@seznam.cz", "secret123")
        self.assertTrue(admin.is_admin)

        # Someone registered the address first; promoting must not keep their password.
        pending = store.create_user("jan@seznam.cz", "attacker password", status="pending")
        store.update_user(pending.id, status="active")
        attacker_session = store.create_session(pending.id, timedelta(days=1))
        self.assertEqual(
            users_cli.main(["--db", str(self.db), "create-admin", "jan@seznam.cz", "--password", "admin chosen"]), 0
        )
        promoted = store.get_user(pending.id)
        self.assertEqual((promoted.status, promoted.is_admin), ("active", True))
        self.assertIsNone(store.authenticate("jan@seznam.cz", "attacker password"))
        self.assertIsNotNone(store.authenticate("jan@seznam.cz", "admin chosen"))
        self.assertIsNone(store.session_user(attacker_session))

        self.assertEqual(users_cli.main(["--db", str(self.db), "set-password", "jan@seznam.cz", "--password", "new password"]), 0)
        self.assertIsNotNone(store.authenticate("jan@seznam.cz", "new password"))

    def test_unknown_user_fails(self) -> None:
        self.assertEqual(users_cli.main(["--db", str(self.db), "set-password", "nobody@seznam.cz", "--password", "x" * 8]), 1)


if __name__ == "__main__":
    unittest.main()
