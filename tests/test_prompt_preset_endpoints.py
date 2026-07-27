import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main


class PromptPresetEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "prompt_presets.json"
        self._orig_path = main.settings.prompt_presets_path
        self._orig_password = main.settings.admin_password
        main.settings.prompt_presets_path = self.path
        main.settings.admin_password = "s3cret"
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        main.settings.prompt_presets_path = self._orig_path
        main.settings.admin_password = self._orig_password
        self._tmp.cleanup()

    def _create(self, name: str, owner_id: str | None) -> dict:
        response = self.client.post(
            "/prompt-presets",
            json={
                "name": name,
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": owner_id,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_owner_updates_and_deletes_without_password(self) -> None:
        created = self._create("Mine", owner_id="owner-a")
        update = self.client.post(
            "/prompt-presets",
            json={
                "id": created["id"],
                "name": "Mine v2",
                "note": "Updated usage experience.",
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-a",
            },
        )
        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(update.json()["name"], "Mine v2")
        self.assertEqual(update.json()["note"], "Updated usage experience.")
        self.assertEqual(update.json()["id"], created["id"])

        deleted = self.client.delete(f"/prompt-presets/{created['id']}", params={"owner_id": "owner-a"})
        self.assertEqual(deleted.status_code, 204)

    def test_other_browser_blocked_without_password(self) -> None:
        created = self._create("Shared", owner_id="owner-a")
        update = self.client.post(
            "/prompt-presets",
            json={
                "id": created["id"],
                "name": "Hijacked",
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-b",
            },
        )
        self.assertEqual(update.status_code, 403)
        deleted = self.client.delete(f"/prompt-presets/{created['id']}", params={"owner_id": "owner-b"})
        self.assertEqual(deleted.status_code, 403)

    def test_other_browser_allowed_with_password(self) -> None:
        created = self._create("Shared", owner_id="owner-a")
        update = self.client.post(
            "/prompt-presets",
            json={
                "id": created["id"],
                "name": "Edited by admin",
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-b",
                "admin_password": "s3cret",
            },
        )
        self.assertEqual(update.status_code, 200, update.text)
        deleted = self.client.delete(
            f"/prompt-presets/{created['id']}",
            params={"owner_id": "owner-b", "admin_password": "s3cret"},
        )
        self.assertEqual(deleted.status_code, 204)

    def test_saved_server_prompt_writes_only_intended_fields(self) -> None:
        response = self.client.post(
            "/prompt-presets",
            json={
                "name": "Scoped",
                "wp_id": "WP2-média",
                "note": "Why this variant exists.",
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-a",
                # Legacy field a stale client might still send; must not be persisted.
                "style_prompts": {"ucitel": "x"},
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["wp_id"], "WP2-média")

        written = json.loads(self.path.read_text(encoding="utf-8"))["presets"][0]
        self.assertEqual(
            set(written),
            {
                "id",
                "name",
                "wp_id",
                "note",
                "system_prompt",
                "user_prompt_template",
                "placeholders",
                "query_transform",
                "owner_id",
                "updated_at",
            },
        )
        self.assertEqual(response.json()["note"], "Why this variant exists.")

    def test_write_failure_returns_structured_json_error(self) -> None:
        with patch.object(
            main,
            "save_prompt_preset",
            side_effect=PermissionError("permission denied"),
        ):
            response = self.client.post(
                "/prompt-presets",
                json={
                    "name": "Cannot save",
                    "system_prompt": "sys",
                    "user_prompt_template": "{question}",
                    "owner_id": "owner-a",
                },
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"detail": "Sdílený prompt se nepodařilo uložit na server."},
        )

    def test_ownerless_preset_requires_password(self) -> None:
        created = self._create("Legacy", owner_id="")
        update = self.client.post(
            "/prompt-presets",
            json={
                "id": created["id"],
                "name": "Legacy edited",
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-x",
            },
        )
        self.assertEqual(update.status_code, 403)
        deleted = self.client.delete(f"/prompt-presets/{created['id']}", params={"owner_id": "owner-x"})
        self.assertEqual(deleted.status_code, 403)

    def test_builtin_id_can_be_saved_as_shared_override_with_normal_ownership(self) -> None:
        created = self.client.post(
            "/prompt-presets",
            json={
                "id": "wp1-laik",
                "name": "Laik",
                "wp_id": "WP1-historie",
                "system_prompt": "shared override",
                "user_prompt_template": "{question}",
                "owner_id": "owner-a",
            },
        )
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["id"], "wp1-laik")

        blocked = self.client.post(
            "/prompt-presets",
            json={
                "id": "wp1-laik",
                "name": "Laik",
                "wp_id": "WP1-historie",
                "system_prompt": "other browser",
                "user_prompt_template": "{question}",
                "owner_id": "owner-b",
            },
        )
        self.assertEqual(blocked.status_code, 403)

        owner_update = self.client.post(
            "/prompt-presets",
            json={
                "id": "wp1-laik",
                "name": "Laik",
                "wp_id": "WP1-historie",
                "system_prompt": "owner update",
                "user_prompt_template": "{question}",
                "owner_id": "owner-a",
            },
        )
        self.assertEqual(owner_update.status_code, 200, owner_update.text)
        self.assertEqual(owner_update.json()["system_prompt"], "owner update")

    def test_admin_saves_transformation_only_override_for_builtin_prompt(self) -> None:
        saved_prompt = self._create("Unrelated", owner_id="owner-a")
        response = self.client.put(
            "/prompt-presets/builtin-overrides/wp1-ucitel",
            json={
                "admin_password": "s3cret",
                "query_transform": {
                    "enabled": True,
                    "auto_apply": True,
                    "default_action": "translate",
                    "actions": [
                        {
                            "id": "translate",
                            "label": "Translate",
                            "description": "Translate the query.",
                            "type": "llm",
                            "prompt_template": "Translate: {question}",
                        }
                    ],
                },
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["prompt_id"], "wp1-ucitel")
        document = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(document["presets"][0]["id"], saved_prompt["id"])
        override = document["builtin_overrides"]["wp1-ucitel"]
        self.assertEqual(set(override), {"query_transform"})
        self.assertNotIn("system_prompt", override)

        with patch.object(
            main.pipeline.msearch_retriever,
            "live_collections_by_prefix",
            return_value={},
        ):
            wps = main._wps_payload_with_live_collections()
        builtin = next(
            prompt
            for wp in wps
            for prompt in wp["builtin_prompts"]
            if prompt["id"] == "wp1-ucitel"
        )
        self.assertTrue(builtin["system_prompt"])
        self.assertTrue(builtin["query_transform"]["enabled"])
        self.assertEqual(main._effective_query_transform("wp1-ucitel")["default_action"], "translate")

    def test_builtin_override_requires_admin_password(self) -> None:
        response = self.client.put(
            "/prompt-presets/builtin-overrides/wp1-ucitel",
            json={
                "query_transform": {
                    "enabled": False,
                    "actions": [],
                },
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.path.exists())

    def test_builtin_override_rejects_unknown_prompt(self) -> None:
        response = self.client.put(
            "/prompt-presets/builtin-overrides/not-a-prompt",
            json={
                "admin_password": "s3cret",
                "query_transform": {
                    "enabled": False,
                    "actions": [],
                },
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_remove_builtin_override_without_removing_presets(self) -> None:
        saved_prompt = self._create("Unrelated", owner_id="owner-a")
        created = self.client.put(
            "/prompt-presets/builtin-overrides/wp1-ucitel",
            json={
                "admin_password": "s3cret",
                "query_transform": {
                    "enabled": False,
                    "actions": [],
                },
            },
        )
        self.assertEqual(created.status_code, 200, created.text)

        deleted = self.client.delete(
            "/prompt-presets/builtin-overrides/wp1-ucitel",
            params={"admin_password": "s3cret"},
        )

        self.assertEqual(deleted.status_code, 204)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(document["builtin_overrides"], {})
        self.assertEqual(document["presets"][0]["id"], saved_prompt["id"])


if __name__ == "__main__":
    unittest.main()
