"""Rolling conversation compaction.

The point of these tests is the property the old implementation did not have:
compaction must make the running context *smaller*. Previously the client kept
uploading the whole transcript, so every over-threshold turn re-summarised it
from scratch and nothing ever shrank.
"""

import unittest

from app.config import get_settings
from app.rag.pipeline import ConversationContext, RAGPipeline
from app.rag.token_budget import PromptBudgetConfig, estimate_text_tokens


class StubGeneration:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.model = "stub"


class StubLLM:
    """Records every summarisation call so tests can assert on cost."""

    def __init__(self, answer: str = "shrnutí", error: Exception | None = None) -> None:
        self.answer = answer
        self.error = error
        self.calls: list[list[dict[str, str]]] = []

    def generate(self, messages, **_kwargs):
        self.calls.append(messages)
        if self.error is not None:
            raise self.error
        return StubGeneration(self.answer)


def message(role: str, text: str) -> dict[str, str]:
    return {"role": role, "content": text}


def history(count: int, filler: str = "slovo ") -> list[dict[str, str]]:
    return [
        message("user" if index % 2 == 0 else "assistant", f"zpráva {index} " + filler * 40)
        for index in range(count)
    ]


def config(trigger: int = 8000, recent: int = 6, trigger_messages: int = 16) -> PromptBudgetConfig:
    return PromptBudgetConfig(
        context_window_tokens=32768,
        output_token_budget_short=384,
        output_token_budget_medium=768,
        output_token_budget_long=1024,
        min_prompt_chunks=3,
        token_budget_safety_margin=0.1,
        conversation_summary_trigger_tokens=trigger,
        conversation_recent_messages=recent,
        conversation_summary_trigger_messages=trigger_messages,
    )


def resolve(pipeline: RAGPipeline, messages, *, summary=None, budget_config=None) -> ConversationContext:
    return pipeline._resolve_conversation_context(
        messages,
        conversation_summary=summary,
        model="unknown-model",
        length="medium",
        budget_config=budget_config or config(),
        api_key=None,
        base_url=None,
    )


class ConversationCompactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = StubLLM()
        self.pipeline = RAGPipeline(get_settings())
        self.pipeline._llm = self.llm

    def test_short_history_is_passed_through_untouched(self) -> None:
        messages = history(4)
        result = resolve(self.pipeline, messages)
        self.assertEqual(result.history, messages)
        self.assertIsNone(result.summary)
        self.assertEqual(result.folded_message_count, 0)
        self.assertEqual(self.llm.calls, [], "no summarisation call below the trigger")

    def test_existing_summary_survives_a_short_history(self) -> None:
        result = resolve(self.pipeline, history(4), summary="dřívější shrnutí")
        self.assertEqual(result.summary, "dřívější shrnutí")
        self.assertEqual(result.folded_message_count, 0)
        self.assertEqual(self.llm.calls, [])

    def test_over_the_token_trigger_keeps_a_token_aware_recent_tail(self) -> None:
        messages = history(20)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=200, recent=6))
        self.assertEqual(result.summary, "shrnutí")
        self.assertGreaterEqual(result.folded_message_count, 10)
        self.assertLessEqual(len(result.history), 6)
        self.assertEqual(result.history[-2:], messages[-2:])
        self.assertEqual(len(self.llm.calls), 1)

    def test_the_summariser_only_sees_the_messages_being_folded(self) -> None:
        messages = history(20)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=200, recent=6))
        prompt = self.llm.calls[0][-1]["content"]
        self.assertIn("zpráva 0", prompt)
        self.assertIn(f"zpráva {result.folded_message_count - 1}", prompt)
        # The kept tail is sent to the answering model verbatim, so folding it
        # into the summary as well would pay for it twice.
        self.assertNotIn(f"zpráva {result.folded_message_count}", prompt)

    def test_folding_is_incremental_over_the_previous_summary(self) -> None:
        resolve(
            self.pipeline,
            history(20),
            summary="dosavadní shrnutí",
            budget_config=config(trigger=200, recent=6),
        )
        prompt = self.llm.calls[0][-1]["content"]
        self.assertIn("dosavadní shrnutí", prompt)

    def test_summary_is_rewritten_as_one_bounded_replacement(self) -> None:
        self.llm.answer = ("Důležitá souhrnná věta. " * 600).strip()
        result = resolve(self.pipeline, history(20), budget_config=config(trigger=200, recent=6))
        prompt = self.llm.calls[0][0]["content"]
        self.assertIn("Do not append a new section", prompt)
        self.assertLessEqual(estimate_text_tokens(result.summary or "", "unknown-model"), 256)
        self.assertTrue((result.summary or "").endswith("…"))

    def test_dropping_the_folded_messages_stops_the_next_turn_resummarising(self) -> None:
        """The property the old implementation lacked.

        A client that drops `folded_message_count` messages comes back under the
        trigger, so the next turn costs no summarisation call at all. The old
        code re-summarised the full transcript on every single turn.
        """

        budget_config = config(trigger=200, recent=6)
        first = resolve(self.pipeline, history(20), budget_config=budget_config)
        remaining = history(20)[first.folded_message_count :]
        self.assertLessEqual(len(remaining), 6)

        second = resolve(self.pipeline, remaining, summary=first.summary, budget_config=budget_config)
        self.assertEqual(second.folded_message_count, 0)
        self.assertEqual(second.summary, first.summary)
        self.assertEqual(len(self.llm.calls), 1, "the second turn makes no summarisation call")

    def test_latest_complete_turn_is_kept_even_when_it_exceeds_the_target(self) -> None:
        messages = history(6)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=1, recent=6))
        self.assertEqual(result.history, messages[-2:])
        self.assertEqual(result.folded_message_count, 4)
        self.assertEqual(len(self.llm.calls), 1)

    def test_two_message_latest_turn_is_never_summarised(self) -> None:
        messages = history(2, filler="velmi dlouhá zpráva " * 100)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=1))
        self.assertEqual(result.history, messages)
        self.assertEqual(result.folded_message_count, 0)
        self.assertEqual(self.llm.calls, [])

    def test_message_count_trigger_compacts_token_light_history(self) -> None:
        messages = history(18, filler="x")
        result = resolve(self.pipeline, messages, budget_config=config(trigger=8000, trigger_messages=16))
        self.assertGreaterEqual(result.folded_message_count, 12)
        self.assertLessEqual(len(result.history), 6)
        self.assertEqual(len(self.llm.calls), 1)

    def test_sixteen_token_light_messages_remain_verbatim(self) -> None:
        messages = history(16, filler="x")
        result = resolve(self.pipeline, messages, budget_config=config(trigger=8000, trigger_messages=16))
        self.assertEqual(result.history, messages)
        self.assertEqual(result.folded_message_count, 0)
        self.assertEqual(self.llm.calls, [])

    def test_effective_trigger_is_derived_from_usable_input_and_capped(self) -> None:
        small = config(trigger=8000)
        self.assertEqual(small.effective_conversation_trigger_tokens("medium"), 7450)
        self.assertEqual(small.conversation_summary_target_tokens("medium"), 768)
        capped = PromptBudgetConfig(
            context_window_tokens=40000,
            output_token_budget_short=768,
            output_token_budget_medium=768,
            output_token_budget_long=768,
            min_prompt_chunks=3,
            token_budget_safety_margin=0.1,
            conversation_summary_trigger_tokens=8000,
        )
        self.assertEqual(capped.effective_conversation_trigger_tokens("medium"), 8000)
        self.assertEqual(capped.conversation_summary_target_tokens("medium"), 768)

        low = config(trigger=1500)
        self.assertEqual(low.conversation_summary_target_tokens("medium"), 256)

    def test_summariser_failure_falls_back_to_the_raw_tail(self) -> None:
        self.llm.error = RuntimeError("The read operation timed out")
        messages = history(20)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=200, recent=6))
        self.assertEqual(result.history, messages)
        self.assertIsNone(result.summary)
        self.assertEqual(result.folded_message_count, 0)
        self.assertIn("The read operation timed out", result.warning)

    def test_summariser_failure_keeps_the_previous_summary(self) -> None:
        self.llm.error = RuntimeError("boom")
        result = resolve(
            self.pipeline,
            history(20),
            summary="dřívější shrnutí",
            budget_config=config(trigger=200, recent=6),
        )
        self.assertEqual(result.summary, "dřívější shrnutí")
        self.assertEqual(result.folded_message_count, 0)
        self.assertIn("previous compressed summary", result.warning)


if __name__ == "__main__":
    unittest.main()
