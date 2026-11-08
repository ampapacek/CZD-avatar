import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import auth, main
from app.accounts import AccountStore, LoginThrottle, RateWindow


class AuthTestCase(unittest.TestCase):
    """Accounts on, against a throwaway database and a 2-request daily limit."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        auth.set_store(self.store)
        self.patches = [
            patch.object(main.settings, "auth_enabled", True),
            patch.object(main.settings, "user_daily_request_limit", 2),
            patch.object(main.settings, "admin_password", ""),
            patch.object(auth, "login_throttle", LoginThrottle()),
            patch.object(auth, "registration_rate", RateWindow(100, 600)),
            patch.object(auth, "failed_login_rate", RateWindow(100, 60)),
            patch.object(main.pipeline, "retrieve_with_baseline", lambda *args, **kwargs: ([], [])),
        ]
        for item in self.patches:
            item.start()
        # https: the session cookie is Secure and is never sent over plain http.
        self.client = TestClient(main.app, base_url="https://testserver")
        self.admin = self.store.create_user("admin@seznam.cz", "admin password", is_admin=True)
        self.user = self.store.create_user("jan@seznam.cz", "user password")

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        auth.set_store(None)
        self.tmp.cleanup()

    def login(self, email: str, password: str, client: TestClient | None = None):
        return (client or self.client).post("/auth/login", json={"email": email, "password": password})


class GateTests(AuthTestCase):
    def test_logged_out_visitor_is_sent_to_login(self) -> None:
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "login")
        shared = self.client.get("/?shared=abc", follow_redirects=False)
        self.assertEqual(shared.headers["location"], "login?shared=abc")
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.post("/retrieve", json={"question": "Cokoliv?"}).status_code, 401)
        self.assertEqual(self.client.get("/prompt-presets").status_code, 401)

    def test_health_settings_and_static_stay_public(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        settings = self.client.get("/settings").json()
        self.assertEqual(settings["account"]["enabled"], True)
        self.assertIsNone(settings["account"]["user"])
        self.assertEqual(self.client.get("/static/styles.css").status_code, 200)

    def test_login_opens_the_app_and_logout_closes_it(self) -> None:
        response = self.login("JAN@seznam.cz", "user password")
        self.assertEqual(response.status_code, 200, response.text)
        cookie = response.headers["set-cookie"].lower()
        for flag in ("httponly", "secure", "samesite=lax", "path=/"):
            self.assertIn(flag, cookie)
        self.assertEqual(self.client.get("/", follow_redirects=False).status_code, 200)
        self.assertEqual(self.client.get("/login", follow_redirects=False).status_code, 303)
        self.assertEqual(self.client.get("/auth/me").json()["user"]["email"], "jan@seznam.cz")

        self.client.post("/auth/logout")
        self.assertEqual(self.client.get("/prompt-presets").status_code, 401)

    def test_wrong_password_pending_and_disabled_users_cannot_log_in(self) -> None:
        self.assertEqual(self.login("jan@seznam.cz", "wrong password").status_code, 401)
        self.assertEqual(self.login("nobody@seznam.cz", "user password").status_code, 401)
        self.store.create_user("eva@seznam.cz", "user password", status="pending")
        response = self.login("eva@seznam.cz", "user password")
        self.assertEqual(response.status_code, 403)
        self.assertIn("schválení", response.json()["detail"])
        self.store.update_user(self.user.id, status="disabled")
        self.assertEqual(self.login("jan@seznam.cz", "user password").status_code, 403)

    def test_repeated_failures_lock_the_login(self) -> None:
        for _ in range(5):
            self.login("jan@seznam.cz", "wrong password")
        response = self.login("jan@seznam.cz", "user password")
        self.assertEqual(response.status_code, 429)

    def test_failed_logins_are_limited_for_the_whole_server(self) -> None:
        with patch.object(auth, "failed_login_rate", RateWindow(2, 60)):
            # A new email each time, so the per-email lockout never triggers.
            self.assertEqual(self.login("a@seznam.cz", "wrong password").status_code, 401)
            self.assertEqual(self.login("b@seznam.cz", "wrong password").status_code, 401)
            with patch.object(self.store, "authenticate", side_effect=AssertionError("password checked")):
                self.assertEqual(self.login("jan@seznam.cz", "user password").status_code, 429)

    def test_password_reset_during_login_check_refuses_the_login(self) -> None:
        authenticate = self.store.authenticate

        def reset_after_check(email, password):
            user = authenticate(email, password)
            self.store.set_password(self.user.id, "admin chosen")
            return user

        with patch.object(self.store, "authenticate", side_effect=reset_after_check):
            response = self.login("jan@seznam.cz", "user password")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get("/prompt-presets").status_code, 401)

    def test_block_during_login_check_refuses_the_login(self) -> None:
        authenticate = self.store.authenticate

        def block_after_check(email, password):
            user = authenticate(email, password)
            self.store.update_user(self.user.id, status="disabled")
            return user

        with patch.object(self.store, "authenticate", side_effect=block_after_check):
            self.assertEqual(self.login("jan@seznam.cz", "user password").status_code, 401)

    def test_lone_surrogates_are_refused_not_a_crash(self) -> None:
        # Raw JSON: valid JSON, but the string cannot be encoded as UTF-8.
        for body in (
            '{"email": "jan@seznam.cz", "password": "\\ud800abcdefgh"}',
            '{"email": "\\ud800@seznam.cz", "password": "user password"}',
        ):
            for path in ("/auth/login", "/auth/register"):
                response = self.client.post(path, content=body, headers={"Content-Type": "application/json"})
                self.assertEqual(response.status_code, 422, (path, body))

    def test_parallel_wrong_passwords_hit_the_lockout(self) -> None:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=10) as pool:
            codes = list(pool.map(lambda _: self.login("jan@seznam.cz", "wrong password").status_code, range(10)))
        self.assertEqual(codes.count(401), 5)
        self.assertEqual(codes.count(429), 5)

    def test_disabling_a_user_ends_their_session(self) -> None:
        self.login("jan@seznam.cz", "user password")
        self.store.update_user(self.user.id, status="disabled")
        self.assertEqual(self.client.get("/prompt-presets").status_code, 401)


class QuotaTests(AuthTestCase):
    def test_counted_endpoints_stop_at_the_daily_limit(self) -> None:
        self.login("jan@seznam.cz", "user password")
        first = self.client.post("/retrieve", json={"question": "Cokoliv?"})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.headers[auth.QUOTA_HEADER], "1")
        second = self.client.post("/retrieve/stream", json={"question": "Cokoliv?"})
        self.assertEqual(second.headers[auth.QUOTA_HEADER], "0")
        third = self.client.post("/retrieve", json={"question": "Cokoliv?"})
        self.assertEqual(third.status_code, 429)
        self.assertIn("limit", third.json()["detail"])
        self.assertEqual(self.client.post("/chat", json={"question": "Cokoliv?"}).status_code, 429)

    def test_query_transform_is_counted(self) -> None:
        # It calls the LLM, so it must not be a way around the limit.
        self.login("jan@seznam.cz", "user password")
        for _ in range(2):
            self.client.post("/query-transform", json={"question": "Cokoliv?"})
        response = self.client.post("/query-transform", json={"question": "Cokoliv?"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(self.store.requests_today(self.user.id), 2)

    def test_other_endpoints_are_not_counted(self) -> None:
        self.login("jan@seznam.cz", "user password")
        for _ in range(3):
            self.client.get("/prompt-presets")
            self.client.get("/settings")
        self.assertEqual(self.store.requests_today(self.user.id), 0)
        self.assertEqual(self.client.get("/auth/me").json()["requests_remaining"], 2)

    def test_admin_is_not_limited(self) -> None:
        self.login("admin@seznam.cz", "admin password")
        for _ in range(3):
            response = self.client.post("/retrieve", json={"question": "Cokoliv?"})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers[auth.QUOTA_HEADER], "-1")
        self.assertIsNone(self.client.get("/auth/me").json()["requests_remaining"])


class RegistrationTests(AuthTestCase):
    def register(self, email: str = "eva@seznam.cz", password: str = "eva password"):
        return self.client.post("/auth/register", json={"email": email, "password": password})

    def test_approval_mode_creates_a_pending_account(self) -> None:
        response = self.register()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["pending"])
        self.assertNotIn("set-cookie", response.headers)
        self.assertEqual(self.store.find_user("eva@seznam.cz").status, "pending")

    def test_open_mode_logs_the_new_user_in(self) -> None:
        self.store.set_registration_mode("open")
        response = self.register()
        self.assertFalse(response.json()["pending"])
        self.assertEqual(self.client.get("/auth/me").json()["user"]["email"], "eva@seznam.cz")

    def test_open_registration_session_is_checked_like_a_login(self) -> None:
        # The first session must not outlive a reset or deletion that lands
        # between creating the account and starting its session.
        self.store.set_registration_mode("open")
        create_user = self.store.create_user

        def delete_after_create(*args, **kwargs):
            user = create_user(*args, **kwargs)
            self.store.delete_user(user.id)
            return user

        with patch.object(self.store, "create_user", side_effect=delete_after_create):
            self.assertEqual(self.register().status_code, 401)
        self.assertIsNone(self.client.get("/auth/me").json()["user"])

    def test_closed_mode_refuses(self) -> None:
        self.store.set_registration_mode("closed")
        self.assertEqual(self.register().status_code, 403)
        self.assertIsNone(self.store.find_user("eva@seznam.cz"))

    def test_invalid_or_taken_email_and_short_password(self) -> None:
        self.assertEqual(self.register(email="eva@seznam").status_code, 400)
        self.assertEqual(self.register(email="JAN@seznam.cz").status_code, 400)
        self.assertEqual(self.register(password="short").status_code, 400)

    def test_registrations_are_rate_limited(self) -> None:
        self.store.set_registration_mode("open")
        with patch.object(auth, "registration_rate", RateWindow(2, 600)):
            self.assertEqual(self.register("a@seznam.cz").status_code, 200)
            self.assertEqual(self.register("b@seznam.cz").status_code, 200)
            response = self.register("c@seznam.cz")
        self.assertEqual(response.status_code, 429)
        self.assertIsNone(self.store.find_user("c@seznam.cz"))

    def test_pending_accounts_are_capped(self) -> None:
        with patch.object(auth, "MAX_PENDING_USERS", 1):
            self.assertEqual(self.register("a@seznam.cz").status_code, 200)
            self.assertEqual(self.register("b@seznam.cz").status_code, 429)
            # Open mode creates active accounts, so the pending cap does not apply.
            self.store.set_registration_mode("open")
            self.assertEqual(self.register("c@seznam.cz").status_code, 200)

    def test_pending_cap_holds_when_parallel_requests_pass_the_precheck(self) -> None:
        # Every request saw a free slot in the cheap precheck; the INSERT decides.
        with patch.object(auth, "MAX_PENDING_USERS", 1), patch.object(self.store, "count_users", return_value=0):
            self.assertEqual(self.register("a@seznam.cz").status_code, 200)
            self.assertEqual(self.register("b@seznam.cz").status_code, 429)
        self.assertIsNone(self.store.find_user("b@seznam.cz"))

    def test_change_own_password(self) -> None:
        self.login("jan@seznam.cz", "user password")
        wrong = self.client.post("/auth/password", json={"current_password": "nope", "new_password": "new password"})
        self.assertEqual(wrong.status_code, 400)
        response = self.client.post(
            "/auth/password", json={"current_password": "user password", "new_password": "new password"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        # The session that changed it stays logged in.
        self.assertEqual(self.client.get("/prompt-presets").status_code, 200)
        self.assertIsNotNone(self.store.authenticate("jan@seznam.cz", "new password"))


class PasswordChangeRaceTests(AuthTestCase):
    def test_admin_reset_during_a_change_wins(self) -> None:
        self.assertEqual(self.login("jan@seznam.cz", "user password").status_code, 200)
        authenticate = self.store.authenticate

        def reset_after_check(email, password):
            user = authenticate(email, password)
            self.store.set_password(self.user.id, "admin chosen")
            return user

        with patch.object(self.store, "authenticate", side_effect=reset_after_check):
            response = self.client.post(
                "/auth/password", json={"current_password": "user password", "new_password": "user chosen"}
            )
        # The reset also ended the session that started the change.
        self.assertIn(response.status_code, (401, 409))
        self.assertIsNone(self.store.authenticate("jan@seznam.cz", "user chosen"))
        self.assertIsNotNone(self.store.authenticate("jan@seznam.cz", "admin chosen"))


class AdminTests(AuthTestCase):
    def test_regular_user_cannot_manage_users(self) -> None:
        self.login("jan@seznam.cz", "user password")
        self.assertEqual(self.client.get("/admin/users").status_code, 403)
        self.assertEqual(self.client.put("/admin/registration-mode", json={"mode": "open"}).status_code, 403)

    def test_admin_manages_users_and_registration(self) -> None:
        self.login("admin@seznam.cz", "admin password")
        listing = self.client.get("/admin/users").json()
        self.assertEqual({row["email"] for row in listing["users"]}, {"admin@seznam.cz", "jan@seznam.cz"})
        self.assertEqual(listing["daily_limit"], 2)

        self.assertEqual(self.client.patch(f"/admin/users/{self.user.id}", json={"status": "disabled"}).status_code, 200)
        self.assertEqual(self.store.get_user(self.user.id).status, "disabled")
        reset = self.client.post(f"/admin/users/{self.user.id}/password", json={"password": "reset password"})
        self.assertEqual(reset.status_code, 200)
        self.assertIsNotNone(self.store.authenticate("jan@seznam.cz", "reset password"))
        self.assertEqual(self.client.put("/admin/registration-mode", json={"mode": "closed"}).json(), {"registration_mode": "closed"})
        self.assertEqual(self.client.delete(f"/admin/users/{self.user.id}").status_code, 204)
        self.assertIsNone(self.store.get_user(self.user.id))
        self.assertEqual(self.client.delete("/admin/users/9999").status_code, 404)

    def test_admin_cannot_lock_themselves_out(self) -> None:
        self.login("admin@seznam.cz", "admin password")
        self.assertEqual(self.client.patch(f"/admin/users/{self.admin.id}", json={"status": "disabled"}).status_code, 400)
        self.assertEqual(self.client.patch(f"/admin/users/{self.admin.id}", json={"is_admin": False}).status_code, 400)
        self.assertEqual(self.client.delete(f"/admin/users/{self.admin.id}").status_code, 400)

    def test_logged_in_admin_needs_no_shared_password(self) -> None:
        # The built-in prompt override is guarded by the shared admin password.
        url = f"/prompt-presets/builtin-overrides/{main.load_wp_configs()[0].builtin_prompts[0].id}"
        with patch.object(main, "delete_builtin_prompt_override") as delete_override:
            self.login("jan@seznam.cz", "user password")
            self.assertEqual(self.client.delete(url).status_code, 403)
            self.client.post("/auth/logout")
            self.login("admin@seznam.cz", "admin password")
            self.assertEqual(self.client.delete(url).status_code, 204)
        delete_override.assert_called_once()

    def test_blocked_shared_password_does_not_stop_admin_accounts(self) -> None:
        url = f"/prompt-presets/builtin-overrides/{main.load_wp_configs()[0].builtin_prompts[0].id}"
        main.admin_password_guard._locked_until = float("inf")
        with patch.object(main.settings, "admin_password", "s3cret"), patch.object(main, "delete_builtin_prompt_override"):
            self.login("admin@seznam.cz", "admin password")
            self.assertEqual(self.client.delete(url, params={"admin_password": "s3cret"}).status_code, 204)


class AuthDisabledTests(unittest.TestCase):
    def test_app_is_open_and_account_endpoints_are_off(self) -> None:
        client = TestClient(main.app)
        self.assertFalse(main.settings.auth_enabled)
        self.assertEqual(client.get("/", follow_redirects=False).status_code, 200)
        self.assertEqual(client.get("/settings").json()["account"], {"enabled": False})
        self.assertEqual(client.post("/auth/login", json={"email": "a@b.cz", "password": "x"}).status_code, 404)
        self.assertEqual(client.get("/login", follow_redirects=False).status_code, 303)


if __name__ == "__main__":
    unittest.main()
