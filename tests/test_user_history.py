import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import auth, main
from app.accounts import AccountStore, HistoryLimitError, HistoryLimits, LoginThrottle


def entry(entry_id, **fields):
    return {"id": entry_id, "question": f"Otázka {entry_id}", **fields}


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        self.user = self.store.create_user("jan@seznam.cz", "user password")
        self.limits = HistoryLimits(max_entries=3, max_bytes=10_000)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_mode_defaults_to_server(self) -> None:
        self.assertIsNone(self.store.prefs(self.user.id)["history_mode"])
        self.assertEqual(self.store.history_mode(self.user.id), "server")
        self.store.set_history_mode(self.user.id, "none")
        self.assertEqual(self.store.history_mode(self.user.id), "none")

    def test_put_replaces_by_id_and_kind(self) -> None:
        self.store.put_history(self.user.id, "history", "1", entry(1), self.limits)
        self.store.put_history(self.user.id, "history", "1", entry(1, note="upraveno"), self.limits)
        self.store.put_history(self.user.id, "conversation", "1", entry(1, title="Vlákno"), self.limits)
        stored = self.store.list_history(self.user.id)
        self.assertEqual(stored["history"], [entry(1, note="upraveno")])
        self.assertEqual(stored["conversation"], [entry(1, title="Vlákno")])

    def test_limit_refuses_and_keeps_old_entries(self) -> None:
        for entry_id in ("1", "2", "3"):
            self.store.put_history(self.user.id, "history", entry_id, entry(entry_id), self.limits)
        with self.assertRaises(HistoryLimitError):
            self.store.put_history(self.user.id, "history", "4", entry("4"), self.limits)
        # Rewriting an existing entry still fits.
        self.store.put_history(self.user.id, "history", "3", entry("3", note="x"), self.limits)
        self.assertEqual(self.store.history_usage(self.user.id)["entries"], 3)
        with self.assertRaises(HistoryLimitError):
            big = HistoryLimits(max_entries=10, max_bytes=200)
            self.store.put_history(self.user.id, "history", "3", entry("3", answer="x" * 500), big)

    def test_import_keeps_server_versions_and_counts_what_did_not_fit(self) -> None:
        self.store.put_history(self.user.id, "history", "1", entry(1, note="server"), self.limits)
        result = self.store.import_history(
            self.user.id,
            [("history", "1", entry(1, note="browser")), ("history", "2", entry(2)),
             ("conversation", "5", entry(5)), ("history", "6", entry(6))],
            self.limits,
        )
        self.assertEqual(result, {"imported": 2, "existing": 1, "over_limit": 1})
        self.assertIn(entry(1, note="server"), self.store.list_history(self.user.id)["history"])

    def test_deleting_the_user_deletes_their_history(self) -> None:
        self.store.put_history(self.user.id, "history", "1", entry(1), self.limits)
        self.store.set_history_mode(self.user.id, "browser")
        self.store.delete_user(self.user.id)
        with self.store._connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM history_entries").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM user_prefs").fetchone()[0], 0)


class EndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        auth.set_store(self.store)
        self.patches = [
            patch.object(main.settings, "auth_enabled", True),
            patch.object(main.settings, "user_history_max_entries", 3),
            patch.object(auth, "login_throttle", LoginThrottle()),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app, base_url="https://testserver")
        self.other = TestClient(main.app, base_url="https://testserver")
        self.store.create_user("jan@seznam.cz", "user password")
        self.store.create_user("eva@seznam.cz", "user password")
        self.client.post("/auth/login", json={"email": "jan@seznam.cz", "password": "user password"})
        self.other.post("/auth/login", json={"email": "eva@seznam.cz", "password": "user password"})

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        auth.set_store(None)
        self.tmp.cleanup()

    def test_needs_login(self) -> None:
        anonymous = TestClient(main.app, base_url="https://testserver")
        self.assertEqual(anonymous.get("/me/history").status_code, 401)
        self.assertEqual(anonymous.put("/me/prefs", json={"history_mode": "none"}).status_code, 401)

    def test_prefs_are_part_of_the_account(self) -> None:
        # Not chosen yet: the browser decides (browser history stays where it is).
        user = self.client.get("/auth/me").json()["user"]
        self.assertEqual((user["history_mode"], user["author_name"]), (None, None))
        self.assertEqual(self.client.put("/me/prefs", json={"history_mode": "browser"}).status_code, 200)
        self.assertEqual(self.client.get("/settings").json()["account"]["user"]["history_mode"], "browser")
        self.assertEqual(self.client.put("/me/prefs", json={"history_mode": "cloud"}).status_code, 422)
        # Only the fields sent change; the name is trimmed.
        prefs = self.client.put("/me/prefs", json={"author_name": "  Jan   Novák "}).json()
        self.assertEqual(prefs, {"history_mode": "browser", "author_name": "Jan Novák"})
        self.assertEqual(self.client.put("/me/prefs", json={"author_name": ""}).json()["author_name"], None)

    def test_entries_are_private_per_user(self) -> None:
        response = self.client.put("/me/history/history/1", json={"entry": entry(1)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["usage"]["entries"], 1)
        self.client.put("/me/history/conversations/2", json={"entry": entry(2)})
        mine = self.client.get("/me/history").json()
        self.assertEqual((mine["history"], mine["conversations"]), ([entry(1)], [entry(2)]))
        self.assertEqual(mine["usage"]["max_entries"], 3)
        self.assertEqual(self.other.get("/me/history").json()["history"], [])
        # Eva cannot delete Jan's entry: the delete only ever touches her own rows.
        self.other.delete("/me/history/history/1")
        self.assertEqual(len(self.client.get("/me/history").json()["history"]), 1)
        self.assertEqual(self.client.delete("/me/history/history/1").status_code, 204)
        self.assertEqual(self.client.get("/me/history").json()["history"], [])

    def test_bad_ids_and_kinds(self) -> None:
        self.assertEqual(self.client.put("/me/history/other/1", json={"entry": entry(1)}).status_code, 404)
        self.assertEqual(self.client.put("/me/history/history/1", json={"entry": entry(2)}).status_code, 400)
        self.assertEqual(self.client.put("/me/history/history/a b", json={"entry": entry("a b")}).status_code, 400)

    def test_over_the_limit_is_413(self) -> None:
        for entry_id in (1, 2, 3):
            self.client.put(f"/me/history/history/{entry_id}", json={"entry": entry(entry_id)})
        response = self.client.put("/me/history/history/4", json={"entry": entry(4)})
        self.assertEqual(response.status_code, 413)
        self.assertIn("plná", response.json()["detail"])

    def test_import(self) -> None:
        self.client.put("/me/history/history/1", json={"entry": entry(1, note="server")})
        result = self.client.post(
            "/me/history/import",
            json={"history": [entry(1), entry(2)], "conversations": [entry(3), entry(4)]},
        ).json()
        self.assertEqual((result["imported"], result["existing"], result["over_limit"]), (2, 1, 1))
        self.assertEqual(result["usage"]["entries"], 3)

    def test_off_without_accounts(self) -> None:
        with patch.object(main.settings, "auth_enabled", False):
            self.assertEqual(TestClient(main.app).get("/me/history").status_code, 404)



class OwnershipTests(unittest.TestCase):
    """Shared items: browser ids are linked to the first account that sends them."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        auth.set_store(self.store)
        self.patches = [
            patch.object(main.settings, "auth_enabled", False),
            patch.object(main.settings, "shared_history_path", Path(self.tmp.name) / "shared.json"),
            patch.object(main.settings, "admin_password", ""),
            patch.object(auth, "login_throttle", LoginThrottle()),
        ]
        for item in self.patches:
            item.start()
        self.store.create_user("jan@seznam.cz", "user password")
        self.store.create_user("eva@seznam.cz", "user password")

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        auth.set_store(None)
        self.tmp.cleanup()

    def logged_in(self, email: str) -> TestClient:
        client = TestClient(main.app, base_url="https://testserver")
        client.post("/auth/login", json={"email": email, "password": "user password"})
        return client

    def share(self, client: TestClient, owner_id: str) -> dict:
        response = client.post("/shared-history", json={"owner_id": owner_id, "question": "Otázka", "visibility": "link"})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_items_shared_before_accounts_follow_the_first_account(self) -> None:
        old = self.share(TestClient(main.app), "owner-laptop")
        with patch.object(main.settings, "auth_enabled", True):
            jan_laptop, jan_phone, eva = (self.logged_in(email) for email in ("jan@seznam.cz", "jan@seznam.cz", "eva@seznam.cz"))
            url = f"/shared-history/{old['id']}"
            # From the old browser the item is Jan's; that links the browser id to him.
            self.assertTrue(jan_laptop.get(url, params={"owner_id": "owner-laptop"}).json()["mine"])
            # ...so it is his from any other browser too.
            self.assertTrue(jan_phone.get(url, params={"owner_id": "owner-phone"}).json()["mine"])
            edited = jan_phone.patch(url, json={"owner_id": "owner-phone", "note": "z telefonu"})
            self.assertEqual(edited.status_code, 200, edited.text)
            # Eva on the same old browser gets nothing: the first account keeps the id.
            self.assertFalse(eva.get(url, params={"owner_id": "owner-laptop"}).json()["mine"])
            self.assertEqual(eva.patch(url, json={"owner_id": "owner-laptop", "note": "x"}).status_code, 403)
            # An account id cannot be claimed by sending it as a browser id.
            self.assertFalse(eva.get(url, params={"owner_id": "user:1"}).json()["mine"])
            self.assertNotIn("user:1", self.store.owner_ids(2))

    def test_new_items_belong_to_the_account(self) -> None:
        with patch.object(main.settings, "auth_enabled", True):
            jan_laptop, jan_phone, eva = (self.logged_in(email) for email in ("jan@seznam.cz", "jan@seznam.cz", "eva@seznam.cz"))
            item = self.share(jan_laptop, "owner-laptop")
            self.assertTrue(item["mine"])
            stored = main.load_shared_history(main.settings.shared_history_path)[0]
            self.assertEqual(stored["owner_id"], "user:1")
            listed = jan_phone.get("/shared-history", params={"owner_id": "owner-new"}).json()
            self.assertEqual([entry["mine"] for entry in listed], [True])
            # Link-only items of others stay out of Eva's list.
            self.assertEqual(eva.get("/shared-history", params={"owner_id": "owner-eva"}).json(), [])


if __name__ == "__main__":
    unittest.main()
