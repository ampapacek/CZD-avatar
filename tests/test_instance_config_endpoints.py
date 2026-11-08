"""The endpoints follow the instance config: provider restriction, unknown WPs,
the shared presets switch and the startup check."""

from __future__ import annotations

import dataclasses
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.rag import wp_config

PROVIDERS = [
    {"id": "test", "label": "Test provider", "base_url": "https://llm.test.invalid/v1"},
    {"id": "other", "label": "Other provider", "base_url": "https://other.test.invalid/v1"},
]
RESTRICTED_COLLECTION = "00000000-0000-4000-8000-000000000002"  # WP2-média, allowed: test
OPEN_COLLECTION = "00000000-0000-4000-8000-000000000001"  # WP1-historie


class ProviderRestrictionTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.object(main, "provider_presets", PROVIDERS)
        patcher.start()
        self.addCleanup(patcher.stop)
        # No live mSearch list in tests: only the configured ids count.
        live = patch.object(main.pipeline.msearch_retriever, "restricted_collection_ids", return_value={})
        live.start()
        self.addCleanup(live.stop)

    def _check(self, wp_id: str | None, collection: str, provider: str, base_url: str) -> None:
        main._enforce_msearch_collection_policy(wp_id, collection, provider, base_url)

    def test_allowed_provider_passes(self) -> None:
        self._check("WP2-média", RESTRICTED_COLLECTION, "test", "https://llm.test.invalid/v1/")

    def test_other_provider_is_refused(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._check("WP2-média", RESTRICTED_COLLECTION, "other", "https://other.test.invalid/v1")
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("Test provider", raised.exception.detail)

    def test_allowed_id_with_a_custom_url_is_refused(self) -> None:
        with self.assertRaises(HTTPException):
            self._check("WP2-média", RESTRICTED_COLLECTION, "test", "https://elsewhere.invalid/v1")

    def test_forged_wp_id_does_not_unlock_a_restricted_collection(self) -> None:
        with self.assertRaises(HTTPException):
            self._check("WP1-historie", RESTRICTED_COLLECTION, "other", "https://other.test.invalid/v1")

    def test_live_collections_of_a_restricted_wp_are_restricted(self) -> None:
        with patch.object(
            main.pipeline.msearch_retriever, "restricted_collection_ids", return_value={"live-wp2": ["test"]}
        ):
            with self.assertRaises(HTTPException):
                self._check(None, "live-wp2", "other", "https://other.test.invalid/v1")

    def test_unrestricted_wp_takes_any_provider(self) -> None:
        self._check("WP1-historie", OPEN_COLLECTION, "other", "https://other.test.invalid/v1")


class UnknownWpTests(unittest.TestCase):
    def test_chat_refuses_a_wp_the_file_does_not_define(self) -> None:
        response = TestClient(main.app).post("/chat", json={"question": "Cokoliv?", "wp_id": "WP9-jinde"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("WP9-jinde", response.json()["detail"])

    def test_settings_lists_only_the_configured_wps(self) -> None:
        instance = wp_config.instance_config()
        wp_config.set_instance_config(dataclasses.replace(instance, wps=instance.wps[:1]))
        with patch.object(main.pipeline.msearch_retriever, "live_collections_by_prefix", return_value={}):
            payload = TestClient(main.app).get("/settings").json()
        self.assertEqual([wp["id"] for wp in payload["wps"]], ["WP1-historie"])
        self.assertEqual(payload["default_wp"], "WP1-historie")
        self.assertEqual(payload["shared_presets"], True)


class SharedPresetsSwitchTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        original = main.settings.prompt_presets_path
        main.settings.prompt_presets_path = Path(tmp.name) / "prompt_presets.json"
        self.addCleanup(setattr, main.settings, "prompt_presets_path", original)
        self.client = TestClient(main.app)
        created = self.client.post(
            "/prompt-presets",
            json={"name": "Sdílený", "system_prompt": "sys", "user_prompt_template": "{question}", "owner_id": "a"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        self.preset_id = created.json()["id"]

    def _switch_off(self) -> None:
        wp_config.set_instance_config(dataclasses.replace(wp_config.instance_config(), shared_presets=False))

    def test_on_lists_the_shared_presets(self) -> None:
        self.assertEqual([p["id"] for p in self.client.get("/prompt-presets").json()], [self.preset_id])

    def test_off_lists_none_and_refuses_changes(self) -> None:
        self._switch_off()
        self.assertEqual(self.client.get("/prompt-presets").json(), [])
        saved = self.client.post(
            "/prompt-presets",
            json={"name": "Nový", "system_prompt": "sys", "user_prompt_template": "{question}", "owner_id": "a"},
        )
        self.assertEqual(saved.status_code, 403)
        deleted = self.client.delete(f"/prompt-presets/{self.preset_id}", params={"owner_id": "a"})
        self.assertEqual(deleted.status_code, 403)
        self.assertFalse(self.client.get("/settings").json()["shared_presets"])

    def test_saving_for_an_unknown_wp_is_refused(self) -> None:
        response = self.client.post(
            "/prompt-presets",
            json={"name": "Jinde", "system_prompt": "s", "user_prompt_template": "{question}", "wp_id": "WP9-jinde"},
        )
        self.assertEqual(response.status_code, 400)


class StartupTests(unittest.TestCase):
    def test_no_config_refuses_to_start_with_help(self) -> None:
        with patch.object(main.settings, "instance_config_path", None), self.assertRaises(SystemExit) as raised:
            main._load_instance()
        self.assertIn("INSTANCE_CONFIG_PATH", str(raised.exception.code))
        self.assertIn("instance.example.toml", str(raised.exception.code))

    def test_unknown_allowed_provider_refuses_to_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "instance.toml"
            path.write_text(
                "[[wps]]\nid = 'A'\nallowed_providers = ['nope']\n"
                "[[wps.collections]]\nid = 'c'\nmsearch_collection_id = 'm'\n"
                "[[wps.prompts]]\nid = 'p'\nname = 'P'\nsystem_prompt = 's'\nuser_prompt_template = '{question}'\n",
                encoding="utf-8",
            )
            with patch.object(main.settings, "instance_config_path", path), self.assertRaises(SystemExit) as raised:
                main._load_instance()
        self.assertIn("nope", str(raised.exception.code))


class RestrictedChatEndToEndTests(unittest.TestCase):
    def test_chat_with_a_custom_url_on_a_restricted_collection_is_refused(self) -> None:
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))]
        with (
            patch("socket.getaddrinfo", return_value=public),
            patch.object(main.pipeline.msearch_retriever, "restricted_collection_ids", return_value={}),
        ):
            response = TestClient(main.app).post(
                "/chat",
                json={
                    "question": "Cokoliv?",
                    "wp_id": "WP2-média",
                    "msearch_collection": RESTRICTED_COLLECTION,
                    "llm_provider": "test",
                    "llm_base_url": "https://example.com/api",
                },
            )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Test provider", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
