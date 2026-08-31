"""Reasoning resolution, request payloads, and trace capture.

Reasoning support is declared in data, not code: providers disagree on both the
request field and the effort vocabulary, and none of it is discoverable. These
tests pin the two rules that follow from that — nothing is sent for a model that
declares nothing, and nothing outside a model's declared vocabulary is ever
forwarded upstream. Parsing `data/models.json` is covered by
`tests/test_model_metadata.py`.
"""

import json
import unittest
from unittest.mock import patch

import httpx

from app.rag.llm import ANSWER, REASONING, OpenAICompatibleLLM, _chat_payload, _reasoning_text
from app.rag.model_metadata import ReasoningSupport, resolve_reasoning_support


class ReasoningResolutionTests(unittest.TestCase):
    def test_model_declaration_wins_over_its_provider_default(self) -> None:
        model_support = ReasoningSupport(param="reasoning", efforts=("none",))
        provider_support = ReasoningSupport(param="reasoning_effort", efforts=("high",))
        resolved = resolve_reasoning_support(
            "m",
            provider_label="P",
            model_reasoning={"m": model_support},
            provider_reasoning_defaults={"P": provider_support},
        )
        self.assertIs(resolved, model_support)

    def test_provider_default_applies_to_an_undeclared_model(self) -> None:
        provider_support = ReasoningSupport(param="reasoning_effort", efforts=("high",))
        resolved = resolve_reasoning_support(
            "unlisted",
            provider_label="P",
            model_reasoning={},
            provider_reasoning_defaults={"P": provider_support},
        )
        self.assertIs(resolved, provider_support)

    def test_nothing_declared_means_nothing_resolved(self) -> None:
        self.assertIsNone(resolve_reasoning_support("m", provider_label="P"))


class ReasoningPayloadTests(unittest.TestCase):
    def test_reasoning_param_nests_the_effort(self) -> None:
        support = ReasoningSupport(param="reasoning", efforts=("none", "low"), default="none")
        self.assertEqual(support.payload("low"), {"reasoning": {"effort": "low"}})

    def test_reasoning_effort_param_is_flat(self) -> None:
        support = ReasoningSupport(param="reasoning_effort", efforts=("low", "high"))
        self.assertEqual(support.payload("high"), {"reasoning_effort": "high"})

    def test_chat_template_reasoning_effort_is_nested_for_llamacpp(self) -> None:
        support = ReasoningSupport(
            param="chat_template_kwargs.reasoning_effort",
            efforts=("low", "medium", "high"),
        )
        self.assertEqual(
            support.payload("high"),
            {"chat_template_kwargs": {"reasoning_effort": "high"}},
        )

    def test_no_choice_falls_back_to_the_declared_default(self) -> None:
        support = ReasoningSupport(param="reasoning", efforts=("none", "low"), default="none")
        self.assertEqual(support.payload(None), {"reasoning": {"effort": "none"}})

    def test_no_choice_and_no_default_sends_nothing(self) -> None:
        support = ReasoningSupport(param="reasoning", efforts=("low",))
        self.assertEqual(support.payload(None), {})

    def test_a_mandatory_model_without_a_default_still_derives_its_cheapest_effort(self) -> None:
        # The global rule, unchanged: several shipped models now declare
        # "medium" on purpose, and declaring one must stay an override rather
        # than a new baseline. A model that says nothing gets the cheapest
        # level it accepts — read off the effort order, not off the list order.
        support = ReasoningSupport(
            param="reasoning_effort", efforts=("high", "medium", "low"), mandatory=True
        )
        self.assertEqual(support.effective_default, "low")
        self.assertEqual(support.payload(None), {"reasoning_effort": "low"})
        # And an optional one is still left alone entirely.
        optional = ReasoningSupport(param="reasoning_effort", efforts=("none", "low", "high"))
        self.assertIsNone(optional.effective_default)
        self.assertEqual(optional.payload(None), {})

    def test_an_undeclared_effort_is_dropped_not_forwarded(self) -> None:
        # A stale client must not be able to put an arbitrary value upstream.
        support = ReasoningSupport(param="reasoning", efforts=("low",), default=None)
        self.assertEqual(support.payload("extreme"), {})

    def test_chat_payload_sends_nothing_by_default(self) -> None:
        payload = _chat_payload(model="m", messages=[{"role": "user", "content": "x"}])
        self.assertNotIn("reasoning", payload)
        self.assertNotIn("reasoning_effort", payload)
        self.assertNotIn("chat_template_kwargs", payload)

    def test_chat_payload_merges_the_declared_fragment(self) -> None:
        payload = _chat_payload(
            model="m",
            messages=[{"role": "user", "content": "x"}],
            reasoning={"reasoning": {"effort": "low"}},
        )
        self.assertEqual(payload["reasoning"], {"effort": "low"})


