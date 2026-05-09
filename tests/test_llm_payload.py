import unittest

from app.rag.llm import _chat_payload


class LLMPayloadTests(unittest.TestCase):
    def test_omits_temperature_for_gpt5_models(self) -> None:
        payload = _chat_payload(
            model="openai/gpt-5-nano",
            messages=[{"role": "user", "content": "hello"}],
        )

        self.assertNotIn("temperature", payload)

    def test_keeps_temperature_for_regular_models(self) -> None:
        payload = _chat_payload(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": "hello"}],
        )

        self.assertEqual(payload["temperature"], 0.2)

    def test_stream_payload_keeps_stream_flag_without_temperature_for_gpt5(self) -> None:
        payload = _chat_payload(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "hello"}],
            stream=True,
        )

        self.assertTrue(payload["stream"])
        self.assertNotIn("temperature", payload)


if __name__ == "__main__":
    unittest.main()
