import tempfile
import unittest
from pathlib import Path

from app.rag.prompt_presets import (
    delete_builtin_prompt_override,
    delete_prompt_preset,
    load_builtin_prompt_overrides,
    load_prompt_presets,
    save_builtin_prompt_override,
    save_prompt_preset,
)


class PromptPresetStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "prompt_presets.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _save(
        self,
        name: str,
        *,
        preset_id: str | None = None,
        owner_id: str | None = None,
        wp_id: str | None = None,
    ) -> dict:
        return save_prompt_preset(
            self.path,
            name=name,
            system_prompt="sys",
            user_prompt_template="{question}",
            wp_id=wp_id,
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
        self.assertEqual(updated["id"], created["id"])

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

    def test_save_round_trips_note(self) -> None:
        record = save_prompt_preset(
            self.path,
            name="With note",
            note="Works best for short factual questions.",
            system_prompt="sys",
            user_prompt_template="{question}",
        )

        self.assertEqual(record["note"], "Works best for short factual questions.")
        self.assertEqual(load_prompt_presets(self.path)[0]["note"], record["note"])

    def test_load_normalizes_missing_note(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            '{"presets": [{"id": "p1", "name": "Old", "system_prompt": "", "user_prompt_template": ""}]}',
            encoding="utf-8",
        )

        self.assertEqual(load_prompt_presets(self.path)[0]["note"], "")

    def test_delete_removes_preset(self) -> None:
        created = self._save("Experiment", owner_id="owner-a")
        self.assertTrue(delete_prompt_preset(self.path, created["id"]))
        self.assertEqual(load_prompt_presets(self.path), [])

    def test_builtin_override_round_trips_without_copying_prompt(self) -> None:
        override = save_builtin_prompt_override(
            self.path,
            "wp1-ucitel",
            {
                "enabled": True,
                "actions": [
                    {
                        "id": "translate",
                        "description": "Translate the query.",
                        "type": "llm",
                        "prompt_template": "Translate: {question}",
                    }
                ],
            },
        )

        self.assertTrue(override["query_transform"]["enabled"])
        written = load_builtin_prompt_overrides(self.path)["wp1-ucitel"]
        self.assertEqual(written, override)
        raw = self.path.read_text(encoding="utf-8")
        self.assertNotIn('"system_prompt"', raw)
        self.assertNotIn('"user_prompt_template"', raw)

    def test_preset_writes_preserve_builtin_overrides(self) -> None:
        save_builtin_prompt_override(
            self.path,
            "wp1-ucitel",
            {"enabled": False, "actions": []},
        )

        created = self._save("Experiment", owner_id="owner-a")
        self._save("Experiment v2", preset_id=created["id"], owner_id="owner-a")
        delete_prompt_preset(self.path, created["id"])

        self.assertIn("wp1-ucitel", load_builtin_prompt_overrides(self.path))

    def test_deleting_builtin_override_preserves_saved_presets(self) -> None:
        created = self._save("Experiment", owner_id="owner-a")
        save_builtin_prompt_override(
            self.path,
            "wp1-ucitel",
            {"enabled": False, "actions": []},
        )

        self.assertTrue(delete_builtin_prompt_override(self.path, "wp1-ucitel"))
        self.assertFalse(delete_builtin_prompt_override(self.path, "wp1-ucitel"))
        self.assertEqual(load_prompt_presets(self.path)[0]["id"], created["id"])

    def test_save_records_wp_id(self) -> None:
        record = self._save("Scoped", wp_id="WP2-média")
        self.assertEqual(record["wp_id"], "WP2-média")
        self.assertEqual(load_prompt_presets(self.path)[0]["wp_id"], "WP2-média")

    def test_save_defaults_wp_id_when_omitted(self) -> None:
        record = self._save("Default scope")
        self.assertEqual(record["wp_id"], "WP1-historie")

    def test_update_preserves_existing_wp_id(self) -> None:
        created = self._save("Scoped", wp_id="WP3-právo")
        updated = self._save("Scoped v2", preset_id=created["id"])
        self.assertEqual(updated["wp_id"], "WP3-právo")

    def test_unknown_wp_id_falls_back_to_default(self) -> None:
        record = self._save("Bad scope", wp_id="WP9-nope")
        self.assertEqual(record["wp_id"], "WP1-historie")

    def test_save_round_trips_inline_placeholders(self) -> None:
        record = save_prompt_preset(
            self.path,
            name="Inline",
            system_prompt="Délka: {length}",
            user_prompt_template="{question}",
            placeholders={
                "length": {
                    "label": "Délka",
                    "kind": "select",
                    "default": "short",
                    "options": [{"name": "short", "label": "Krátká", "text": "INLINE short"}],
                }
            },
            owner_id="owner-a",
        )
        self.assertIn("length", record["placeholders"])
        loaded = load_prompt_presets(self.path)[0]
        self.assertEqual(loaded["placeholders"]["length"]["options"][0]["text"], "INLINE short")
        self.assertEqual(loaded["placeholders"]["length"]["kind"], "select")

    def test_save_round_trips_query_transform_override(self) -> None:
        record = save_prompt_preset(
            self.path,
            name="Translated persona",
            system_prompt="sys",
            user_prompt_template="{question}",
            query_transform={
                "enabled": True,
                "auto_apply": False,
                "default_action": "translate",
                "actions": [
                    {
                        "id": "translate",
                        "label": "Translate",
                        "description": "Translate the query to English.",
                        "type": "llm",
                        "prompt_template": "Translate to English: {question}",
                    }
                ],
            },
        )

        self.assertTrue(record["query_transform"]["enabled"])
        self.assertFalse(record["query_transform"]["auto_apply"])
        loaded = load_prompt_presets(self.path)[0]
        self.assertFalse(loaded["query_transform"]["auto_apply"])
        self.assertEqual(
            loaded["query_transform"]["actions"][0]["prompt_template"], "Translate to English: {question}"
        )
        self.assertEqual(
            loaded["query_transform"]["actions"][0]["description"], "Translate the query to English."
        )

    def test_query_transform_auto_apply_defaults_to_true_and_default_action_is_singular(self) -> None:
        record = save_prompt_preset(
            self.path,
            name="Automatic transform",
            system_prompt="sys",
            user_prompt_template="{question}",
            query_transform={
                "enabled": True,
                "default_action": "missing",
                "actions": [
                    {
                        "id": "first",
                        "label": "First",
                        "description": "First transformation.",
                        "type": "llm",
                        "prompt_template": "Transform: {question}",
                    },
                    {
                        "id": "second",
                        "label": "Second",
                        "description": "Second transformation.",
                        "type": "llm",
                        "prompt_template": "Rewrite: {question}",
                    },
                ],
            },
        )

        self.assertTrue(record["query_transform"]["auto_apply"])
        self.assertEqual(record["query_transform"]["default_action"], "first")

    def test_disabling_query_transform_preserves_configured_actions(self) -> None:
        record = save_prompt_preset(
            self.path,
            name="Temporarily disabled transform",
            system_prompt="sys",
            user_prompt_template="{question}",
            query_transform={
                "enabled": False,
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
        )

        self.assertFalse(record["query_transform"]["enabled"])
        self.assertEqual(record["query_transform"]["default_action"], "translate")
        self.assertEqual(len(record["query_transform"]["actions"]), 1)

    def test_missing_query_transform_inherits_as_null(self) -> None:
        record = self._save("Inherit WP")

        self.assertIsNone(record["query_transform"])
        self.assertIsNone(load_prompt_presets(self.path)[0]["query_transform"])

    def test_save_drops_legacy_length_prompts_field(self) -> None:
        record = self._save("Clean")
        self.assertNotIn("length_prompts", record)
        self.assertIn("placeholders", record)
        self.assertNotIn("length_prompts", load_prompt_presets(self.path)[0])

    def test_saved_record_drops_legacy_style_prompts(self) -> None:
        record = self._save("Clean")
        self.assertNotIn("style_prompts", record)
        self.assertNotIn("style_prompts", load_prompt_presets(self.path)[0])

    def test_load_missing_file_returns_empty(self) -> None:
        self.assertEqual(load_prompt_presets(self.path), [])

    def test_load_empty_file_returns_empty(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        self.assertEqual(load_prompt_presets(self.path), [])

    def test_load_malformed_file_returns_empty(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{ not valid json", encoding="utf-8")
        self.assertEqual(load_prompt_presets(self.path), [])

    def test_load_normalizes_legacy_record_to_new_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            '{"presets": [{"id": "p1", "name": "Old", "system_prompt": "",'
            ' "user_prompt_template": "", "style_prompts": {"ucitel": "x"}}]}',
            encoding="utf-8",
        )
        loaded = load_prompt_presets(self.path)[0]
        self.assertNotIn("style_prompts", loaded)
        self.assertEqual(loaded["wp_id"], "WP1-historie")


if __name__ == "__main__":
    unittest.main()
