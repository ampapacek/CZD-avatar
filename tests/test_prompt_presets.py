import tempfile
import unittest
from pathlib import Path

from app.rag.prompt_presets import (
    delete_prompt_preset,
    load_prompt_presets,
    save_prompt_preset,
)


class PromptPresetStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "prompt_presets.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _save(self, name: str, *, preset_id: str | None = None, owner_id: str | None = None) -> dict:
        return save_prompt_preset(
            self.path,
            name=name,
            system_prompt="sys",
            user_prompt_template="{question}",
            preset_id=preset_id,
            owner_id=owner_id,
        )

    def test_create_records_owner_id(self) -> None:
        record = self._save("Experiment", owner_id="owner-a")
        self.assertEqual(record["owner_id"], "owner-a")
        self.assertEqual(load_prompt_presets(self.path)[0]["owner_id"], "owner-a")

    def test_update_preserves_existing_owner(self) -> None:
        created = self._save("Experiment", owner_id="owner-a")
        updated = self._save("Experiment renamed", preset_id=created["id"], owner_id="owner-b")
        self.assertEqual(updated["owner_id"], "owner-a")
        self.assertEqual(updated["name"], "Experiment renamed")

    def test_authorized_edit_claims_ownerless_preset(self) -> None:
        created = self._save("Legacy", owner_id="")
        self.assertEqual(created["owner_id"], "")
        updated = self._save("Legacy", preset_id=created["id"], owner_id="owner-c")
        self.assertEqual(updated["owner_id"], "owner-c")

    def test_load_normalizes_missing_owner_id(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            '{"presets": [{"id": "p1", "name": "Old", "system_prompt": "", "user_prompt_template": ""}]}',
            encoding="utf-8",
        )
        self.assertEqual(load_prompt_presets(self.path)[0]["owner_id"], "")

    def test_delete_removes_preset(self) -> None:
        created = self._save("Experiment", owner_id="owner-a")
        self.assertTrue(delete_prompt_preset(self.path, created["id"]))
        self.assertEqual(load_prompt_presets(self.path), [])


if __name__ == "__main__":
    unittest.main()
