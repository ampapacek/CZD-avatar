"""A server key must never be sent to a URL taken from a request."""

import socket
import unittest
from unittest.mock import patch

import httpx

from app import main
from app.rag.llm import OpenAICompatibleLLM


def resolves_to(*addresses):
    family = {4: socket.AF_INET, 6: socket.AF_INET6}
    return lambda host, port, **_: [
        (family[6 if ":" in address else 4], socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses
    ]



class ServerKeyStaysWithItsUrlTests(unittest.TestCase):
    """The real resolver and the real client together; only HTTP is mocked."""

    def setUp(self) -> None:
        self.sent: list[httpx.Request] = []
        # The client the pipeline builds: the default provider's URL and server key.
        self.llm = OpenAICompatibleLLM("test-key", "test-model", "https://llm.test.invalid/v1")

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.sent.append(request)
        if b'"stream":true' in request.content.replace(b" ", b""):
            return httpx.Response(200, content=b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n')
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    def call(self, base_url: str, *, streaming: bool) -> httpx.Request:
        request = main.ChatRequest(question="x", model="test-model", llm_base_url=base_url)
        with patch("socket.getaddrinfo", resolves_to("93.184.215.14")):
            _, model, api_key, resolved_base_url = main._resolve_llm_request(request)
        transport = httpx.MockTransport(self.handler)
        messages = [{"role": "user", "content": "q"}]
        if streaming:
            with patch("app.rag.llm.httpx.Client", return_value=httpx.Client(transport=transport)):
                list(self.llm.stream_generate(messages, model=model, api_key=api_key, base_url=resolved_base_url))
        else:
            with httpx.Client(transport=transport) as client, patch("app.rag.llm.httpx.post", client.post):
                self.llm.generate(messages, model=model, api_key=api_key, base_url=resolved_base_url)
        return self.sent[-1]

    def test_custom_url_without_a_key_gets_no_server_key(self) -> None:
        for streaming in (False, True):
            with self.subTest(streaming=streaming):
                sent = self.call("https://attacker.example/v1", streaming=streaming)
                self.assertEqual(str(sent.url), "https://attacker.example/v1/chat/completions")
                self.assertNotIn("authorization", sent.headers)

    def test_configured_url_still_gets_the_server_key(self) -> None:
        for streaming in (False, True):
            with self.subTest(streaming=streaming):
                sent = self.call("https://llm.test.invalid/v1", streaming=streaming)
                self.assertEqual(sent.headers["authorization"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