class ReasoningTraceTests(unittest.TestCase):
    def test_reads_either_field_name_providers_use(self) -> None:
        self.assertEqual(_reasoning_text({"reasoning": "a"}), "a")
        self.assertEqual(_reasoning_text({"reasoning_content": "b"}), "b")

    def test_prefers_reasoning_when_both_are_present(self) -> None:
        self.assertEqual(_reasoning_text({"reasoning": "a", "reasoning_content": "b"}), "a")

    def test_ignores_absent_empty_and_non_string_values(self) -> None:
        self.assertEqual(_reasoning_text({}), "")
        self.assertEqual(_reasoning_text(None), "")
        self.assertEqual(_reasoning_text({"reasoning": ""}), "")
        self.assertEqual(_reasoning_text({"reasoning": {"blocks": []}}), "")


class ReasoningStreamTests(unittest.TestCase):
    """Reasoning deltas reach the caller as they arrive, tagged and in order."""

    def _stream(self, body: str):
        client = OpenAICompatibleLLM("key", "model", "https://provider.example/v1")

        def handler(request):
            return httpx.Response(
                200, request=request, text=body, headers={"content-type": "text/event-stream"}
            )

        stream = client.stream_generate([{"role": "user", "content": "q"}])
        with patch("app.rag.llm.httpx.Client", return_value=httpx.Client(transport=httpx.MockTransport(handler))):
            return list(stream), stream

    def _chunk(self, delta: dict) -> str:
        return f'data: {json.dumps({"choices": [{"delta": delta}]})}\n\n'

    def test_the_trace_streams_before_the_answer_and_stays_out_of_it(self) -> None:
        # This is the shape that makes streaming worth doing: a reasoning model
        # writes its whole trace first, so a caller that waited for the end
        # would show nothing for exactly as long as the model thinks.
        body = (
            self._chunk({"reasoning": "thinking "})
            + self._chunk({"reasoning_content": "harder"})
            + self._chunk({"content": "the "})
            + self._chunk({"content": "answer"})
            + "data: [DONE]\n\n"
        )
        chunks, stream = self._stream(body)
        self.assertEqual(
            chunks,
            [
                (REASONING, "thinking "),
                (REASONING, "harder"),
                (ANSWER, "the "),
                (ANSWER, "answer"),
            ],
        )
        # Still joined for the caller that wants it whole — history, and the
        # final event for a client that ignored the deltas.
        self.assertEqual(stream.reasoning_text, "thinking harder")

    def test_a_chunk_carrying_both_yields_the_trace_first(self) -> None:
        body = self._chunk({"reasoning": "hmm", "content": "yes"}) + "data: [DONE]\n\n"
        chunks, _ = self._stream(body)
        self.assertEqual(chunks, [(REASONING, "hmm"), (ANSWER, "yes")])

    def test_a_model_that_does_not_reason_yields_only_the_answer(self) -> None:
        body = self._chunk({"content": "plain"}) + "data: [DONE]\n\n"
        chunks, stream = self._stream(body)
        self.assertEqual(chunks, [(ANSWER, "plain")])
        self.assertEqual(stream.reasoning_text, "")


class ReasoningStreamEndpointTests(unittest.TestCase):
    """`/chat/stream` forwards the trace as its own event, ahead of the answer."""

    def test_reasoning_events_precede_the_tokens_and_the_trace_still_lands_in_done(self) -> None:
        from fastapi.testclient import TestClient

        from app import main
        from app.rag.pipeline import RetrievalCandidates

        def stream_handler(request):
            return httpx.Response(
                200,
                request=request,
                text=(
                    'data: {"choices":[{"delta":{"reasoning":"weigh"}}]}\n\n'
                    'data: {"choices":[{"delta":{"reasoning_content":"ing it"}}]}\n\n'
                    'data: {"choices":[{"delta":{"content":"answer"}}]}\n\n'
                    "data: [DONE]\n\n"
                ),
                headers={"content-type": "text/event-stream"},
            )

        with (
            patch("app.main._resolve_llm_request", return_value=(
                "provider-1", "requested-model", "server-key", "https://provider.example/v1"
            )),
            patch("app.main._enforce_msearch_collection_policy"),
            patch("app.main._enforce_retrieval_backend_policy"),
            patch.object(
                main.pipeline, "retrieve_candidates",
                return_value=RetrievalCandidates([], [], False, 0.0, 0),
            ),
            patch.object(main.pipeline, "apply_rerank_iter", return_value=iter([("result", [], 0.0)])),
            patch(
                "app.rag.llm.httpx.Client",
                return_value=httpx.Client(transport=httpx.MockTransport(stream_handler)),
            ),
        ):
            response = TestClient(main.app).post(
                "/chat/stream", json={"question": "q", "wp_id": "WP1-historie", "top_k": 0}
            )

        self.assertEqual(response.status_code, 200)
        order = [line for line in response.text.splitlines() if line.startswith("event: ")]
        self.assertEqual(
            [name for name in order if name in ("event: reasoning", "event: token")],
            ["event: reasoning", "event: reasoning", "event: token"],
        )
        self.assertIn('"text": "weigh"', response.text)
        # The answer never carries the trace, and `done` still carries it whole
        # for history and for a client that ignored the deltas.
        self.assertIn('"answer": "answer"', response.text)
        self.assertIn('"reasoning": "weighing it"', response.text)


if __name__ == "__main__":
    unittest.main()
