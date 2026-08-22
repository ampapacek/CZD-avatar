"""Reasoning resolution, request payloads, and trace capture.

Reasoning support is declared in data, not code: providers disagree on both the
request field and the effort vocabulary, and none of it is discoverable. These
tests pin the two rules that follow from that — nothing is sent for a model that
declares nothing, and nothing outside a model's declared vocabulary is ever
forwarded upstream. Parsing `data/models.json` is covered by
`tests/test_model_metadata.py`.
"""

import unittest

from app.rag.llm import _chat_payload, _reasoning_text
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

    def test_no_choice_falls_back_to_the_declared_default(self) -> None:
        support = ReasoningSupport(param="reasoning", efforts=("none", "low"), default="none")
        self.assertEqual(support.payload(None), {"reasoning": {"effort": "none"}})

    def test_no_choice_and_no_default_sends_nothing(self) -> None:
        support = ReasoningSupport(param="reasoning", efforts=("low",))
        self.assertEqual(support.payload(None), {})

    def test_an_undeclared_effort_is_dropped_not_forwarded(self) -> None:
        # A stale client must not be able to put an arbitrary value upstream.
        support = ReasoningSupport(param="reasoning", efforts=("low",), default=None)
        self.assertEqual(support.payload("extreme"), {})

    def test_chat_payload_sends_nothing_by_default(self) -> None:
        payload = _chat_payload(model="m", messages=[{"role": "user", "content": "x"}])
        self.assertNotIn("reasoning", payload)
        self.assertNotIn("reasoning_effort", payload)

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


if __name__ == "__main__":
    unittest.main()
