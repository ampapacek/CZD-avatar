"""Answering without sources ("Bez zdrojů"): retrieval off, the same as top_k=0."""

import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.rag.llm import LLMGeneration
from app.rag.pipeline import RAGPipeline
from app.rag.prompts import NO_SOURCES_CONTEXT, build_messages
from app.rag.wp_config import restricted_msearch_collection_ids


class _FakeLLM:
    model = "fake-model"

    def __init__(self) -> None:
        self.calls = []

    def generate(self, messages, model=None, api_key=None, base_url=None, reasoning=None):
        self.calls.append(messages)
        return LLMGeneration(answer="answer", model=model)


class NoSourcesMessagesTests(unittest.TestCase):
    def test_empty_context_tells_the_model_to_answer_from_its_knowledge(self) -> None:
        messages = build_messages("Kdo byl Jan Hus?", [], user_prompt_template="{question}\n{retrieved_snippets}")

        self.assertEqual(messages[-1]["content"], f"Kdo byl Jan Hus?\n{NO_SOURCES_CONTEXT}")

    def test_empty_prompts_fall_back_to_the_defaults(self) -> None:
        messages = build_messages("Otázka?", [], system_prompt="", user_prompt_template="")

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("RAG", messages[0]["content"])
        self.assertIn(NO_SOURCES_CONTEXT, messages[-1]["content"])


class NoSourcesPipelineTests(unittest.TestCase):
    def _pipeline(self) -> tuple[RAGPipeline, _FakeLLM]:
        pipeline = RAGPipeline(get_settings())
        llm = _FakeLLM()
        pipeline._llm = llm
        return pipeline, llm

    def _chat_with_history(self, pipeline: RAGPipeline, **kwargs):
        return pipeline.chat(
            "A co potom?",
            "medium",
            conversation_history=[
                {"role": "user", "content": "Kdo byl Jan Hus?"},
                {"role": "assistant", "content": "Reformátor."},
            ],
            model="selected-model",
            rewrite_query_for_retrieval=True,
            **kwargs,
        )

    def test_no_sources_and_top_k_zero_skip_retrieval_and_the_rewrite_alike(self) -> None:
        for kwargs in ({"top_k": 10, "use_sources": False}, {"top_k": 0}):
            with self.subTest(**kwargs):
                pipeline, llm = self._pipeline()
                pipeline.msearch_retriever.retrieve = lambda *args, **kw: self.fail("must not retrieve")

                response = self._chat_with_history(pipeline, **kwargs)

                # Only the answer call: no query rewrite, no retrieval.
                self.assertEqual(len(llm.calls), 1)
                self.assertEqual(llm.calls[0][0]["role"], "system")
                self.assertIn(NO_SOURCES_CONTEXT, llm.calls[0][-1]["content"])
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
            user_prompt_template="{question}",
        )

        self.assertEqual(response.answer_question, "Translated question")
        self.assertEqual(llm.calls[0][-1]["content"], "Translated question")


class NoSourcesEndpointTests(unittest.TestCase):
    def _stream(self, body: dict) -> tuple[str, list]:
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
            # A provider outside the WP's allowed_providers, with its restricted collection.
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
                    "msearch_collection": next(iter(restricted_msearch_collection_ids())),
                    "user_prompt_template": "{question}\n{retrieved_snippets}",
                    **body,
                },
            )
        return response.text, upstream_bodies

    def test_stream_skips_retrieval_and_the_provider_restriction(self) -> None:
        for body in ({"use_sources": False, "top_k": 10}, {"top_k": 0}):
            with self.subTest(**body):
                text, upstream_bodies = self._stream(body)

                events = [line for line in text.splitlines() if line.startswith("event: ")]
                self.assertIn("event: done", events)
                self.assertNotIn("event: error", events)
                self.assertNotIn('"phase": "retrieval"', text)
                self.assertEqual(
                    upstream_bodies[0]["messages"][-1],
                    {"role": "user", "content": f"Co je mediální gramotnost?\n{NO_SOURCES_CONTEXT}"},
                )


if __name__ == "__main__":
    unittest.main()
