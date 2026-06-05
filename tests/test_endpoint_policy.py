import unittest

from fastapi.testclient import TestClient

from app import main


class PolicyErrorStatusTests(unittest.TestCase):
    """The msearch collection policy raises an HTTPException (400). The broad
    ``except Exception`` in /retrieve and /chat must not swallow it into a 500."""

    def setUp(self) -> None:
        self._orig_preset = main.default_provider_preset
        # Force a non-AI-Ufal provider base URL so the gated collection policy fires.
        main.default_provider_preset = {**main.default_provider_preset, "base_url": "https://example.com/api"}
        self.client = TestClient(main.app, raise_server_exceptions=False)
        self.gated_collection = next(iter(main.gated_msearch_collection_ids()))

    def tearDown(self) -> None:
        main.default_provider_preset = self._orig_preset

    def test_retrieve_policy_violation_returns_400_not_500(self) -> None:
        response = self.client.post(
            "/retrieve",
            json={
                "question": "Cokoliv?",
                "msearch_collection": self.gated_collection,
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("AI Ufal", response.json()["detail"])

    def test_retrieve_rejects_local_backend_for_non_wp1(self) -> None:
        response = self.client.post(
            "/retrieve",
            json={
                "question": "Cokoliv?",
                "wp_id": "WP3-právo",
                "retrieval_backend": "local",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Local retrieval", response.json()["detail"])

    def test_chat_policy_violation_returns_400_not_500(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "question": "Cokoliv?",
                "msearch_collection": self.gated_collection,
                "llm_base_url": "https://example.com/api",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("AI Ufal", response.json()["detail"])

    def test_chat_rejects_local_backend_for_non_wp1(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "question": "Cokoliv?",
                "wp_id": "WP4-adiktologie",
                "retrieval_backend": "local",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Local retrieval", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
