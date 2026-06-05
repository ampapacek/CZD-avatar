import json
import tempfile
import unittest
from pathlib import Path

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
                "system_prompt": "sys",
                "user_prompt_template": "{question}",
                "owner_id": "owner-a",
            },
        )
        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(update.json()["name"], "Mine v2")

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
                "system_prompt",
                "user_prompt_template",
                "placeholders",
                "owner_id",
                "updated_at",
            },
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


if __name__ == "__main__":
    unittest.main()
