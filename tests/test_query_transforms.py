import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from app import main
from app.rag.llm import LLMGeneration
from app.rag.query_transforms import render_query_transform_prompt


class RenderQueryTransformPromptTests(unittest.TestCase):
    def test_substitutes_both_tokens(self) -> None:
        rendered = render_query_transform_prompt(
            "Instrukce: {instruction}\nDotaz: {question}", "Původní dotaz", "Přelož do angličtiny"
        )
        self.assertEqual(rendered, "Instrukce: Přelož do angličtiny\nDotaz: Původní dotaz")

    def test_question_containing_instruction_token_is_left_untouched(self) -> None:
        rendered = render_query_transform_prompt(
            "{instruction} :: {question}", "please use {instruction} nicely", "TRANSLATE"
        )
        self.assertEqual(rendered, "TRANSLATE :: please use {instruction} nicely")

    def test_instruction_containing_question_token_is_left_untouched(self) -> None:
        rendered = render_query_transform_prompt(
            "{instruction} :: {question}", "original", "use {question} verbatim"
        )
        self.assertEqual(rendered, "use {question} verbatim :: original")


class QueryTransformEndpointTests(unittest.TestCase):
    """These rely on WP4-adiktologie's real, hardcoded query_transform config

    (``app.rag.wp_config.WP_CONFIGS``), which ships the ``charles-cs-en``
    lindat action and the ``llm-query-transform`` LLM action.
    """

    def setUp(self) -> None:
        self.client = TestClient(main.app, raise_server_exceptions=False)

    @patch("app.main.httpx.post")
    def test_wp4_lindat_action_sends_multipart_input_text(self, post: Mock) -> None:
        post.return_value = httpx.Response(
            200,
            text="How does alcohol affect sleep?",
            request=httpx.Request("POST", "https://lindat.example/cs-en"),
        )

        response = self.client.post(
            "/query-transform",
            json={
                "question": "Jak alkohol ovlivňuje spánek?",
                "wp_id": "WP4-adiktologie",
                "action_id": "charles-cs-en",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["transformed_query"], "How does alcohol affect sleep?")
        self.assertEqual(response.json()["action_type"], "lindat")
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["files"]["input_text"], (None, "Jak alkohol ovlivňuje spánek?"))
        self.assertEqual(kwargs["timeout"], main.settings.query_transform_timeout)
        self.assertTrue(post.call_args.args[0].endswith("/cs-en"))

    def test_inline_llm_action_uses_editable_instruction(self) -> None:
        fake_llm = Mock()
        fake_llm.generate.return_value = LLMGeneration(answer='"translated query"', model="selected-model")
        original_llm = main.pipeline._llm
        main.pipeline._llm = fake_llm
        try:
            with patch(
                "app.main._resolve_llm_request",
                return_value=("provider", "selected-model", "key", "https://llm.example/v1"),
            ):
                response = self.client.post(
                    "/query-transform",
                    json={
                        "question": "Původní dotaz",
                        "prompt_preset_id": "local-test-persona",
                        "instruction": "Custom instruction",
                        "action": {
                            "id": "local-llm",
                            "label": "Local",
                            "description": "Transform the query using the supplied instruction.",
                            "type": "llm",
                            "prompt_template": "Instrukce: {instruction}\nDotaz: {question}\nVrať pouze upravený dotaz.",
                        },
                    },
                )
        finally:
            main.pipeline._llm = original_llm

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["transformed_query"], "translated query")
        call = fake_llm.generate.call_args
        self.assertEqual(len(call.args[0]), 1)
        self.assertEqual(call.args[0][0]["role"], "user")
        self.assertEqual(
            call.args[0][0]["content"],
            "Instrukce: Custom instruction\nDotaz: Původní dotaz\nVrať pouze upravený dotaz.",
        )
        self.assertEqual(call.kwargs["model"], "selected-model")

    def test_question_containing_literal_instruction_token_is_not_corrupted(self) -> None:
        # Regression test: chained str.replace("{question}", ...).replace("{instruction}", ...)
        # would rescan the already-substituted question text for a literal
        # "{instruction}" and clobber it with the instruction value.
        fake_llm = Mock()
        fake_llm.generate.return_value = LLMGeneration(answer="translated query", model="selected-model")
        original_llm = main.pipeline._llm
        main.pipeline._llm = fake_llm
        try:
            with patch(
                "app.main._resolve_llm_request",
                return_value=("provider", "selected-model", "key", "https://llm.example/v1"),
            ):
                response = self.client.post(
                    "/query-transform",
                    json={
                        "question": "Co mám napsat do pole {instruction} ve formuláři?",
                        "prompt_preset_id": "local-test-persona",
                        "instruction": "Custom instruction",
                        "action": {
                            "id": "local-llm",
                            "label": "Local",
                            "description": "Transform the query using the supplied instruction.",
                            "type": "llm",
                            "prompt_template": "Instrukce: {instruction}\nDotaz: {question}",
                        },
                    },
                )
        finally:
            main.pipeline._llm = original_llm

        self.assertEqual(response.status_code, 200, response.text)
        call = fake_llm.generate.call_args
        self.assertEqual(
            call.args[0][0]["content"],
            "Instrukce: Custom instruction\nDotaz: Co mám napsat do pole {instruction} ve formuláři?",
        )

    def test_llm_action_without_question_placeholder_is_rejected(self) -> None:
        fake_llm = Mock()
        original_llm = main.pipeline._llm
        main.pipeline._llm = fake_llm
        try:
            with patch(
                "app.main._resolve_llm_request",
                return_value=("provider", "selected-model", "key", "https://llm.example/v1"),
            ):
                response = self.client.post(
                    "/query-transform",
                    json={
                        "question": "Původní dotaz",
                        "prompt_preset_id": "local-test-persona",
                        "instruction": "translate to english",
                        "action": {
                            "id": "local-llm",
                            "label": "Local",
                            "description": "Transform the query using the supplied instruction.",
                            "type": "llm",
                            "prompt_template": "{instruction}",
                        },
                    },
                )
        finally:
            main.pipeline._llm = original_llm

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("{question}", response.json()["detail"])
        fake_llm.generate.assert_not_called()

    def test_inline_action_cannot_bypass_disabled_server_profile(self) -> None:
        response = self.client.post(
            "/query-transform",
            json={
                "question": "Kdo byl Jan Hus?",
                "wp_id": "WP1-historie",
                "prompt_preset_id": "wp1-ucitel",
                "action": {
                    "id": "inline-llm",
                    "label": "Inline",
                    "description": "Transform the query with an LLM.",
                    "type": "llm",
                    "prompt_template": "Translate {question}",
                },
            },
        )

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("není pro tento profil povolena", response.json()["detail"])

    @patch("app.main.httpx.post", side_effect=httpx.ConnectError("offline"))
    def test_upstream_failure_returns_actionable_502(self, _post: Mock) -> None:
        response = self.client.post(
            "/query-transform",
            json={
                "question": "Jak alkohol ovlivňuje spánek?",
                "wp_id": "WP4-adiktologie",
                "action_id": "charles-cs-en",
            },
        )

        self.assertEqual(response.status_code, 502, response.text)
        self.assertIn("Původní dotaz zůstal beze změny", response.json()["detail"])

    def test_disabled_wp_has_no_server_resolved_action(self) -> None:
        response = self.client.post(
            "/query-transform",
            json={
                "question": "Kdo byl Jan Hus?",
                "wp_id": "WP1-historie",
                "action_id": "charles-cs-en",
            },
        )

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("není pro tento profil povolena", response.json()["detail"])

    def test_wp4_configuration_is_exposed_without_hardcoded_endpoint_logic(self) -> None:
        with patch.object(main.pipeline.msearch_retriever, "live_collections_by_prefix", return_value={}):
            wps = main._wps_payload_with_live_collections()

        wp4 = next(wp for wp in wps if wp["id"] == "WP4-adiktologie")
        wp1 = next(wp for wp in wps if wp["id"] == "WP1-historie")
        self.assertTrue(wp4["query_transform"]["enabled"])
        self.assertEqual(
            [action["id"] for action in wp4["query_transform"]["actions"]],
            ["charles-cs-en", "llm-query-transform"],
        )
        self.assertTrue(
            all(action["description"] for action in wp4["query_transform"]["actions"])
        )
        self.assertFalse(wp1["query_transform"]["enabled"])


class RetrievalQueryEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app, raise_server_exceptions=False)

    def test_retrieve_uses_explicit_query_and_preserves_original_metadata(self) -> None:
        calls: list[str] = []
        original = main.pipeline.retrieve_with_baseline

        def fake_retrieve(question, *args, **kwargs):
            calls.append(question)
            return [], []

        main.pipeline.retrieve_with_baseline = fake_retrieve
        try:
            response = self.client.post(
                "/retrieve",
                json={
                    "question": "Jak alkohol ovlivňuje spánek?",
                    "retrieval_query": "How does alcohol affect sleep?",
                },
            )
        finally:
            main.pipeline.retrieve_with_baseline = original

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(calls, ["How does alcohol affect sleep?"])
        self.assertEqual(response.json()["original_question"], "Jak alkohol ovlivňuje spánek?")
        self.assertEqual(response.json()["retrieval_query"], "How does alcohol affect sleep?")

    def test_empty_explicit_chat_retrieval_query_returns_400(self) -> None:
        response = self.client.post(
            "/chat",
            json={"question": "Original", "retrieval_query": "   "},
        )

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("nesmí být prázdný", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
