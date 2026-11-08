from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.rag.prompts import OptionDef, PlaceholderDef
from app.rag.wp_config import (
    InstanceConfigError,
    default_wp_id,
    get_wp_config,
    is_valid_wp_id,
    load_instance_config,
    load_wp_configs,
    parse_instance_config,
    resolve_wp_id,
    restricted_collection_prefixes,
    restricted_msearch_collection_ids,
    wp_allowed_providers,
    wp_collection_prefixes,
    wp_public_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

MINIMAL = {
    "wps": [
        {
            "id": "A",
            "collections": [{"id": "a-docs", "msearch_collection_id": "id-a"}],
            "prompts": [{"id": "a-p", "name": "P", "system_prompt": "S", "user_prompt_template": "{question}"}],
        }
    ]
}


def _minimal(**wp_fields: object) -> dict:
    data = copy.deepcopy(MINIMAL)
    data["wps"][0].update(wp_fields)
    return data


class ActiveInstanceTests(unittest.TestCase):
    """The test fixture (tests/fixtures/instance.toml) is the active instance."""

    def test_loads_the_fixture_wps_in_order(self) -> None:
        self.assertEqual([wp.id for wp in load_wp_configs()], ["WP1-historie", "WP2-média", "WP3-právo"])

    def test_default_wp_is_first(self) -> None:
        self.assertEqual(default_wp_id(), "WP1-historie")

    def test_resolve_wp_id_falls_back_to_default(self) -> None:
        self.assertEqual(resolve_wp_id("WP3-právo"), "WP3-právo")
        self.assertEqual(resolve_wp_id("does-not-exist"), default_wp_id())
        self.assertEqual(resolve_wp_id(None), default_wp_id())
        self.assertEqual(resolve_wp_id("  "), default_wp_id())

    def test_is_valid_wp_id(self) -> None:
        self.assertTrue(is_valid_wp_id("WP2-média"))
        self.assertFalse(is_valid_wp_id("WP9-nope"))

    def test_provider_restriction_comes_from_the_file(self) -> None:
        self.assertEqual(wp_allowed_providers("WP2-média"), ["test"])
        self.assertIsNone(wp_allowed_providers("WP1-historie"))
        self.assertIsNone(wp_allowed_providers("unknown"))
        self.assertEqual(restricted_collection_prefixes(), {"wp2": ["test"]})
        self.assertEqual(restricted_msearch_collection_ids(), {"00000000-0000-4000-8000-000000000002": ["test"]})
        self.assertEqual(wp_collection_prefixes(), {"wp1", "wp2", "wp3"})

    def test_public_payload_shape(self) -> None:
        payload = wp_public_payload()
        self.assertEqual(len(payload), 3)
        self.assertEqual(
            set(payload[0]),
            {
                "id",
                "label",
                "description",
                "builtin_prompts",
                "default_prompt_id",
                "collections",
                "default_collection_id",
                "collection_prefix",
                "questions",
                "local_retrieval_enabled",
                "placeholders",
                "allowed_providers",
            },
        )
        self.assertEqual(
            set(payload[0]["builtin_prompts"][0]),
            {"id", "name", "system_prompt", "user_prompt_template", "placeholders"},
        )
        self.assertEqual(payload[1]["allowed_providers"], ["test"])
        self.assertIsNone(payload[0]["allowed_providers"])

    def test_prompt_text_is_kept_verbatim(self) -> None:
        wp1 = get_wp_config("WP1-historie")
        assert wp1 is not None
        ucitel = next(prompt for prompt in wp1.builtin_prompts if prompt.id == "wp1-ucitel")
        self.assertEqual(ucitel.system_prompt, "Jsi testovací učitel. Cituj zdroje jako [^Z1].\n\nDélka: {length}")


class ExampleFileTests(unittest.TestCase):
    def test_the_tracked_example_file_is_valid(self) -> None:
        instance = load_instance_config(REPO_ROOT / "instance.example.toml")
        self.assertTrue(instance.wps)


class LoaderTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "instance.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_no_path_explains_what_to_set(self) -> None:
        for value in (None, "", "."):
            with self.subTest(value=value), self.assertRaises(InstanceConfigError) as raised:
                load_instance_config(value)
            self.assertIn("INSTANCE_CONFIG_PATH", str(raised.exception))
            self.assertIn("instance.example.toml", str(raised.exception))

    def test_missing_file_is_an_error(self) -> None:
        with self.assertRaises(InstanceConfigError) as raised:
            load_instance_config("/does/not/exist.toml")
        self.assertIn("was not found", str(raised.exception))

    def test_invalid_toml_is_an_error(self) -> None:
        with self.assertRaises(InstanceConfigError) as raised:
            load_instance_config(self._write("[[wps]\nid = "))
        self.assertIn("could not be read", str(raised.exception))

    def test_literal_strings_keep_the_text_verbatim(self) -> None:
        path = self._write(
            "[[wps]]\nid = 'A'\n"
            "[[wps.collections]]\nid = 'c'\nmsearch_collection_id = 'm'\n"
            "[[wps.prompts]]\nid = 'p'\nname = 'P'\n"
            "system_prompt = '''\nŘádek \\n bez escape.  \n\n  Odsazení {length} '''\n"
            "user_prompt_template = '''\n{question}'''\n"
        )
        prompt = load_instance_config(path).wps[0].builtin_prompts[0]
        self.assertEqual(prompt.system_prompt, "Řádek \\n bez escape.  \n\n  Odsazení {length} ")
        self.assertEqual(prompt.user_prompt_template, "{question}")

    def test_minimal_file_gets_defaults(self) -> None:
        instance = parse_instance_config(_minimal())
        wp = instance.wps[0]
        self.assertTrue(instance.shared_presets)
        self.assertEqual(wp.label, "A")
        self.assertEqual(wp.default_prompt_id, "a-p")
        self.assertEqual(wp.default_collection_id, "a-docs")
        self.assertEqual(wp.questions, [])
        self.assertEqual(wp.collection_prefix, "")
        self.assertIsNone(wp.allowed_providers)
        self.assertFalse(wp.local_retrieval_enabled)

    def test_values_are_normalized(self) -> None:
        wp = parse_instance_config(
            _minimal(
                collection_prefix=" Kurz ",
                allowed_providers=[" AIUfal "],
                questions=["  Jedna?  ", "", "   "],
            )
        ).wps[0]
        self.assertEqual(wp.collection_prefix, "kurz")
        self.assertEqual(wp.allowed_providers, ["aiufal"])
        self.assertEqual(wp.questions, ["Jedna?"])

    def test_shared_presets_switch(self) -> None:
        self.assertFalse(parse_instance_config({**_minimal(), "shared_presets": False}).shared_presets)

    def test_placeholders_are_parsed(self) -> None:
        prompt = {
            "id": "a-p",
            "name": "P",
            "system_prompt": "{tone}",
            "user_prompt_template": "{question}",
            "placeholders": {
                "tone": {
                    "label": "Tón",
                    "kind": "select",
                    "default": "calm",
                    "options": [{"name": "calm", "label": "Klidný", "text": "Piš klidně."}],
                }
            },
        }
        parsed = parse_instance_config(_minimal(prompts=[prompt])).wps[0].builtin_prompts[0]
        self.assertEqual(
            parsed.placeholders,
            {
                "tone": PlaceholderDef(
                    label="Tón",
                    kind="select",
                    default="calm",
                    options=[OptionDef(name="calm", label="Klidný", text="Piš klidně.")],
                )
            },
        )

    def test_invalid_files_are_rejected(self) -> None:
        second = copy.deepcopy(MINIMAL["wps"][0])
        second["prompts"][0]["id"] = "b-p"
        same_prompt = copy.deepcopy(MINIMAL["wps"][0])
        same_prompt["id"] = "B"
        cases = {
            "no wps": ({}, "at least one [[wps]]"),
            "unknown top key": ({**_minimal(), "wp": []}, "unknown key(s) wp"),
            "unknown wp key": (_minimal(requires_aiufal=True), "unknown key(s) requires_aiufal"),
            "duplicate wp": ({"wps": [MINIMAL["wps"][0], second]}, "duplicate WP id 'A'"),
            "duplicate prompt": ({"wps": [MINIMAL["wps"][0], same_prompt]}, "duplicate prompt id 'a-p'"),
            "no prompts": (_minimal(prompts=[]), "at least one [[wps.prompts]]"),
            "no collections": (_minimal(collections=[]), "at least one [[wps.collections]]"),
            "default prompt": (_minimal(default_prompt="nope"), "default_prompt 'nope'"),
            "default collection": (_minimal(default_collection="nope"), "default_collection 'nope'"),
            "empty providers": (_minimal(allowed_providers=[]), "allowed_providers"),
            "provider not a string": (_minimal(allowed_providers=[1]), "allowed_providers"),
            "prefix with dash": (_minimal(collection_prefix="wp-1"), "collection_prefix"),
            "questions not strings": (_minimal(questions="Jedna?"), "questions"),
            "shared_presets not bool": ({**_minimal(), "shared_presets": "no"}, "shared_presets"),
            "empty system prompt": (
                _minimal(prompts=[{"id": "a-p", "name": "P", "system_prompt": "  ", "user_prompt_template": "{question}"}]),
                "system_prompt",
            ),
            "bad placeholder kind": (
                _minimal(
                    placeholders={"tone": {"kind": "radio"}},
                ),
                "kind must be",
            ),
        }
        for name, (data, message) in cases.items():
            with self.subTest(name), self.assertRaises(InstanceConfigError) as raised:
                parse_instance_config(data)
            self.assertIn(message, str(raised.exception))

    def test_two_restricted_wps_keep_their_own_providers(self) -> None:
        second = copy.deepcopy(MINIMAL["wps"][0])
        second.update(id="B", collection_prefix="b", allowed_providers=["other"])
        second["prompts"][0]["id"] = "b-p"
        second["collections"][0]["msearch_collection_id"] = "id-b"
        instance = parse_instance_config(
            {"wps": [{**MINIMAL["wps"][0], "collection_prefix": "a", "allowed_providers": ["one"]}, second]}
        )
        with patch("app.rag.wp_config._instance", instance):
            self.assertEqual(restricted_collection_prefixes(), {"a": ["one"], "b": ["other"]})
            self.assertEqual(restricted_msearch_collection_ids(), {"id-a": ["one"], "id-b": ["other"]})


if __name__ == "__main__":
    unittest.main()
