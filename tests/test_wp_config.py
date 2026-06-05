from __future__ import annotations

import unittest

from app.rag.wp_config import (
    default_wp_id,
    get_wp_config,
    is_valid_wp_id,
    load_wp_configs,
    resolve_wp_id,
    wp_public_payload,
)


class WPConfigTests(unittest.TestCase):
    def test_loads_all_four_wps(self) -> None:
        ids = [wp.id for wp in load_wp_configs()]
        self.assertEqual(
            ids,
            ["WP1-historie", "WP2-média", "WP3-právo", "WP4-adiktologie"],
        )

    def test_default_wp_is_first(self) -> None:
        self.assertEqual(default_wp_id(), "WP1-historie")

    def test_each_wp_is_internally_consistent(self) -> None:
        for wp in load_wp_configs():
            prompt_ids = {prompt.id for prompt in wp.builtin_prompts}
            self.assertTrue(wp.builtin_prompts, f"{wp.id} has no built-in prompts")
            self.assertIn(wp.default_prompt_id, prompt_ids, f"{wp.id} default prompt missing")
            collection_ids = {collection.id for collection in wp.collections}
            self.assertIn(wp.default_collection_id, collection_ids, f"{wp.id} default collection missing")

    def test_wp1_keeps_history_built_in_prompts(self) -> None:
        wp1 = get_wp_config("WP1-historie")
        assert wp1 is not None
        names = {prompt.name for prompt in wp1.builtin_prompts}
        self.assertEqual(names, {"Učitel", "Historik", "Laik"})
        ucitel = next(prompt for prompt in wp1.builtin_prompts if prompt.id == "wp1-ucitel")
        # Style is baked in; the orthogonal length placeholder stays for chat-time rendering.
        self.assertNotIn("{style}", ucitel.system_prompt)
        self.assertIn("{length}", ucitel.system_prompt)

    def test_wp_collections_map_by_number(self) -> None:
        expected = {
            "WP1-historie": "64d6f521-5044-4b02-8658-380b639801af",
            "WP2-média": "ab79b4f6-6a91-45a3-908e-edb2c771d3b0",
            "WP3-právo": "d4be44d5-689c-4bbe-a372-b959929cd511",
            "WP4-adiktologie": "3429956e-8a21-4502-ad21-a41fddc5ef99",
        }
        for wp in load_wp_configs():
            default_collection = next(c for c in wp.collections if c.id == wp.default_collection_id)
            self.assertEqual(default_collection.msearch_collection_id, expected[wp.id])

    def test_resolve_wp_id_falls_back_to_default(self) -> None:
        self.assertEqual(resolve_wp_id("WP3-právo"), "WP3-právo")
        self.assertEqual(resolve_wp_id("does-not-exist"), default_wp_id())
        self.assertEqual(resolve_wp_id(None), default_wp_id())
        self.assertEqual(resolve_wp_id("  "), default_wp_id())

    def test_is_valid_wp_id(self) -> None:
        self.assertTrue(is_valid_wp_id("WP2-média"))
        self.assertFalse(is_valid_wp_id("WP9-nope"))

    def test_public_payload_is_json_serializable_shape(self) -> None:
        payload = wp_public_payload()
        self.assertEqual(len(payload), 4)
        first = payload[0]
        self.assertEqual(
            set(first),
            {
                "id",
                "label",
                "description",
                "builtin_prompts",
                "default_prompt_id",
                "collections",
                "default_collection_id",
                "placeholders",
            },
        )
        self.assertEqual(
            set(first["builtin_prompts"][0]),
            {"id", "name", "system_prompt", "user_prompt_template", "placeholders"},
        )


if __name__ == "__main__":
    unittest.main()
