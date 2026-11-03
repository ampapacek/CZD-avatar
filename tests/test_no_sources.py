"""Answering without sources ("Bez zdrojů"): the bare model, no retrieval."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.rag.llm import LLMGeneration
from app.rag.pipeline import RAGPipeline
from app.rag.placeholders import DEFAULT_PLACEHOLDERS
from app.rag.prompt_presets import load_prompt_presets, save_prompt_preset
from app.rag.prompts import (
    build_messages,
    default_no_sources_system_prompt,
    default_no_sources_user_prompt_template,
)
from app.rag.wp_config import WP_CONFIGS, gated_msearch_collection_ids, get_wp_config


class _FakeLLM:
    model = "fake-model"

    def __init__(self) -> None:
        self.calls = []

    def generate(self, messages, model=None, api_key=None, base_url=None, reasoning=None):
        self.calls.append(messages)
        return LLMGeneration(answer="answer", model=model)


class NoSourcesMessagesTests(unittest.TestCase):
    def test_empty_system_prompt_sends_no_system_message(self) -> None:
        messages = build_messages("Kdo byl Jan Hus?", [], system_prompt="", use_sources=False)

        self.assertEqual(messages, [{"role": "user", "content": "Kdo byl Jan Hus?"}])

    def test_system_prompt_is_rendered_without_any_context(self) -> None:
        messages = build_messages(
            "Kdo byl Jan Hus?",
            [{"chunk_id": "c1", "text": "Should never reach the prompt", "metadata": {}}],
            placeholder_defs={"length": DEFAULT_PLACEHOLDERS["length"]},
            selections={"length": "short"},
            system_prompt=default_no_sources_system_prompt(),
            user_prompt_template="{question}\n{retrieved_snippets}",
            use_sources=False,
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertNotIn("{length}", messages[0]["content"])
        self.assertIn("Markdown", messages[0]["content"])
        rendered = "\n".join(message["content"] for message in messages)
        self.assertNotIn("Should never reach the prompt", rendered)
        self.assertNotIn("Nebyly nalezeny", rendered)
        self.assertEqual(messages[-1]["content"], "Kdo byl Jan Hus?")

    def test_with_sources_an_empty_system_prompt_still_falls_back_to_the_default(self) -> None:
        messages = build_messages("Otázka?", [], system_prompt="")

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("RAG", messages[0]["content"])


class NoSourcesPipelineTests(unittest.TestCase):
    def _pipeline(self) -> tuple[RAGPipeline, _FakeLLM]:
        pipeline = RAGPipeline(get_settings())
        llm = _FakeLLM()
        pipeline._llm = llm
        return pipeline, llm

    def test_chat_skips_retrieval_and_the_conversation_rewrite(self) -> None:
        pipeline, llm = self._pipeline()
        pipeline.msearch_retriever.retrieve = lambda *args, **kwargs: self.fail("must not retrieve")

        response = pipeline.chat(
            "A co potom?",
            "medium",
            conversation_history=[
                {"role": "user", "content": "Kdo byl Jan Hus?"},
                {"role": "assistant", "content": "Reformátor."},
            ],
            top_k=10,
            model="selected-model",
            rewrite_query_for_retrieval=True,
            use_sources=False,
        )

        # Only the answer call: no query rewrite, no retrieval.
        self.assertEqual(len(llm.calls), 1)
        self.assertNotEqual(llm.calls[0][0]["role"], "system")
        self.assertEqual(llm.calls[0][-1], {"role": "user", "content": "A co potom?"})
        self.assertEqual(response.sources, [])
        self.assertFalse(response.retrieval_query_rewrite_attempted)
        self.assertEqual(response.retrieval_query_rewrite_skip_reason, "no_sources")

    def test_a_query_transform_can_still_drive_the_answer(self) -> None:
        pipeline, llm = self._pipeline()

        response = pipeline.chat(
            "Původní dotaz",
            "medium",
            top_k=10,
            model="selected-model",
            retrieval_query_override="Translated question",
            use_retrieval_query_for_answer=True,
            use_sources=False,
        )

        self.assertEqual(response.answer_question, "Translated question")
        self.assertEqual(llm.calls[0][-1]["content"], "Translated question")


class NoSourcesEndpointTests(unittest.TestCase):
    def test_stream_skips_retrieval_and_the_ai_ufal_gate(self) -> None:
        from app import main

        upstream_bodies = []

        def stream_handler(request):
            upstream_bodies.append(json.loads(request.content))
            return httpx.Response(
                200,
                request=request,
                text='data: {"choices":[{"delta":{"content":"answer"}}]}\n\ndata: [DONE]\n\n',
                headers={"content-type": "text/event-stream"},
            )

        with (
            # A non-AI-Ufal provider together with a gated WP2 collection.
            patch("app.main._resolve_llm_request", return_value=(
                "provider-1", "requested-model", "server-key", "https://provider.example/v1"
            )),
            patch.object(main.pipeline.msearch_retriever, "retrieve", side_effect=AssertionError("retrieved")),
            patch(
                "app.rag.llm.httpx.Client",
                return_value=httpx.Client(transport=httpx.MockTransport(stream_handler)),
            ),
        ):
            response = TestClient(main.app).post(
                "/chat/stream",
                json={
                    "question": "Co je mediální gramotnost?",
                    "wp_id": "WP2-média",
                    "msearch_collection": next(iter(gated_msearch_collection_ids())),
                    "use_sources": False,
                    "system_prompt": "",
                    "user_prompt_template": "{question}",
                    "top_k": 10,
                },
            )

        events = [line for line in response.text.splitlines() if line.startswith("event: ")]
        self.assertIn("event: done", events)
        self.assertNotIn("event: error", events)
        self.assertNotIn('"phase": "retrieval"', response.text)
        self.assertEqual(
            upstream_bodies[0]["messages"],
            [{"role": "user", "content": "Co je mediální gramotnost?"}],
        )

    def test_settings_expose_no_sources_defaults_and_prompt_flags(self) -> None:
        from app import main

        data = TestClient(main.app).get("/settings").json()

        self.assertEqual(
            data["prompt_defaults"]["no_sources"],
            {
                "system_prompt": default_no_sources_system_prompt(),
                "user_prompt_template": default_no_sources_user_prompt_template(),
            },
        )
        for wp in data["wps"]:
            flags = [prompt["uses_sources"] for prompt in wp["builtin_prompts"]]
            self.assertIn(False, flags, wp["id"])


class NoSourcesPromptConfigTests(unittest.TestCase):
    def test_every_wp_ships_one_generic_prompt_without_sources(self) -> None:
        for wp in WP_CONFIGS:
            without = [prompt for prompt in wp.builtin_prompts if not prompt.uses_sources]
            self.assertEqual(len(without), 1, wp.id)
            self.assertEqual(without[0].system_prompt, default_no_sources_system_prompt())
            default = next(prompt for prompt in wp.builtin_prompts if prompt.id == wp.default_prompt_id)
            self.assertTrue(default.uses_sources, wp.id)
        ids = [prompt.id for wp in WP_CONFIGS for prompt in wp.builtin_prompts]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIsNotNone(get_wp_config("WP1-historie"))

    def test_presets_keep_the_flag_and_older_ones_use_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt_presets.json"
            path.write_text(
                json.dumps({"presets": [{"id": "old", "name": "Old", "system_prompt": "s", "user_prompt_template": "u"}]}),
                encoding="utf-8",
            )
            save_prompt_preset(path, name="Bare", system_prompt="", user_prompt_template="{question}", uses_sources=False)

            presets = {preset["id"]: preset for preset in load_prompt_presets(path)}

        self.assertIs(presets["old"]["uses_sources"], True)
        self.assertIs(presets["bare"]["uses_sources"], False)
        self.assertEqual(presets["bare"]["system_prompt"], "")


if __name__ == "__main__":
    unittest.main()
