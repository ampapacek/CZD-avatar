import unittest

from app.rag.token_budget import (
    PromptBudgetConfig,
    PromptBudgetError,
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
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertEqual(len(budget.used_chunks), 1)
        self.assertEqual(budget.used_chunks[0]["text"], chunks[0]["text"])
        self.assertEqual(budget.omitted_chunks, [])
        self.assertEqual(
            budget.metadata()["estimated_total_input_tokens"],
            budget.metadata()["estimated_non_source_tokens"] + budget.metadata()["estimated_source_tokens"],
        )
        self.assertEqual(
            budget.metadata()["estimated_retrieved_source_tokens"],
            budget.metadata()["estimated_source_tokens"],
        )

    def test_reports_conversation_history_tokens_separately(self) -> None:
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
            question="Navazující otázka?",
            retrieved_chunks=[],
            length="short",
            model="unknown-model",
            config=config,
            conversation_history=[
                {"role": "user", "content": "První otázka"},
                {"role": "assistant", "content": "První odpověď"},
            ],
        )

        metadata = budget.metadata()
        self.assertGreater(metadata["estimated_conversation_history_tokens"], 0)
        self.assertGreaterEqual(
            metadata["estimated_total_input_tokens"],
            metadata["estimated_conversation_history_tokens"],
        )
        self.assertEqual(metadata["conversation_history_message_count"], 2)
        self.assertEqual(metadata["conversation_history_used_message_count"], 2)
        self.assertEqual(metadata["conversation_history_omitted_message_count"], 0)

    def test_prompt_packing_defers_the_last_chunk_behind_older_history(self) -> None:
        chunks = [chunk(f"z{index}", (f"chunk {index} " * 300), 1 - index / 10) for index in range(1, 5)]
        history = [
            {
                "role": "user" if index % 2 == 0 else "assistant",
                "content": f"history {index} " * 100,
            }
            for index in range(6)
        ]
        config = PromptBudgetConfig(
            context_window_tokens=5000,
            output_token_budget_short=128,
            output_token_budget_medium=128,
            output_token_budget_long=128,
            min_prompt_chunks=2,
            token_budget_safety_margin=0.0,
            conversation_summary_trigger_tokens=8000,
        )

        budget = prepare_prompt_budget(
            question="Navazující otázka",
            retrieved_chunks=chunks,
            length="short",
            model="unknown-model",
            config=config,
            conversation_history=history,
            conversation_summary="Dřívější shrnutí",
            system_prompt="S",
            user_prompt_template="{question}\n{retrieved_snippets}",
        )

        self.assertEqual([item["chunk_id"] for item in budget.used_chunks], ["z1", "z2", "z3"])
        self.assertEqual(budget.metadata()["conversation_history_used_message_count"], 6)
        self.assertEqual(budget.metadata()["conversation_history_omitted_message_count"], 0)
        self.assertEqual([item["chunk_id"] for item in budget.omitted_chunks], ["z4"])

    def test_minimum_chunks_and_last_turn_outrank_older_history(self) -> None:
        chunks = [chunk(f"z{index}", (f"chunk {index} " * 300), 1 - index / 10) for index in range(1, 5)]
        history = [
            {
                "role": "user" if index % 2 == 0 else "assistant",
                "content": f"history {index} " * 100,
            }
            for index in range(6)
        ]
        config = PromptBudgetConfig(
            context_window_tokens=1200,
            output_token_budget_short=128,
            output_token_budget_medium=128,
            output_token_budget_long=128,
            min_prompt_chunks=2,
            token_budget_safety_margin=0.0,
            conversation_summary_trigger_tokens=8000,
        )

        budget = prepare_prompt_budget(
            question="Navazující otázka",
            retrieved_chunks=chunks,
            length="short",
            model="unknown-model",
            config=config,
            conversation_history=history,
            conversation_summary="Dřívější shrnutí",
            system_prompt="S",
            user_prompt_template="{question}\n{retrieved_snippets}",
        )

        self.assertEqual([item["chunk_id"] for item in budget.used_chunks], ["z1", "z2"])
        self.assertEqual(budget.metadata()["conversation_history_used_message_count"], 2)
        self.assertEqual(budget.metadata()["conversation_history_omitted_message_count"], 4)
        self.assertTrue(all(item["metadata"].get("budget_status") == "trimmed" for item in budget.used_chunks))

    def test_safety_margin_completes_the_subtraction(self) -> None:
        # The UI renders context window − output reserve − safety margin =
        # usable input, so the reported margin has to be exactly the residual.
        config = PromptBudgetConfig(
            context_window_tokens=40000,
            output_token_budget_short=768,
            output_token_budget_medium=768,
            output_token_budget_long=768,
            min_prompt_chunks=3,
            token_budget_safety_margin=0.1,
            conversation_summary_trigger_tokens=3000,
        )

        budget = prepare_prompt_budget(
            question="Jaký byl význam husitských válek?",
            retrieved_chunks=[],
            length="short",
            model="unknown-model",
            config=config,
        )

        metadata = budget.metadata()
        self.assertEqual(metadata["context_window_tokens"], 40000)
        self.assertEqual(metadata["reserved_output_tokens"], 768)
        self.assertEqual(metadata["usable_input_tokens"], 35308)
        self.assertEqual(metadata["safety_margin_tokens"], 3924)
        self.assertEqual(metadata["safety_margin_ratio"], 0.1)
        self.assertEqual(
            metadata["context_window_tokens"]
            - metadata["reserved_output_tokens"]
            - metadata["safety_margin_tokens"],
            metadata["usable_input_tokens"],
        )

    def test_safety_margin_is_zero_without_a_configured_margin(self) -> None:
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
            question="Otázka?",
            retrieved_chunks=[],
            length="short",
            model="unknown-model",
            config=config,
        )

        metadata = budget.metadata()
        self.assertEqual(metadata["safety_margin_tokens"], 0)
        self.assertEqual(metadata["safety_margin_ratio"], 0.0)

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
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertIn("z1", {item["chunk_id"] for item in budget.used_chunks})
        self.assertIn("z3", {item["chunk_id"] for item in budget.omitted_chunks})
        self.assertGreater(
            budget.metadata()["estimated_retrieved_source_tokens"],
            budget.metadata()["estimated_source_tokens"],
        )
        self.assertIn("Kvůli limitu kontextu nebylo modelu posláno", budget.warnings[0])

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
            length="short",
            model="unknown-model",
            config=config,
        )

        self.assertGreaterEqual(len(budget.used_chunks), 1)
        self.assertTrue(any(item["metadata"].get("budget_status") == "trimmed" for item in budget.used_chunks))


if __name__ == "__main__":
    unittest.main()
