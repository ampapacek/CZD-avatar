import unittest

from app.rag.token_budget import (
    PromptBudgetConfig,
    PromptBudgetError,
    estimate_text_tokens,
    prepare_prompt_budget,
)


def chunk(chunk_id: str, text: str, score: float) -> dict:
    return {
        "citation_id": chunk_id.upper(),
        "chunk_id": chunk_id,
        "text": text,
        "score": score,
        "metadata": {"title": f"Doc {chunk_id}", "source_path": f"{chunk_id}.md"},
    }


class TokenBudgetTests(unittest.TestCase):
    def test_estimates_tokens(self) -> None:
        self.assertGreater(estimate_text_tokens("hello world", "unknown-model"), 0)

    def test_errors_when_non_source_prompt_does_not_fit(self) -> None:
        config = PromptBudgetConfig(
            context_window_tokens=1024,
            output_token_budget_short=384,
            output_token_budget_medium=384,
            output_token_budget_long=384,
            min_prompt_chunks=3,
            token_budget_safety_margin=0.1,
            conversation_summary_trigger_tokens=3000,
        )

        with self.assertRaises(PromptBudgetError) as raised:
            prepare_prompt_budget(
                question="x" * 10000,
                retrieved_chunks=[],
                style="ucitel",
                length="short",
                model="unknown-model",
                config=config,
            )
        error = raised.exception
        self.assertGreater(error.estimated_non_source_tokens, error.usable_input_tokens)
        self.assertGreater(error.over_by_tokens, 0)
        self.assertIn("Current prompt without sources", str(error))
        self.assertIn("Usable input budget", str(error))

    def test_keeps_full_chunks_when_they_fit(self) -> None:
        chunks = [chunk("z1", "Husitské války měly náboženský i politický význam.", 0.9)]
        config = PromptBudgetConfig(
            context_window_tokens=4096,
            output_token_budget_short=384,
            output_token_budget_medium=768,
            output_token_budget_long=1024,
            min_prompt_chunks=3,
            token_budget_safety_margin=0.0,
            conversation_summary_trigger_tokens=3000,
        )

        budget = prepare_prompt_budget(
            question="Jaký byl význam husitských válek?",
            retrieved_chunks=chunks,
            style="ucitel",
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertEqual(len(budget.used_chunks), 1)
        self.assertEqual(budget.used_chunks[0]["text"], chunks[0]["text"])
        self.assertEqual(budget.omitted_chunks, [])

    def test_drops_least_relevant_chunks_first(self) -> None:
        chunks = [
            chunk("z1", "První relevantní text. " * 20, 0.9),
            chunk("z2", "Druhý relevantní text. " * 20, 0.8),
            chunk("z3", "Třetí relevantní text. " * 500, 0.1),
        ]
        config = PromptBudgetConfig(
            context_window_tokens=1500,
            output_token_budget_short=384,
            output_token_budget_medium=768,
            output_token_budget_long=1024,
            min_prompt_chunks=1,
            token_budget_safety_margin=0.0,
            conversation_summary_trigger_tokens=3000,
        )

        budget = prepare_prompt_budget(
            question="Co je relevantní?",
            retrieved_chunks=chunks,
            style="ucitel",
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertIn("z1", {item["chunk_id"] for item in budget.used_chunks})
        self.assertIn("z3", {item["chunk_id"] for item in budget.omitted_chunks})

    def test_trims_top_chunks_to_keep_minimum_when_possible(self) -> None:
        chunks = [
            chunk("z1", "Husitské války byly důležité. " + ("Dlouhý text. " * 120), 0.9),
            chunk("z2", "Husitské války změnily politiku. " + ("Dlouhý text. " * 120), 0.8),
            chunk("z3", "Husitské války ovlivnily společnost. " + ("Dlouhý text. " * 120), 0.7),
        ]
        config = PromptBudgetConfig(
            context_window_tokens=1400,
            output_token_budget_short=384,
            output_token_budget_medium=768,
            output_token_budget_long=1024,
            min_prompt_chunks=3,
            token_budget_safety_margin=0.0,
            conversation_summary_trigger_tokens=3000,
        )

        budget = prepare_prompt_budget(
            question="Jaký význam měly husitské války?",
            retrieved_chunks=chunks,
            style="ucitel",
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertGreaterEqual(len(budget.used_chunks), 1)
        self.assertTrue(any(item["metadata"].get("budget_status") == "trimmed" for item in budget.used_chunks))


if __name__ == "__main__":
    unittest.main()
