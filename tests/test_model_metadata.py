"""`data/models.json` — one entry per model, context window plus reasoning.

The file is the only place model facts are declared, so these tests pin what a
malformed or partial entry does: a bad field is dropped, the rest of the entry
survives, and a broken file is never fatal.
"""

import json
import tempfile
import unittest
from pathlib import Path

from app.rag.model_metadata import OFF_EFFORTS, load_model_metadata


def write_metadata(payload: object) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / "models.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class ModelMetadataTests(unittest.TestCase):
    def test_missing_file_declares_nothing(self) -> None:
        metadata = load_model_metadata(Path("does-not-exist.json"))
        self.assertEqual(metadata.context_windows, {})
        self.assertEqual(metadata.reasoning, {})

    def test_malformed_file_is_ignored_rather_than_fatal(self) -> None:
        path = Path(tempfile.mkdtemp()) / "models.json"
        path.write_text("{not json", encoding="utf-8")
        metadata = load_model_metadata(path)
        self.assertEqual(metadata.context_windows, {})
        self.assertEqual(metadata.reasoning, {})

    def test_reads_context_windows_and_reasoning_from_one_entry(self) -> None:
        path = write_metadata(
            {
                "models": {
                    "m": {
                        "context_window": 65500,
                        "reasoning": {"param": "reasoning", "efforts": ["none", "low"], "default": "none"},
                    }
                },
                "provider_defaults": {
                    "P": {"context_window": 16000, "reasoning": {"efforts": ["low", "high"]}}
                },
            }
        )
        metadata = load_model_metadata(path)
        self.assertEqual(metadata.context_windows, {"m": 65500})
        self.assertEqual(metadata.reasoning["m"].efforts, ("none", "low"))
        self.assertEqual(metadata.reasoning["m"].default, "none")
        self.assertEqual(metadata.provider_context_windows, {"P": 16000})
        self.assertEqual(metadata.provider_reasoning["P"].param, "reasoning_effort")

    def test_context_window_and_reasoning_are_independent(self) -> None:
        # A model may declare either half; a bad half must not take the other with it.
        path = write_metadata(
            {
                "models": {
                    "window-only": {"context_window": 8192},
                    "reasoning-only": {"reasoning": {"efforts": ["low"]}},
                    "bad-window-good-reasoning": {
                        "context_window": "many",
                        "reasoning": {"efforts": ["low"]},
                    },
                }
            }
        )
        metadata = load_model_metadata(path)
        self.assertEqual(metadata.context_windows, {"window-only": 8192})
        self.assertEqual(
            sorted(metadata.reasoning), ["bad-window-good-reasoning", "reasoning-only"]
        )

    def test_unusable_context_windows_are_dropped(self) -> None:
        path = write_metadata(
            {
                "models": {
                    "valid": {"context_window": 8192},
                    "string-number": {"context_window": "4096"},
                    "too-small": {"context_window": 512},
                    "not-a-number": {"context_window": "many"},
                    "not-an-object": "8192",
                }
            }
        )
        self.assertEqual(
            load_model_metadata(path).context_windows,
            {"valid": 8192, "string-number": 4096},
        )

    def test_unusable_reasoning_declarations_are_dropped(self) -> None:
        path = write_metadata(
            {
                "models": {
                    "bad-param": {"reasoning": {"param": "think_harder", "efforts": ["low"]}},
                    "says-nothing": {"reasoning": {"efforts": []}},
                    "not-an-object": {"reasoning": "low"},
                    "bad-default": {"reasoning": {"efforts": ["low"], "default": "extreme"}},
                }
            }
        )
        metadata = load_model_metadata(path)
        self.assertEqual(list(metadata.reasoning), ["bad-default"])
        # The entry survives; only the unusable default is dropped.
        self.assertIsNone(metadata.reasoning["bad-default"].default)

    def test_reasoning_without_efforts_is_kept_when_it_is_mandatory(self) -> None:
        # "Reasons anyway, but we cannot steer it" — no control, trace still shown.
        path = write_metadata({"models": {"m": {"reasoning": {"mandatory": True, "note": "gateway drops it"}}}})
        support = load_model_metadata(path).reasoning["m"]
        self.assertEqual(support.efforts, ())
        self.assertFalse(support.controllable)
        self.assertTrue(support.mandatory)
        self.assertEqual(support.note, "gateway drops it")
        self.assertEqual(support.payload("high"), {})


    def test_mandatory_reasoning_loses_its_off_switch(self) -> None:
        # `openai/gpt-oss-120b` shipped `mandatory` alongside "none", and
        # OpenRouter answers "none" with a 400 that killed every answer. The
        # steerable levels survive; the switch that cannot work does not.
        path = write_metadata(
            {
                "models": {
                    "m": {
                        "reasoning": {
                            "mandatory": True,
                            "efforts": ["none", "off", "low", "high"],
                            "default": "none",
                        }
                    }
                }
            }
        )
        support = load_model_metadata(path).reasoning["m"]
        self.assertEqual(support.efforts, ("low", "high"))
        # The default went with it rather than being sent as an unlisted value.
        self.assertIsNone(support.default)
        self.assertEqual(support.payload("none"), {})
        self.assertEqual(support.payload(None), {})

    def test_optional_reasoning_keeps_its_off_switch(self) -> None:
        path = write_metadata(
            {"models": {"m": {"reasoning": {"efforts": ["none", "high"], "default": "none"}}}}
        )
        support = load_model_metadata(path).reasoning["m"]
        self.assertEqual(support.efforts, ("none", "high"))
        self.assertEqual(support.payload(None), {"reasoning_effort": "none"})


class ShippedMetadataTests(unittest.TestCase):
    """The file we actually ship must parse — a typo here silently drops a model."""

    def test_shipped_file_parses_and_declares_the_models_we_serve(self) -> None:
        metadata = load_model_metadata(Path("data/models.json"))
        declared = json.loads(Path("data/models.json").read_text(encoding="utf-8"))["models"]
        for name, entry in declared.items():
            if "context_window" in entry:
                self.assertIn(name, metadata.context_windows, f"{name} lost its context window")
            if "reasoning" in entry:
                self.assertIn(name, metadata.reasoning, f"{name} lost its reasoning declaration")

    def test_no_shipped_model_offers_an_off_switch_it_does_not_have(self) -> None:
        # The loader strips the contradiction, so a typo here is silent rather
        # than fatal. Catch it in the file instead.
        declared = json.loads(Path("data/models.json").read_text(encoding="utf-8"))
        for group in ("models", "provider_defaults"):
            for name, entry in declared.get(group, {}).items():
                reasoning = entry.get("reasoning") or {}
                if not reasoning.get("mandatory"):
                    continue
                offered = set(reasoning.get("efforts") or [])
                self.assertEqual(
                    offered & set(OFF_EFFORTS),
                    set(),
                    f"{name} is mandatory but offers a way to turn reasoning off",
                )


if __name__ == "__main__":
    unittest.main()
