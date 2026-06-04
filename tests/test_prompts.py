import unittest
from datetime import date

from app.rag.prompts import LENGTH_PROMPTS, build_messages


class PromptRenderingTests(unittest.TestCase):
    def test_uses_prompt_specific_length_definition(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="short",
            system_prompt="Délka odpovědi: {length}",
            length_prompts={"short": "Jedna věta bez úvodu."},
        )

        self.assertIn("Jedna věta bez úvodu.", messages[0]["content"])
        self.assertNotIn(LENGTH_PROMPTS["short"], messages[0]["content"])

    def test_falls_back_to_default_length_definition(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="medium",
            system_prompt="Délka odpovědi: {length}",
            length_prompts={},
        )

        self.assertIn(LENGTH_PROMPTS["medium"], messages[0]["content"])

    def test_omits_custom_instructions_when_template_has_no_placeholder(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="short",
            custom_instructions="Odpověz v bodech.",
            user_prompt_template="Otázka: {question}\nKontext: {context}",
        )

        self.assertIn("Otázka: Co se stalo?", messages[-1]["content"])
        self.assertNotIn("Odpověz v bodech.", messages[-1]["content"])

    def test_empty_custom_instructions_render_neutral_default_when_requested(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="short",
            custom_instructions="",
            user_prompt_template="Instrukce: {custom_instructions}",
        )

        self.assertEqual("Instrukce: Žádné.", messages[-1]["content"])

    def test_unknown_placeholder_stays_literal_while_known_values_render(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="short",
            system_prompt="Délka: {length}\nNeznámé: {avatar_name}",
            user_prompt_template="Otázka: {question}\nNeznámé: {audience}",
        )

        self.assertIn(LENGTH_PROMPTS["short"], messages[0]["content"])
        self.assertIn("{avatar_name}", messages[0]["content"])
        self.assertIn("Otázka: Co se stalo?", messages[-1]["content"])
        self.assertIn("{audience}", messages[-1]["content"])

    def test_current_date_placeholder_renders_iso_date(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            style="ucitel",
            length="short",
            system_prompt="Datum: {current_date}",
            user_prompt_template="Otázka: {question}",
        )

        self.assertEqual(f"Datum: {date.today().isoformat()}", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
