import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import main


class SharedHistoryEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "shared_history.json"
        self._orig_path = main.settings.shared_history_path
        self._orig_password = main.settings.admin_password
        main.settings.shared_history_path = self.path
        main.settings.admin_password = "s3cret"
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        main.settings.shared_history_path = self._orig_path
        main.settings.admin_password = self._orig_password
        self._tmp.cleanup()

    def _create(self, question: str, owner_id: str = "", **extra) -> dict:
        payload = {
            "owner_id": owner_id,
            "author_name": "Ada",
            "note": "note",
            "question": question,
            "answer": "answer",
            "mode": "chat",
            "settings": {"top_k": 5},
            "sources": [{"title": "Src", "score": 0.9}],
            "retrieved_chunks": [],
            "source_count": 1,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        payload.update(extra)
        response = self.client.post("/shared-history", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_post_creates_and_returns_id_and_shared_at(self) -> None:
        created = self._create("What is history?", owner_id="owner-a")
        self.assertTrue(created["id"])
        self.assertTrue(created["shared_at"])
        self.assertEqual(created["question"], "What is history?")
        self.assertEqual(created["owner_id"], "owner-a")

    def test_get_lists_newest_first(self) -> None:
        first = self._create("First", owner_id="owner-a")
        second = self._create("Second", owner_id="owner-a")
        response = self.client.get("/shared-history")
        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()
        self.assertEqual([item["id"] for item in items], [second["id"], first["id"]])

    def test_settings_and_sources_round_trip_verbatim(self) -> None:
        self._create(
            "Verbatim",
            owner_id="owner-a",
            settings={
                "top_k": 7,
                "system_prompt": "SYS",
                "user_prompt_template": "{question}",
                "nested": {"a": 1, "list": [1, 2, 3]},
            },
            sources=[{"title": "S1", "score": 0.5, "meta": {"page": 3}}],
        )
        items = self.client.get("/shared-history").json()
        stored = items[0]
        self.assertEqual(stored["settings"]["system_prompt"], "SYS")
        self.assertEqual(stored["settings"]["nested"], {"a": 1, "list": [1, 2, 3]})
        self.assertEqual(stored["sources"][0]["meta"], {"page": 3})

    def test_owner_can_delete_without_password(self) -> None:
        created = self._create("Mine", owner_id="owner-a")
        deleted = self.client.delete(
            f"/shared-history/{created['id']}", params={"owner_id": "owner-a"}
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get("/shared-history").json(), [])

    def test_wrong_owner_without_password_blocked(self) -> None:
        created = self._create("Shared", owner_id="owner-a")
        deleted = self.client.delete(
            f"/shared-history/{created['id']}", params={"owner_id": "owner-b"}
        )
        self.assertEqual(deleted.status_code, 403)

    def test_delete_missing_returns_404(self) -> None:
        deleted = self.client.delete(
            "/shared-history/does-not-exist", params={"owner_id": "owner-a"}
        )
        self.assertEqual(deleted.status_code, 404)

    def test_delete_with_admin_password(self) -> None:
        created = self._create("Shared", owner_id="owner-a")
        deleted = self.client.delete(
            f"/shared-history/{created['id']}",
            params={"owner_id": "owner-b", "admin_password": "s3cret"},
        )
        self.assertEqual(deleted.status_code, 204)


if __name__ == "__main__":
    unittest.main()
