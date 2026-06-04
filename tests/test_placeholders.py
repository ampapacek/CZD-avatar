import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.config import get_settings
from app.rag.placeholders import (
    delete_placeholder,
    load_placeholders,
    placeholder_defs_from_records,
    save_placeholder,
)


class PlaceholderStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "placeholders.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_round_trip_select(self) -> None:
        record = save_placeholder(
            self.path,
            name="length",
            label="Délka",
            kind="select",
            default="medium",
            options=[
                {"name": "short", "label": "Krátká", "text": "Stručně."},
                {"name": "medium", "label": "Střední", "text": "Středně."},
            ],
            owner_id="owner-a",
        )
        self.assertEqual(record["name"], "length")
        self.assertEqual(record["owner_id"], "owner-a")
        self.assertTrue(record["updated_at"])
        loaded = load_placeholders(self.path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["options"][0]["text"], "Stručně.")

    def test_round_trip_text(self) -> None:
        save_placeholder(
            self.path,
            name="custom_instructions",
            label="Vlastní instrukce",
            kind="text",
            default="Žádné.",
        )
        loaded = load_placeholders(self.path)[0]
        self.assertEqual(loaded["kind"], "text")
        self.assertEqual(loaded["default"], "Žádné.")
        self.assertEqual(loaded["options"], [])

    def test_update_preserves_owner(self) -> None:
        save_placeholder(self.path, name="length", label="Délka", owner_id="owner-a")
        updated = save_placeholder(self.path, name="length", label="Délka v2", owner_id="owner-b")
        self.assertEqual(updated["owner_id"], "owner-a")
        self.assertEqual(updated["label"], "Délka v2")
        self.assertEqual(len(load_placeholders(self.path)), 1)

    def test_delete(self) -> None:
        save_placeholder(self.path, name="length", label="Délka")
        self.assertTrue(delete_placeholder(self.path, "length"))
        self.assertEqual(load_placeholders(self.path), [])
        self.assertFalse(delete_placeholder(self.path, "length"))

    def test_defs_from_records(self) -> None:
        save_placeholder(
            self.path,
            name="length",
            label="Délka",
            kind="select",
            default="medium",
            options=[{"name": "short", "label": "Krátká", "text": "Stručně."}],
        )
        defs = placeholder_defs_from_records(load_placeholders(self.path))
        self.assertIn("length", defs)
        self.assertEqual(defs["length"].options[0].text, "Stručně.")


class SeededPlaceholderFileTests(unittest.TestCase):
    def test_seed_file_shape(self) -> None:
        path = Path(get_settings().placeholders_path)
        self.assertTrue(path.exists(), "data/placeholders.json must be committed")
        records = load_placeholders(path)
        by_name = {item["name"]: item for item in records}
        self.assertIn("length", by_name)
        self.assertIn("custom_instructions", by_name)

        length = by_name["length"]
        self.assertEqual(length["kind"], "select")
        self.assertEqual(length["label"], "Délka")
        self.assertEqual(length["default"], "medium")
        self.assertEqual(
            {option["name"] for option in length["options"]},
            {"short", "medium", "long"},
        )
        self.assertEqual(
            {option["label"] for option in length["options"]},
            {"Krátká", "Střední", "Dlouhá"},
        )

        custom = by_name["custom_instructions"]
        self.assertEqual(custom["kind"], "text")
        self.assertEqual(custom["label"], "Vlastní instrukce")
        self.assertEqual(custom["default"], "Žádné.")


class PlaceholderEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "placeholders.json"
        self._orig_path = main.settings.placeholders_path
        self._orig_password = main.settings.admin_password
        main.settings.placeholders_path = self.path
        main.settings.admin_password = "s3cret"
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        main.settings.placeholders_path = self._orig_path
        main.settings.admin_password = self._orig_password
        self._tmp.cleanup()

    def _create(self, name: str, owner_id: str | None) -> dict:
        response = self.client.post(
            "/placeholders",
            json={"name": name, "label": name, "kind": "text", "owner_id": owner_id},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_owner_updates_and_deletes_without_password(self) -> None:
        created = self._create("tone", owner_id="owner-a")
        update = self.client.post(
            "/placeholders",
            json={"name": created["name"], "label": "Tón", "kind": "text", "owner_id": "owner-a"},
        )
        self.assertEqual(update.status_code, 200, update.text)
        deleted = self.client.delete(f"/placeholders/{created['name']}", params={"owner_id": "owner-a"})
        self.assertEqual(deleted.status_code, 204)

    def test_other_browser_blocked_without_password(self) -> None:
        created = self._create("tone", owner_id="owner-a")
        update = self.client.post(
            "/placeholders",
            json={"name": created["name"], "label": "Hijack", "kind": "text", "owner_id": "owner-b"},
        )
        self.assertEqual(update.status_code, 403)
        deleted = self.client.delete(f"/placeholders/{created['name']}", params={"owner_id": "owner-b"})
        self.assertEqual(deleted.status_code, 403)

    def test_other_browser_allowed_with_password(self) -> None:
        created = self._create("tone", owner_id="owner-a")
        update = self.client.post(
            "/placeholders",
            json={
                "name": created["name"],
                "label": "Admin edit",
                "kind": "text",
                "owner_id": "owner-b",
                "admin_password": "s3cret",
            },
        )
        self.assertEqual(update.status_code, 200, update.text)
        deleted = self.client.delete(
            f"/placeholders/{created['name']}",
            params={"owner_id": "owner-b", "admin_password": "s3cret"},
        )
        self.assertEqual(deleted.status_code, 204)

    def test_get_returns_saved(self) -> None:
        self._create("tone", owner_id="owner-a")
        response = self.client.get("/placeholders")
        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json()}
        self.assertIn("tone", names)

    def test_delete_missing_returns_404(self) -> None:
        response = self.client.delete("/placeholders/nope", params={"owner_id": "owner-a"})
        self.assertEqual(response.status_code, 404)

    def test_saved_file_shape(self) -> None:
        self._create("tone", owner_id="owner-a")
        written = json.loads(self.path.read_text(encoding="utf-8"))["placeholders"][0]
        self.assertEqual(
            set(written),
            {"name", "label", "kind", "help", "default", "options", "owner_id", "updated_at"},
        )


if __name__ == "__main__":
    unittest.main()
