from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import main


class RandomQuestionEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app)
        self._original_project_root = main.project_root
        self._tmp = tempfile.TemporaryDirectory()
        main.project_root = Path(self._tmp.name)

    def tearDown(self) -> None:
        main.project_root = self._original_project_root
        self._tmp.cleanup()

    def _write_questions(self, relative_path: str, content: str) -> None:
        path = main.project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_random_question_uses_selected_wp_path(self) -> None:
        self._write_questions("data/questions/wp3-pravo.txt", "Co je právní norma?\n")

        response = self.client.get("/questions/random", params={"wp_id": "WP3-právo"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"question": "Co je právní norma?", "wp_id": "WP3-právo"})

    def test_random_question_falls_back_to_default_wp(self) -> None:
        self._write_questions("data/questions/wp1-historie.txt", "Kdo byl Karel IV.?\n")

        response = self.client.get("/questions/random", params={"wp_id": "unknown"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"question": "Kdo byl Karel IV.?", "wp_id": "WP1-historie"})

    def test_random_question_reports_empty_wp_file(self) -> None:
        self._write_questions("data/questions/wp2-media.txt", "\n")

        response = self.client.get("/questions/random", params={"wp_id": "WP2-média"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("WP2-média", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
