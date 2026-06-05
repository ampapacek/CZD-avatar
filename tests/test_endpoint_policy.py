import unittest

from fastapi.testclient import TestClient

from app import main


class PolicyErrorStatusTests(unittest.TestCase):
    """The msearch collection policy raises an HTTPException (400). The broad
    ``except Exception`` in /retrieve and /chat must not swallow it into a 500."""

    def setUp(self) -> None:
        self._orig_preset = main.default_provider_preset
        # Force a non-AI-Ufal provider base URL so the WP2 collection policy fires.
        main.default_provider_preset = {**main.default_provider_preset, "base_url": "https://example.com/api"}
        self.client = TestClient(main.app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        main.default_provider_preset = self._orig_preset

    def test_retrieve_policy_violation_returns_400_not_500(self) -> None:
        response = self.client.post(
            "/retrieve",
            json={
                "question": "Cokoliv?",
                "msearch_collection": main.WP2_MSEARCH_COLLECTION,
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("WP2", response.json()["detail"])

    def test_chat_policy_violation_returns_400_not_500(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "question": "Cokoliv?",
                "msearch_collection": main.WP2_MSEARCH_COLLECTION,
                "llm_base_url": "https://example.com/api",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("WP2", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
