import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.rag import shared_history


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

    def test_generation_details_round_trip(self) -> None:
        created = self._create(
            "Details",
            owner_id="owner-a",
            model_used="openrouter/free",
            upstream_model="vendor/actual-model",
            response_time_seconds=4.2,
            token_budget={"context_window_tokens": 65000, "estimated_source_tokens": 15269},
        )
        stored = self.client.get(f"/shared-history/{created['id']}").json()
        self.assertEqual(stored["model_used"], "openrouter/free")
        self.assertEqual(stored["upstream_model"], "vendor/actual-model")
        self.assertEqual(stored["response_time_seconds"], 4.2)
        self.assertEqual(stored["token_budget"]["estimated_source_tokens"], 15269)

    def test_items_shared_without_generation_details_load(self) -> None:
        self.path.write_text('{"items": [{"id": "old", "response_time_seconds": "junk"}]}', encoding="utf-8")
        stored = self.client.get("/shared-history/old").json()
        self.assertIsNone(stored["model_used"])
        self.assertIsNone(stored["response_time_seconds"])
        self.assertIsNone(stored["token_budget"])

    def test_visibility_defaults_to_listed_for_new_and_legacy_items(self) -> None:
        created = self._create("New", owner_id="owner-a")
        self.assertEqual(created["visibility"], "listed")
        # A file written before visibility existed, plus an unknown value.
        self.path.write_text(
            '{"items": [{"id": "old", "question": "Old"}, {"id": "odd", "visibility": "secret"}]}',
            encoding="utf-8",
        )
        items = self.client.get("/shared-history").json()
        self.assertEqual({item["id"]: item["visibility"] for item in items}, {"old": "listed", "odd": "listed"})

    def test_link_only_items_hidden_from_list_but_fetchable_by_id(self) -> None:
        listed = self._create("Listed", owner_id="owner-a")
        unlisted = self._create("Unlisted", owner_id="owner-a", visibility="link")
        self.assertEqual(unlisted["visibility"], "link")

        anonymous = self.client.get("/shared-history").json()
        self.assertEqual([item["id"] for item in anonymous], [listed["id"]])
        stranger = self.client.get("/shared-history", params={"owner_id": "owner-b"}).json()
        self.assertEqual([item["id"] for item in stranger], [listed["id"]])
        owner = self.client.get("/shared-history", params={"owner_id": "owner-a"}).json()
        self.assertEqual([item["id"] for item in owner], [unlisted["id"], listed["id"]])

        fetched = self.client.get(f"/shared-history/{unlisted['id']}")
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.json()["question"], "Unlisted")

    def test_get_missing_item_returns_404(self) -> None:
        self.assertEqual(self.client.get("/shared-history/nope").status_code, 404)

    def test_owner_can_change_visibility(self) -> None:
        created = self._create("Mine", owner_id="owner-a")
        response = self.client.patch(
            f"/shared-history/{created['id']}", json={"visibility": "link", "owner_id": "owner-a"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["visibility"], "link")
        self.assertEqual(self.client.get("/shared-history").json(), [])
        # Everything else survives the rewrite.
        stored = self.client.get(f"/shared-history/{created['id']}").json()
        self.assertEqual(stored["answer"], "answer")
        self.assertEqual(stored["shared_at"], created["shared_at"])

    def test_visibility_change_requires_owner_or_password(self) -> None:
        created = self._create("Theirs", owner_id="owner-a")
        url = f"/shared-history/{created['id']}"
        blocked = self.client.patch(url, json={"visibility": "link", "owner_id": "owner-b"})
        self.assertEqual(blocked.status_code, 403)
        admin = self.client.patch(
            url, json={"visibility": "link", "owner_id": "owner-b", "admin_password": "s3cret"}
        )
        self.assertEqual(admin.status_code, 200, admin.text)
        missing = self.client.patch("/shared-history/nope", json={"visibility": "link", "owner_id": "owner-a"})
        self.assertEqual(missing.status_code, 404)
        invalid = self.client.patch(url, json={"visibility": "secret", "owner_id": "owner-a"})
        self.assertEqual(invalid.status_code, 422)

    def test_owner_can_edit_note_and_edit_is_stamped(self) -> None:
        created = self._create("Mine", owner_id="owner-a")
        self.assertIsNone(created["note_edited_at"])
        url = f"/shared-history/{created['id']}"
        response = self.client.patch(url, json={"note": "better note", "owner_id": "owner-a"})
        self.assertEqual(response.status_code, 200, response.text)
        edited = response.json()
        self.assertEqual(edited["note"], "better note")
        self.assertTrue(edited["note_edited_at"])
        # The visibility is untouched and no previous text is kept anywhere.
        self.assertEqual(edited["visibility"], "listed")
        self.assertNotIn('"note": "note"', self.path.read_text(encoding="utf-8"))
        self.assertEqual(self.client.get(url).json()["note"], "better note")

    def test_unchanged_note_does_not_stamp_an_edit(self) -> None:
        created = self._create("Mine", owner_id="owner-a")
        url = f"/shared-history/{created['id']}"
        same = self.client.patch(url, json={"note": "note", "owner_id": "owner-a"}).json()
        self.assertIsNone(same["note_edited_at"])
        # A visibility-only change does not count as a note edit either.
        moved = self.client.patch(url, json={"visibility": "link", "owner_id": "owner-a"}).json()
        self.assertEqual(moved["note"], "note")
        self.assertIsNone(moved["note_edited_at"])

    def test_note_edit_requires_owner_or_password(self) -> None:
        created = self._create("Theirs", owner_id="owner-a")
        url = f"/shared-history/{created['id']}"
        blocked = self.client.patch(url, json={"note": "hijack", "owner_id": "owner-b"})
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(self.client.get(url).json()["note"], "note")
        admin = self.client.patch(url, json={"note": "fixed", "owner_id": "owner-b", "admin_password": "s3cret"})
        self.assertEqual(admin.status_code, 200, admin.text)
        self.assertEqual(admin.json()["note"], "fixed")


class SharedHistoryStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "shared_history.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_concurrent_shares_are_all_kept(self) -> None:
        # Each share reads the list, adds one and writes it back; without the
        # lock, overlapping shares drop each other's items.
        real_read = shared_history._read_items

        def slow_read(path):
            items = real_read(path)
            threading.Event().wait(0.01)  # widen the read-to-write window
            return items

        with patch.object(shared_history, "_read_items", side_effect=slow_read):
            threads = [
                threading.Thread(
                    target=shared_history.save_shared_history_item,
                    kwargs={"path": self.path, "question": f"q{index}"},
                )
                for index in range(8)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        questions = {item["question"] for item in shared_history.load_shared_history(self.path)}
        self.assertEqual(questions, {f"q{index}" for index in range(8)})

    def test_failed_write_leaves_the_old_file_whole(self) -> None:
        kept = shared_history.save_shared_history_item(self.path, question="kept")

        with patch.object(shared_history.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                shared_history.save_shared_history_item(self.path, question="lost")

        self.assertEqual([item["id"] for item in shared_history.load_shared_history(self.path)], [kept["id"]])
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_unreadable_file_is_never_overwritten(self) -> None:
        # Readers see a broken file as empty, but a write must not turn that
        # into "the new item only" and erase everything else.
        self.path.write_text('{"items": [{"id": "a"', encoding="utf-8")

        self.assertEqual(shared_history.load_shared_history(self.path), [])
        with self.assertRaises(ValueError):
            shared_history.save_shared_history_item(self.path, question="new")
        self.assertEqual(self.path.read_text(encoding="utf-8"), '{"items": [{"id": "a"')


if __name__ == "__main__":
    unittest.main()
