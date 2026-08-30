"""What the user is told when an upstream call fails.

An error path that raises its own error is worse than no error path: the
provider's reason ("rate limited", "no such model") is replaced by a complaint
about our plumbing, and every distinct upstream failure starts looking alike.
These tests pin the reason surviving all the way to the caller.
"""

import json
import unittest
from unittest.mock import patch

import httpx

from app.rag.llm import OpenAICompatibleLLM


class StreamingErrorTests(unittest.TestCase):
    def _stream_failure(self, status: int, body: bytes, headers: dict | None = None) -> str:
        client = OpenAICompatibleLLM("key", "model", "https://provider.example/v1")
        stream = client.stream_generate([{"role": "user", "content": "q"}])

        def handler(request):
            # A one-shot iterator, not `content=`: a real network body can only
            # be read once and only while the response is open, and a mock that
            # hands back a rewindable buffer would pass no matter when we read.
            return httpx.Response(
                status, request=request, headers=headers or {}, content=iter([body])
            )

        transport = httpx.MockTransport(handler)
        with patch("app.rag.llm.httpx.Client", return_value=httpx.Client(transport=transport)):
            with self.assertRaises(RuntimeError) as caught:
                list(stream)
        return str(caught.exception)

    def test_the_provider_reason_survives_the_closing_of_the_stream(self) -> None:
        # `client.stream(...)` closes the response on the way out, taking the
        # body with it. Reading the error body only after that got every 4xx and
        # 5xx reported as httpx's "without having called read()", which is not a
        # thing any provider ever said.
        message = self._stream_failure(
            429,
            json.dumps({"error": {"message": "Rate limit exceeded"}}).encode(),
            {"content-type": "application/json", "retry-after": "13"},
        )
        self.assertIn("Rate limit exceeded", message)
        self.assertIn("429", message)
        self.assertIn("Retry after 13 seconds", message)
        self.assertNotIn("read()", message)

    def test_a_non_json_error_body_is_reported_as_text(self) -> None:
        message = self._stream_failure(
            502, b"<html>bad gateway</html>", {"content-type": "text/html"}
        )
        self.assertIn("bad gateway", message)
        self.assertIn("502", message)

    def test_an_empty_error_body_still_reports_the_status(self) -> None:
        message = self._stream_failure(500, b"")
        self.assertIn("500", message)
        self.assertIn("No response body", message)


class NonStreamingErrorTests(unittest.TestCase):
    def test_the_provider_reason_reaches_the_caller(self) -> None:
        client = OpenAICompatibleLLM("key", "model", "https://provider.example/v1")
        response = httpx.Response(
            404,
            request=httpx.Request("POST", "https://provider.example/v1/chat/completions"),
            headers={"content-type": "application/json"},
            content=json.dumps({"error": {"message": "No such model"}}).encode(),
        )
        with patch("app.rag.llm.httpx.post", return_value=response):
            with self.assertRaises(RuntimeError) as caught:
                client.generate([{"role": "user", "content": "q"}])
        self.assertIn("No such model", str(caught.exception))

    def test_an_error_body_that_is_not_an_object_is_not_a_crash(self) -> None:
        # Some gateways answer with a bare string or a list of errors.
        client = OpenAICompatibleLLM("key", "model", "https://provider.example/v1")
        response = httpx.Response(
            400,
            request=httpx.Request("POST", "https://provider.example/v1/chat/completions"),
            headers={"content-type": "application/json"},
            content=json.dumps(["reasoning_effort is not supported"]).encode(),
        )
        with patch("app.rag.llm.httpx.post", return_value=response):
            with self.assertRaises(RuntimeError) as caught:
                client.generate([{"role": "user", "content": "q"}])
        self.assertIn("reasoning_effort is not supported", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
