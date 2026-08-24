import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.config import get_settings
from app.rag.llm import LLMGeneration
from app.rag.pipeline import RAGPipeline, RetrievalCandidates
from app.rag.token_budget import PromptBudgetError


class _FakeLLM:
    model = "fake-model"

    def __init__(self, answer: str = "rewritten query") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, messages, model=None, api_key=None, base_url=None, reasoning=None):
        self.calls.append(
            {
                "messages": messages,
                "model": model,
                "api_key": api_key,
                "base_url": base_url,
                "reasoning": reasoning,
            }
        )
        return LLMGeneration(answer=self.answer, model=model)


class RetrievalQueryRewriteTests(unittest.TestCase):
    def _pipeline(
        self,
        answer: str = "rewritten query",
        settings: Settings | None = None,
    ) -> tuple[RAGPipeline, _FakeLLM]:
        pipeline = RAGPipeline(settings or get_settings())
        llm = _FakeLLM(answer)
        pipeline._llm = llm
        return pipeline, llm

    def test_disabled_returns_original_question_without_llm_call(self) -> None:
        pipeline, llm = self._pipeline()

        query = pipeline.rewrite_query_for_retrieval(
            "A co potom?",
            conversation_history=[{"role": "user", "content": "Mluvili jsme o Janu Husovi."}],
            conversation_summary=None,
            enabled=False,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "A co potom?")
        self.assertEqual(llm.calls, [])

    def test_long_conversation_message_skips_rewrite(self) -> None:
        settings = Settings(_env_file=None, CONVERSATION_QUERY_REWRITE_MAX_TOKENS=1)
        pipeline, llm = self._pipeline(settings=settings)

        query = pipeline.rewrite_query_for_retrieval(
            "This long standalone prompt already contains its own context.",
            conversation_history=[{"role": "assistant", "content": "Earlier answer"}],
            conversation_summary=None,
            enabled=True,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "This long standalone prompt already contains its own context.")
        self.assertEqual(llm.calls, [])

    def test_long_message_is_still_sent_to_retrieval(self) -> None:
        settings = Settings(_env_file=None, CONVERSATION_QUERY_REWRITE_MAX_TOKENS=1)
        pipeline, _llm = self._pipeline(answer="generated answer", settings=settings)
        retrieved_queries: list[str] = []
        pipeline.retrieve_with_baseline = lambda query, *args, **kwargs: (
            retrieved_queries.append(query) or [],
            [],
        )
        budget = SimpleNamespace(
            messages=[{"role": "user", "content": "original"}],
            used_chunks=[],
            omitted_chunks=[],
            warnings=[],
            conversation_summary_used=False,
            metadata=lambda: None,
        )
        with patch("app.rag.pipeline.prepare_prompt_budget", return_value=budget):
            pipeline.chat(
                "A long self-contained message",
                "medium",
                conversation_history=[{"role": "assistant", "content": "Earlier answer"}],
                rewrite_query_for_retrieval=True,
                model="selected-model",
            )

        self.assertEqual(retrieved_queries, ["A long self-contained message"])

    def test_oversized_current_prompt_stops_before_remote_work(self) -> None:
        pipeline, llm = self._pipeline(answer="must not be used")
        with (
            patch.object(
                pipeline,
                "_resolve_conversation_context",
                side_effect=AssertionError("conversation summarisation must not run"),
            ),
            patch.object(
                pipeline,
                "rewrite_query_for_retrieval",
                side_effect=AssertionError("query rewriting must not run"),
            ),
            patch.object(
                pipeline,
                "retrieve_with_baseline",
                side_effect=AssertionError("retrieval must not run"),
            ),
            self.assertRaises(PromptBudgetError),
        ):
            pipeline.chat(
                "x" * 10000,
                "short",
                conversation_history=[{"role": "assistant", "content": "Earlier answer"}],
                rewrite_query_for_retrieval=True,
                model="selected-model",
                context_window_tokens=1024,
                output_token_budget_short=384,
            )

        self.assertEqual(llm.calls, [])

    def test_first_conversation_message_returns_original_question(self) -> None:
        pipeline, llm = self._pipeline()

        query = pipeline.rewrite_query_for_retrieval(
            "Kdo byl Jan Hus?",
            conversation_history=[],
            conversation_summary=None,
            enabled=True,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "Kdo byl Jan Hus?")
        self.assertEqual(llm.calls, [])
        self.assertEqual(
            pipeline.query_rewrite_skip_reason(
                "Kdo byl Jan Hus?",
                conversation_history=[],
                enabled=True,
                model="selected-model",
            ),
            "no_conversation_history",
        )

    def test_long_message_reports_why_rewrite_was_skipped(self) -> None:
        settings = Settings(_env_file=None, CONVERSATION_QUERY_REWRITE_MAX_TOKENS=1)
        pipeline, _llm = self._pipeline(settings=settings)

        self.assertEqual(
            pipeline.query_rewrite_skip_reason(
                "A long self-contained message",
                conversation_history=[{"role": "assistant", "content": "Earlier answer"}],
                enabled=True,
                model="selected-model",
            ),
            "question_too_long",
        )

    def test_uses_same_model_and_recent_conversation_for_rewrite(self) -> None:
        pipeline, llm = self._pipeline('"Jan Hus a jeho vliv"')

        query = pipeline.rewrite_query_for_retrieval(
            "A jaký měl vliv?",
            conversation_history=[
                {"role": "user", "content": "Kdo byl Jan Hus?"},
                {"role": "assistant", "content": "Jan Hus byl český reformátor."},
            ],
            conversation_summary="Konverzace je o Janu Husovi.",
            enabled=True,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "Jan Hus a jeho vliv")
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(llm.calls[0]["model"], "selected-model")
        self.assertEqual(llm.calls[0]["api_key"], "key")
        self.assertEqual(llm.calls[0]["base_url"], "https://example.test/v1")
        prompt = llm.calls[0]["messages"][1]["content"]
        self.assertIn("Konverzace je o Janu Husovi.", prompt)
        self.assertIn("Jan Hus byl český reformátor.", prompt)
        self.assertIn("A jaký měl vliv?", prompt)

    def test_explicit_retrieval_query_bypasses_conversation_rewrite(self) -> None:
        pipeline, llm = self._pipeline("generated answer")
        retrieved_queries: list[str] = []
        pipeline.rewrite_query_for_retrieval = lambda *args, **kwargs: self.fail(
            "Explicit retrieval query must bypass conversation rewriting"
        )
        pipeline.retrieve_with_baseline = lambda query, *args, **kwargs: (
            retrieved_queries.append(query) or [],
            [],
        )
        budget = SimpleNamespace(
            messages=[{"role": "user", "content": "original"}],
            used_chunks=[],
            omitted_chunks=[],
            warnings=[],
            conversation_summary_used=False,
            metadata=lambda: None,
        )
        with patch("app.rag.pipeline.prepare_prompt_budget", return_value=budget) as prepare:
            response = pipeline.chat(
                "Původní dotaz",
                "medium",
                model="selected-model",
                retrieval_query_override="Translated retrieval query",
            )

        self.assertEqual(retrieved_queries, ["Translated retrieval query"])
        self.assertEqual(prepare.call_args.kwargs["question"], "Původní dotaz")
        self.assertEqual(response.original_question, "Původní dotaz")
        self.assertEqual(response.retrieval_query, "Translated retrieval query")
        self.assertEqual(response.answer_question, "Původní dotaz")
        self.assertEqual(len(llm.calls), 1)

    def test_explicit_retrieval_query_can_also_drive_answer_generation(self) -> None:
        pipeline, _llm = self._pipeline("generated answer")
        pipeline.retrieve_with_baseline = lambda *args, **kwargs: ([], [])
        budget = SimpleNamespace(
            messages=[{"role": "user", "content": "translated"}],
            used_chunks=[],
            omitted_chunks=[],
            warnings=[],
            conversation_summary_used=False,
            metadata=lambda: None,
        )
        with patch("app.rag.pipeline.prepare_prompt_budget", return_value=budget) as prepare:
            response = pipeline.chat(
                "Původní dotaz",
                "medium",
                model="selected-model",
                retrieval_query_override="Translated retrieval query",
                use_retrieval_query_for_answer=True,
            )

        self.assertEqual(prepare.call_args.kwargs["question"], "Translated retrieval query")
        self.assertEqual(response.answer_question, "Translated retrieval query")

    def test_pipeline_uses_configured_timeout_for_all_llm_calls(self) -> None:
        settings = Settings(_env_file=None, LLM_TIMEOUT_SECONDS=123)
        pipeline = RAGPipeline(settings)
        providers = {
            "test": {
                "default_model": "model",
                "base_url": "https://example.test/v1",
            }
        }
        with (
            patch("app.rag.pipeline.available_llm_providers", return_value=providers),
            patch("app.rag.pipeline.resolve_llm_provider", return_value="test"),
            patch("app.rag.pipeline.provider_preset", return_value=providers["test"]),
            patch("app.rag.pipeline.provider_api_key", return_value="key"),
        ):
            client = pipeline.llm

        self.assertEqual(client.timeout, 123)

    def test_stream_reports_query_rewrite_before_sources(self) -> None:
        from app import main

        def stream_handler(request):
            return httpx.Response(
                200,
                request=request,
                text='data: {"choices":[{"delta":{"content":"answer"}}]}\n\ndata: [DONE]\n\n',
                headers={"content-type": "text/event-stream"},
            )

        with (
            patch("app.main._resolve_llm_request", return_value=(
                "provider-1", "requested-model", "server-key", "https://provider.example/v1"
            )),
            patch("app.main._enforce_msearch_collection_policy"),
            patch("app.main._enforce_retrieval_backend_policy"),
            patch.object(main.pipeline, "should_rewrite_query_for_retrieval", return_value=True),
            patch.object(main.pipeline, "rewrite_query_for_retrieval", return_value="rewritten query"),
            patch.object(
                main.pipeline,
                "retrieve_candidates",
                return_value=RetrievalCandidates([], [], False, 0.0, 0),
            ),
            patch.object(main.pipeline, "apply_rerank_iter", return_value=iter([("result", [], 0.0)])),
            patch(
                "app.rag.llm.httpx.Client",
                return_value=httpx.Client(transport=httpx.MockTransport(stream_handler)),
            ),
        ):
            response = TestClient(main.app).post(
                "/chat/stream",
                json={
                    "question": "And what happened next?",
                    "conversation_history": [{"role": "assistant", "content": "Earlier answer"}],
                    "rewrite_query_for_retrieval": True,
                    "wp_id": "WP1-historie",
                    "top_k": 0,
                },
            )

        events = [line for line in response.text.splitlines() if line.startswith("event: ")]
        self.assertLess(events.index("event: status"), events.index("event: sources"))
        self.assertIn('"phase": "query_rewrite"', response.text)
        self.assertIn('"phase": "retrieval"', response.text)
        self.assertIn('"retrieval_query_rewrite_attempted": true', response.text)

    def test_stream_rejects_oversized_prompt_before_rewrite_or_retrieval(self) -> None:
        from app import main

        with (
            patch("app.main._resolve_llm_request", return_value=(
                "provider-1", "requested-model", "server-key", "https://provider.example/v1"
            )),
            patch.object(
                main.pipeline,
                "should_rewrite_query_for_retrieval",
                side_effect=AssertionError("query rewrite decision must not run"),
            ),
            patch.object(
                main.pipeline,
                "retrieve_candidates",
                side_effect=AssertionError("retrieval must not run"),
            ),
            patch.object(
                main.pipeline,
                "build_chat_prompt",
                side_effect=AssertionError("conversation summarisation must not run"),
            ),
        ):
            response = TestClient(main.app).post(
                "/chat/stream",
                json={
                    "question": "x" * 10000,
                    "conversation_history": [{"role": "assistant", "content": "Earlier answer"}],
                    "rewrite_query_for_retrieval": True,
                    "context_window_tokens": 1024,
                    "output_token_budget_short": 384,
                    "wp_id": "WP1-historie",
                    "top_k": 10,
                },
            )

        events = [line for line in response.text.splitlines() if line.startswith("event: ")]
        self.assertEqual(events, ["event: error"])
        self.assertIn('"over_by_tokens"', response.text)
        self.assertNotIn("event: status", response.text)
        self.assertNotIn("event: sources", response.text)


if __name__ == "__main__":
    unittest.main()
