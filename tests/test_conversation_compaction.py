"""Rolling conversation compaction.

The point of these tests is the property the old implementation did not have:
compaction must make the running context *smaller*. Previously the client kept
uploading the whole transcript, so every over-threshold turn re-summarised it
from scratch and nothing ever shrank.
"""

import unittest

from app.config import get_settings
from app.rag.pipeline import ConversationContext, RAGPipeline
from app.rag.token_budget import PromptBudgetConfig


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


def config(trigger: int = 3000, recent: int = 6) -> PromptBudgetConfig:
    return PromptBudgetConfig(
        context_window_tokens=32768,
        output_token_budget_short=384,
        output_token_budget_medium=768,
        output_token_budget_long=1024,
        min_prompt_chunks=3,
        token_budget_safety_margin=0.1,
        conversation_summary_trigger_tokens=trigger,
        conversation_recent_messages=recent,
    )


def resolve(pipeline: RAGPipeline, messages, *, summary=None, budget_config=None) -> ConversationContext:
    return pipeline._resolve_conversation_context(
        messages,
        conversation_summary=summary,
        model="unknown-model",
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

    def test_over_the_trigger_folds_everything_but_the_recent_tail(self) -> None:
        messages = history(20)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=200, recent=6))
        self.assertEqual(result.summary, "shrnutí")
        self.assertEqual(result.folded_message_count, 14)
        self.assertEqual(result.history, messages[-6:])
        self.assertEqual(len(self.llm.calls), 1)

    def test_the_summariser_only_sees_the_messages_being_folded(self) -> None:
        messages = history(20)
        resolve(self.pipeline, messages, budget_config=config(trigger=200, recent=6))
        prompt = self.llm.calls[0][-1]["content"]
        self.assertIn("zpráva 0", prompt)
        self.assertIn("zpráva 13", prompt)
        # The kept tail is sent to the answering model verbatim, so folding it
        # into the summary as well would pay for it twice.
        self.assertNotIn("zpráva 14", prompt)

    def test_folding_is_incremental_over_the_previous_summary(self) -> None:
        resolve(
            self.pipeline,
            history(20),
            summary="dosavadní shrnutí",
            budget_config=config(trigger=200, recent=6),
        )
        prompt = self.llm.calls[0][-1]["content"]
        self.assertIn("dosavadní shrnutí", prompt)

    def test_dropping_the_folded_messages_stops_the_next_turn_resummarising(self) -> None:
        """The property the old implementation lacked.

        A client that drops `folded_message_count` messages comes back under the
        trigger, so the next turn costs no summarisation call at all. The old
        code re-summarised the full transcript on every single turn.
        """

        budget_config = config(trigger=200, recent=6)
        first = resolve(self.pipeline, history(20), budget_config=budget_config)
        remaining = history(20)[first.folded_message_count :]
        self.assertEqual(len(remaining), 6)

        second = resolve(self.pipeline, remaining, summary=first.summary, budget_config=budget_config)
        self.assertEqual(second.folded_message_count, 0)
        self.assertEqual(second.summary, first.summary)
        self.assertEqual(len(self.llm.calls), 1, "the second turn makes no summarisation call")

    def test_a_long_tail_of_only_recent_messages_is_not_folded(self) -> None:
        # Over the trigger but nothing older than the tail: folding here would
        # compress context the model still needs verbatim.
        messages = history(6)
        result = resolve(self.pipeline, messages, budget_config=config(trigger=1, recent=6))
        self.assertEqual(result.history, messages)
        self.assertEqual(result.folded_message_count, 0)
        self.assertEqual(self.llm.calls, [])

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
