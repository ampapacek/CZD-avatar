import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.admin_password_guard import AdminPasswordGuard


class AdminPasswordGuardTests(unittest.TestCase):
    def test_locks_after_distinct_wrong_guesses_and_unlocks_later(self) -> None:
        guard = AdminPasswordGuard(max_failures=3, window_seconds=60, lockout_seconds=100)
        for index in range(3):
            self.assertEqual(guard.retry_after(now=index), 0)
            guard.failed(f"guess {index}", now=index)
        self.assertEqual(guard.retry_after(now=3), 99)
        self.assertEqual(guard.retry_after(now=102), 0)

    def test_repeating_one_wrong_value_counts_once(self) -> None:
        # A stale password stored in a browser is sent with every request.
        guard = AdminPasswordGuard(max_failures=3)
        for index in range(10):
            guard.failed("stale", now=index)
        self.assertEqual(guard.retry_after(now=10), 0)

    def test_old_failures_leave_the_window(self) -> None:
        guard = AdminPasswordGuard(max_failures=3, window_seconds=60)
        guard.failed("a", now=0)
        guard.failed("b", now=1)
        guard.failed("c", now=100)
        self.assertEqual(guard.retry_after(now=100), 0)

    def test_check_compares_and_counts_in_one_step(self) -> None:
        guard = AdminPasswordGuard(max_failures=2, lockout_seconds=100)
        self.assertEqual(guard.check("s3cret", "s3cret", now=0), (True, 0.0))
        self.assertEqual(guard.check("a", "s3cret", now=1), (False, 0.0))
        self.assertEqual(guard.check("b", "s3cret", now=2), (False, 0.0))
        self.assertEqual(guard.check("s3cret", "s3cret", now=3), (False, 99))


class SharedPasswordEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patches = [
            patch.object(main.settings, "admin_password", "s3cret"),
            patch.object(main, "admin_password_guard", AdminPasswordGuard(max_failures=3)),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()

    def unlock(self, password: str):
        return self.client.post("/unlock", json={"password": password})

    def test_unlock_is_blocked_after_wrong_guesses_even_for_the_right_password(self) -> None:
        self.assertTrue(self.unlock("s3cret").json()["unlocked"])
        for index in range(3):
            self.assertFalse(self.unlock(f"guess {index}").json()["unlocked"])
        response = self.unlock("s3cret")
        self.assertEqual(response.status_code, 429)
        self.assertIn("zablokované", response.json()["detail"])

    def test_other_admin_password_endpoints_share_the_limit(self) -> None:
        for index in range(3):
            self.client.delete("/prompt-presets/builtin-overrides/x", params={"admin_password": f"guess {index}"})
        response = self.client.delete("/prompt-presets/builtin-overrides/x", params={"admin_password": "s3cret"})
        self.assertEqual(response.status_code, 429)

    def test_stale_password_with_public_model_is_not_a_guess(self) -> None:
        for index in range(5):
            main._resolve_llm_request(main.ChatRequest(question="x", model="test-model", admin_password=f"old {index}"))
        self.assertTrue(self.unlock("s3cret").json()["unlocked"])

    def test_missing_password_is_not_a_guess(self) -> None:
        for _ in range(5):
            self.unlock("")
        self.assertTrue(self.unlock("s3cret").json()["unlocked"])
