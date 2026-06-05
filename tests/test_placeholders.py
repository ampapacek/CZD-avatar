import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.rag.placeholders import (
    DEFAULT_PLACEHOLDERS,
    delete_placeholder,
    load_placeholders,
    placeholder_def_from_record,
    placeholder_defs_from_records,
    save_placeholder,
)
from app.rag.prompts import PlaceholderDef, resolve_placeholder_defs


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


class DefaultPlaceholdersTests(unittest.TestCase):
    def test_code_floor_contains_length_and_custom_instructions(self) -> None:
        self.assertIn("length", DEFAULT_PLACEHOLDERS)
        self.assertIn("custom_instructions", DEFAULT_PLACEHOLDERS)

        length = DEFAULT_PLACEHOLDERS["length"]
        self.assertEqual(length.kind, "select")
        self.assertEqual(length.label, "Délka")
        self.assertEqual(length.default, "medium")
        self.assertEqual({option.name for option in length.options}, {"short", "medium", "long"})
        self.assertEqual({option.label for option in length.options}, {"Krátká", "Střední", "Dlouhá"})

        custom = DEFAULT_PLACEHOLDERS["custom_instructions"]
        self.assertEqual(custom.kind, "text")
        self.assertEqual(custom.label, "Vlastní instrukce")
        self.assertEqual(custom.default, "")

    def test_resolution_uses_code_floor_when_overlay_absent(self) -> None:
        # No overlay (placeholders.json absent) and no higher layer: the code
        # floor still provides length / custom_instructions.
        defs = resolve_placeholder_defs(
            {"length", "custom_instructions"},
            code_default_defs=DEFAULT_PLACEHOLDERS,
        )
        self.assertEqual(defs["length"].default, "medium")
        self.assertEqual(defs["custom_instructions"].default, "")

    def test_code_floor_def_applies_only_when_no_higher_layer(self) -> None:
        # custom_instructions only in code; length overridden by overlay.
        overlay = {"length": PlaceholderDef(label="x", kind="text", default="OVERLAY")}
        defs = resolve_placeholder_defs(
            {"length", "custom_instructions"},
            shared_global_defs=overlay,
            code_default_defs=DEFAULT_PLACEHOLDERS,
        )
        self.assertEqual(defs["length"].default, "OVERLAY")
        self.assertEqual(defs["custom_instructions"].default, "")


class PlaceholderRecordConversionTests(unittest.TestCase):
    def test_missing_file_returns_empty_without_raising(self) -> None:
        self.assertEqual(load_placeholders(Path("/nonexistent/placeholders.json")), [])

    def test_round_trip_from_inline_record(self) -> None:
        # placeholder_def_from_record bridges stored inline records to defs.
        definition = placeholder_def_from_record(
            {"name": "length", "label": "Délka", "kind": "select", "default": "short",
             "options": [{"name": "short", "label": "Krátká", "text": "X"}]}
        )
        self.assertEqual(definition.kind, "select")
        self.assertEqual(definition.options[0].text, "X")


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

    def test_builtin_server_override_requires_password(self) -> None:
        response = self.client.post(
            "/placeholders",
            json={"name": "length", "label": "Délka", "kind": "text", "owner_id": "owner-a"},
        )
        self.assertEqual(response.status_code, 403)

        created = self.client.post(
            "/placeholders",
            json={
                "name": "length",
                "label": "Délka",
                "kind": "text",
                "owner_id": "owner-a",
                "admin_password": "s3cret",
            },
        )
        self.assertEqual(created.status_code, 200, created.text)

        owner_update = self.client.post(
            "/placeholders",
            json={"name": "length", "label": "Délka bez hesla", "kind": "text", "owner_id": "owner-a"},
        )
        self.assertEqual(owner_update.status_code, 403)

        admin_update = self.client.post(
            "/placeholders",
            json={
                "name": "length",
                "label": "Délka admin",
                "kind": "text",
                "owner_id": "owner-b",
                "admin_password": "s3cret",
            },
        )
        self.assertEqual(admin_update.status_code, 200, admin_update.text)

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


class ResolveChatPlaceholdersTests(unittest.TestCase):
    """14d: the chat request's ``placeholder_defs`` carries fully resolved
    effective defs (inline -> browser-local global -> shared overlay) and must win
    over the server's own shared overlay, so browser-local globals take effect."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "placeholders.json"
        self._orig_path = main.settings.placeholders_path
        main.settings.placeholders_path = self.path

    def tearDown(self) -> None:
        main.settings.placeholders_path = self._orig_path
        self._tmp.cleanup()

    def _request(self, placeholder_defs):
        from app.models import ChatRequest

        return ChatRequest(
            question="q",
            system_prompt="Délka: {length}",
            user_prompt_template="Otázka: {question}",
            selections={"length": "short"},
            placeholder_defs=placeholder_defs,
        )

    def test_request_defs_override_shared_overlay(self) -> None:
        # Shared overlay on disk says one thing...
        save_placeholder(
            self.path,
            name="length",
            label="Délka",
            kind="select",
            default="short",
            options=[{"name": "short", "label": "K", "text": "OVERLAY short"}],
        )
        # ...but the request carries an effective (e.g. browser-local) def that wins.
        request = self._request(
            {
                "length": {
                    "label": "Délka",
                    "kind": "select",
                    "default": "short",
                    "options": [{"name": "short", "label": "K", "text": "LOCAL short"}],
                }
            }
        )
        defs, selections = main._resolve_chat_placeholders(request)
        self.assertEqual(defs["length"].options[0].text, "LOCAL short")
        self.assertEqual(selections["length"], "short")

    def test_falls_back_to_overlay_then_code_floor(self) -> None:
        save_placeholder(
            self.path,
            name="length",
            label="Délka",
            kind="select",
            default="short",
            options=[{"name": "short", "label": "K", "text": "OVERLAY short"}],
        )
        # Request omits length: overlay supplies it; custom_instructions falls to floor.
        request = self._request(None)
        request.user_prompt_template = "Otázka: {question} {custom_instructions}"
        defs, _ = main._resolve_chat_placeholders(request)
        self.assertEqual(defs["length"].options[0].text, "OVERLAY short")
        self.assertEqual(defs["custom_instructions"].default, "")


if __name__ == "__main__":
    unittest.main()
