import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import auth, main
from app.accounts import AccountStore, LoginThrottle
from app.admin_password_guard import AdminPasswordGuard
from app.answer_cache import AnswerCache
from tests.test_answer_cache import EndpointTestCase

ADMIN = {"X-Admin-Password": "secret"}


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = AnswerCache(Path(self.tmp.name) / "cache.sqlite3", ttl_seconds=100, max_entries=10)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_entries_summarise_live_entries_newest_first(self) -> None:
        key_input = {"question": "q", "wp_id": "WP1", "model": "m", "llm_provider": "p", "cache_version": 2, "server": {"a": 1}}
        self.cache.put("old", key_input, {"answer": "a"}, meta={"prompt_preset_id": "x"}, now=1000)
        self.cache.put("new", {**key_input, "question": "q2"}, {"answer": "b"}, pinned=True, now=1050)
        self.cache.get("old", now=1060)
        entries = self.cache.entries(now=1060)
        self.assertEqual([entry["key"] for entry in entries], ["new", "old"])
        old = entries[1]
        self.assertEqual(
            {name: old[name] for name in ("question", "wp_id", "model", "llm_provider", "prompt_preset_id", "hit_count", "pinned", "server")},
            {"question": "q", "wp_id": "WP1", "model": "m", "llm_provider": "p", "prompt_preset_id": "x",
             "hit_count": 1, "pinned": False, "server": {"a": 1}},
        )
        self.assertGreater(old["size"], 0)
        self.assertEqual([entry["key"] for entry in self.cache.entries(now=1101)], ["new"])

    def test_peek_does_not_count_a_hit(self) -> None:
        self.cache.put("k", {"question": "q"}, {"answer": "a"}, now=1000)
        self.assertEqual(self.cache.peek("k"), ({"question": "q"}, {"answer": "a"}))
        self.assertIsNone(self.cache.peek("missing"))
        self.assertEqual(self.cache.entries(now=1001)[0]["hit_count"], 0)

    def test_unpin_and_delete_many(self) -> None:
        self.cache.put("a", {}, {"answer": "a"}, pinned=True, now=1000)
        self.cache.put("b", {}, {"answer": "b"}, now=1000)
        self.assertTrue(self.cache.unpin("a"))
        self.assertFalse(self.cache.unpin("missing"))
        self.assertIsNone(self.cache.get("a", now=1101))
        self.cache.put("c", {}, {"answer": "c"}, now=2000)
        self.cache.put("d", {}, {"answer": "d"}, now=2000)
        self.assertEqual(self.cache.delete_many(["c", "d", "missing"]), 2)
        self.assertEqual(self.cache.count(), 0)


class AdminTestCase(EndpointTestCase):
    def setUp(self) -> None:
        super().setUp()
        for item in (
            patch.object(main.settings, "admin_password", "secret"),
            patch.object(main, "admin_password_guard", AdminPasswordGuard()),
        ):
            item.start()
            self.addCleanup(item.stop)

    def listing(self, **params):
        response = self.client.get("/answer-cache", params=params, headers=ADMIN)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()


