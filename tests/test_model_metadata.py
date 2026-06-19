from pathlib import Path
import tempfile
import unittest

from app.rag.model_metadata import load_model_context_metadata, load_model_context_windows


class ModelMetadataTests(unittest.TestCase):
    def test_load_model_context_windows_ignores_invalid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model_context_windows.json"
            path.write_text(
                """
                {
                  "valid-model": 8192,
                  "string-number": "4096",
                  "too-small": 512,
                  "invalid": "many"
                }
                """,
                encoding="utf-8",
            )

            self.assertEqual(
                load_model_context_windows(path),
                {
                    "valid-model": 8192,
                    "string-number": 4096,
                },
            )

    def test_load_model_context_windows_missing_file_is_empty(self) -> None:
        self.assertEqual(load_model_context_windows(Path("does-not-exist.json")), {})

    def test_load_model_context_metadata_supports_provider_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model_context_windows.json"
            path.write_text(
                """
                {
                  "models": {
                    "known-model": 8192
                  },
                  "provider_defaults": {
                    "OpenRouter": 50000
                  }
                }
                """,
                encoding="utf-8",
            )

            self.assertEqual(load_model_context_metadata(path), ({"known-model": 8192}, {"OpenRouter": 50000}))


if __name__ == "__main__":
    unittest.main()
