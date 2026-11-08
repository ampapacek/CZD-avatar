from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app import main


class RandomQuestionEndpointTests(unittest.TestCase):
    """Questions come from the WP's ``questions`` list in the instance config."""

    def setUp(self) -> None:
        self.client = TestClient(main.app)

    def test_random_question_uses_selected_wp_list(self) -> None:
        response = self.client.get("/questions/random", params={"wp_id": "WP1-historie"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["wp_id"], "WP1-historie")
        self.assertIn(response.json()["question"], ["Kdo byl Karel IV.?", "Co byla normalizace?"])

    def test_questions_list_keeps_the_configured_order(self) -> None:
        response = self.client.get("/questions", params={"wp_id": "WP1-historie"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"questions": ["Kdo byl Karel IV.?", "Co byla normalizace?"], "wp_id": "WP1-historie"},
        )

    def test_no_wp_id_uses_the_default_wp(self) -> None:
        response = self.client.get("/questions")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["wp_id"], "WP1-historie")

    def test_unknown_wp_is_not_found(self) -> None:
        response = self.client.get("/questions/random", params={"wp_id": "unknown"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("unknown", response.json()["detail"])

    def test_wp_without_questions_is_not_found(self) -> None:
        response = self.client.get("/questions/random", params={"wp_id": "WP3-právo"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("WP3-právo", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