class AdminEndpointTests(AdminTestCase):
    def test_needs_admin_access(self) -> None:
        key = self.done(self.ask())["cache_key"]
        wrong = {"X-Admin-Password": "wrong"}
        for method, path, kwargs in (
            ("get", "/answer-cache", {}),
            ("get", f"/answer-cache/{key}", {}),
            ("put", f"/answer-cache/{key}/pin", {"json": {"pinned": True}}),
            ("delete", f"/answer-cache/{key}", {}),
            ("post", "/answer-cache/delete", {"json": {}}),
        ):
            for headers in ({}, wrong):
                with self.subTest(method=method, path=path, headers=headers):
                    response = getattr(self.client, method)(path, headers=headers, **kwargs)
                    self.assertEqual(response.status_code, 403)
        self.assertEqual(self.cache.count(), 1)

    def test_lists_previews_pins_and_deletes(self) -> None:
        key = self.done(self.ask(prompt_preset_id="wp1-ucitel"))["cache_key"]
        self.ask()
        data = self.listing()
        self.assertEqual(data["matching"], 1)
        self.assertEqual({name: data["stats"][name] for name in ("entries", "pinned", "stale", "hits")},
                         {"entries": 1, "pinned": 0, "stale": 0, "hits": 1})
        entry = data["entries"][0]
        self.assertEqual((entry["key"], entry["question"], entry["model"], entry["stale"]),
                         (key, "Kdo byl Jan Hus?", "test-model", False))
        self.assertEqual(entry["prompt_preset_name"], "Učitel")

        preview = self.client.get(f"/answer-cache/{key}", headers=ADMIN).json()
        self.assertEqual(preview["answer"], "Jan Hus byl kazatel [1].")
        self.assertEqual(preview["settings"]["question"], "Kdo byl Jan Hus?")
        self.assertNotIn("llm_api_key", preview["settings"])
        self.assertEqual(self.listing()["stats"]["hits"], 1)

        self.assertEqual(self.client.put(f"/answer-cache/{key}/pin", json={"pinned": True}, headers=ADMIN).status_code, 200)
        self.assertTrue(self.listing()["entries"][0]["pinned"])
        self.client.put(f"/answer-cache/{key}/pin", json={"pinned": False}, headers=ADMIN)
        self.assertFalse(self.listing()["entries"][0]["pinned"])

        self.assertEqual(self.client.delete(f"/answer-cache/{key}", headers=ADMIN).status_code, 204)
        self.assertEqual(self.client.delete(f"/answer-cache/{key}", headers=ADMIN).status_code, 404)
        self.assertEqual(self.client.get(f"/answer-cache/{key}", headers=ADMIN).status_code, 404)
        self.assertEqual(self.client.put(f"/answer-cache/{key}/pin", json={"pinned": True}, headers=ADMIN).status_code, 404)

    def test_filters_and_bulk_delete(self) -> None:
        jan = self.done(self.ask())["cache_key"]
        self.ask(question="Kdo byl Žižka?")
        self.ask(question="Kdo byl Žižka?", top_k=3)
        self.cache.pin(jan)
        self.assertEqual(self.listing(pinned=True)["matching"], 1)
        self.assertEqual(self.listing(pinned=False)["matching"], 2)
        self.assertEqual(self.listing(q="žIžKA")["matching"], 2)
        self.assertEqual(self.listing(wp_id="nonexistent")["matching"], 0)

        deleted = self.client.post("/answer-cache/delete", json={"pinned": False, "q": "žižka"}, headers=ADMIN).json()
        self.assertEqual(deleted, {"deleted": 2})
        self.assertEqual([entry["key"] for entry in self.listing()["entries"]], [jan])

    def test_entries_for_another_configuration_are_stale(self) -> None:
        old = self.done(self.ask())["cache_key"]
        with patch.object(main.settings, "top_k", main.settings.top_k + 1):
            new = self.done(self.ask())["cache_key"]
            self.assertNotEqual(old, new)
            entries = {entry["key"]: entry["stale"] for entry in self.listing()["entries"]}
            self.assertEqual(entries, {old: True, new: False})
            self.assertEqual(self.listing()["stats"]["stale"], 1)
            self.assertEqual([entry["key"] for entry in self.listing(stale=True)["entries"]], [old])
            self.client.post("/answer-cache/delete", json={"stale": True}, headers=ADMIN)
        self.assertEqual(self.cache.count(), 1)

    def test_disabled_cache(self) -> None:
        with patch.object(main, "_get_answer_cache", lambda: None):
            self.assertEqual(self.client.get("/answer-cache", headers=ADMIN).status_code, 404)
        with patch.object(main.settings, "answer_cache_enabled", False):
            self.assertFalse(self.client.get("/settings").json()["answer_cache_enabled"])


class AccountAdminTests(AdminTestCase):
    """With accounts on, a logged-in admin needs no password; others get 403."""

    def setUp(self) -> None:
        super().setUp()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        auth.set_store(self.store)
        for item in (
            patch.object(main.settings, "auth_enabled", True),
            patch.object(auth, "login_throttle", LoginThrottle()),
        ):
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(auth.set_store, None)
        self.store.create_user("admin@seznam.cz", "admin password", is_admin=True)
        self.store.create_user("jan@seznam.cz", "user password")

    def client_for(self, email, password):
        client = TestClient(main.app, base_url="https://testserver")
        client.post("/auth/login", json={"email": email, "password": password})
        return client

    def test_admin_account_and_user(self) -> None:
        self.assertEqual(self.client_for("admin@seznam.cz", "admin password").get("/answer-cache").status_code, 200)
        self.assertEqual(self.client_for("jan@seznam.cz", "user password").get("/answer-cache").status_code, 403)
        anonymous = TestClient(main.app, base_url="https://testserver")
        self.assertEqual(anonymous.get("/answer-cache", headers=ADMIN).status_code, 401)


if __name__ == "__main__":
    unittest.main()
