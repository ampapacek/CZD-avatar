import unittest
from datetime import date

from app.rag.prompts import (
    OptionDef,
    PlaceholderDef,
    build_messages,
    resolve_placeholder_defs,
)


LENGTH_DEF = PlaceholderDef(
    label="Délka",
    kind="select",
    default="medium",
    options=[
        OptionDef(name="short", label="Krátká", text="Buď stručný."),
        OptionDef(name="medium", label="Střední", text="Buď středně dlouhý."),
        OptionDef(name="long", label="Dlouhá", text="Buď podrobný."),
    ],
)

CUSTOM_DEF = PlaceholderDef(label="Vlastní instrukce", kind="text", default="Žádné.")


class PlaceholderEngineTests(unittest.TestCase):
    def test_select_substitutes_chosen_option_text(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"length": LENGTH_DEF},
            selections={"length": "short"},
            system_prompt="Délka: {length}",
            user_prompt_template="Otázka: {question}",
        )
        self.assertIn("Délka: Buď stručný.", messages[0]["content"])

    def test_select_falls_back_to_default_option(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"length": LENGTH_DEF},
            selections={},
            system_prompt="Délka: {length}",
            user_prompt_template="Otázka: {question}",
        )
        self.assertIn("Délka: Buď středně dlouhý.", messages[0]["content"])

    def test_text_uses_default_when_empty(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"custom_instructions": CUSTOM_DEF},
            selections={"custom_instructions": ""},
            user_prompt_template="Instrukce: {custom_instructions}",
        )
        self.assertEqual("Instrukce: Žádné.", messages[-1]["content"])

    def test_text_uses_typed_value(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"custom_instructions": CUSTOM_DEF},
            selections={"custom_instructions": "Odpověz v bodech."},
            user_prompt_template="Instrukce: {custom_instructions}",
        )
        self.assertEqual("Instrukce: Odpověz v bodech.", messages[-1]["content"])

    def test_text_omitted_when_token_absent(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"custom_instructions": CUSTOM_DEF},
            selections={"custom_instructions": "Odpověz v bodech."},
            user_prompt_template="Otázka: {question}",
        )
        self.assertIn("Otázka: Co se stalo?", messages[-1]["content"])
        self.assertNotIn("Odpověz v bodech.", messages[-1]["content"])
        self.assertNotIn("custom_instructions", messages[-1]["content"])

    def test_system_placeholders_fill(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={},
            selections={},
            system_prompt="Datum: {current_date}",
            user_prompt_template="Otázka: {question}\nKontext: {retrieved_snippets}",
            context_text="kontextový text",
        )
        self.assertEqual(f"Datum: {date.today().isoformat()}", messages[0]["content"])
        self.assertIn("Otázka: Co se stalo?", messages[-1]["content"])
        self.assertIn("Kontext: kontextový text", messages[-1]["content"])

    def test_undeclared_token_renders_literally_without_raising(self) -> None:
        messages = build_messages(
            question="Co se stalo?",
            retrieved_chunks=[],
            placeholder_defs={"length": LENGTH_DEF},
            selections={"length": "short"},
            system_prompt="Délka: {length}\nNeznámé: {avatar_name}",
            user_prompt_template="Otázka: {question}\nNeznámé: {audience}",
        )
        self.assertIn("Délka: Buď stručný.", messages[0]["content"])
        self.assertIn("{avatar_name}", messages[0]["content"])
        self.assertIn("{audience}", messages[-1]["content"])


class ResolutionTests(unittest.TestCase):
    def _shared(self) -> dict[str, PlaceholderDef]:
        return {
            "length": PlaceholderDef(
                label="Délka",
                kind="select",
                default="medium",
                options=[OptionDef(name="short", label="Krátká", text="SHARED short")],
            )
        }

    def _code(self) -> dict[str, PlaceholderDef]:
        return {
            "length": PlaceholderDef(
                label="Délka",
                kind="select",
                default="medium",
                options=[OptionDef(name="medium", label="Střední", text="CODE medium")],
            )
        }

    def test_full_four_layer_precedence_no_merging(self) -> None:
        inline = {"length": PlaceholderDef(label="i", default="INLINE")}
        local = {"length": PlaceholderDef(label="l", default="LOCAL")}
        # inline wins
        defs = resolve_placeholder_defs(
            {"length"},
            inline_defs=inline,
            local_global_defs=local,
            shared_global_defs=self._shared(),
            code_default_defs=self._code(),
        )
        self.assertEqual(defs["length"].default, "INLINE")
        self.assertEqual(defs["length"].options, [])
        # without inline, local wins
        defs = resolve_placeholder_defs(
            {"length"},
            local_global_defs=local,
            shared_global_defs=self._shared(),
            code_default_defs=self._code(),
        )
        self.assertEqual(defs["length"].default, "LOCAL")
        # without inline/local, shared wins
        defs = resolve_placeholder_defs(
            {"length"},
            shared_global_defs=self._shared(),
            code_default_defs=self._code(),
        )
        self.assertEqual(defs["length"].options[0].text, "SHARED short")
        # only code floor left
        defs = resolve_placeholder_defs({"length"}, code_default_defs=self._code())
        self.assertEqual(defs["length"].options[0].text, "CODE medium")

    def test_system_placeholders_are_never_resolved(self) -> None:
        defs = resolve_placeholder_defs(
            {"question", "retrieved_snippets", "current_date"},
            shared_global_defs=self._shared(),
        )
        self.assertEqual(defs, {})

    def test_undeclared_name_absent_from_result(self) -> None:
        defs = resolve_placeholder_defs({"mystery"}, shared_global_defs=self._shared())
        self.assertNotIn("mystery", defs)


if __name__ == "__main__":
    unittest.main()
