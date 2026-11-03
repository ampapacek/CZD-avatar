"""A user-supplied API URL must not let the server reach its own network."""

import socket
import unittest
from unittest.mock import patch

import httpx

from app import main
from app.rag.llm import OpenAICompatibleLLM, check_public_base_url, validate_api_key


def resolves_to(*addresses):
    family = {4: socket.AF_INET, 6: socket.AF_INET6}
    return lambda host, port, **_: [
        (family[6 if ":" in address else 4], socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses
    ]


class CheckPublicBaseUrlTests(unittest.TestCase):
    def test_internal_addresses_are_refused(self) -> None:
        for url in (
            "https://127.0.0.1:8000/v1",
            "https://localhost/v1",
            "https://10.0.0.5/v1",
            "https://192.168.1.1/v1",
            "https://169.254.169.254/latest",
            "https://[::1]/v1",
            "https://[::ffff:127.0.0.1]/v1",
            "https://0.0.0.0/v1",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_public_base_url(url)

    def test_a_name_with_any_internal_address_is_refused(self) -> None:
        with patch("socket.getaddrinfo", resolves_to("8.8.8.8", "10.1.2.3")), self.assertRaises(ValueError):
            check_public_base_url("https://mixed.example/v1")

    def test_public_names_pass(self) -> None:
        with patch("socket.getaddrinfo", resolves_to("8.8.8.8", "2001:4860:4860::8888")):
            check_public_base_url("https://api.example/v1")

    def test_other_schemes_and_unknown_hosts_are_refused(self) -> None:
        # Plain http too: only TLS stops a rebound name from reaching an internal host.
        for url in ("file:///etc/passwd", "ftp://8.8.8.8/", "https:///v1", "https://8.8.8.8:99999/", "http://8.8.8.8/v1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_public_base_url(url)
        with patch("socket.getaddrinfo", side_effect=socket.gaierror), self.assertRaises(ValueError):
            check_public_base_url("https://nowhere.example/v1")

    def test_non_ascii_hosts_are_refused(self) -> None:
        # The stdlib and httpx convert "ß" differently, so the check would look
        # up another name than the one httpx connects to.
        with patch("socket.getaddrinfo", resolves_to("8.8.8.8")), self.assertRaises(ValueError):
            check_public_base_url("https://faß.example/v1")


class ResolveRequestTests(unittest.TestCase):
    def test_custom_internal_url_is_refused_before_any_request(self) -> None:
        with patch.object(main, "validate_api_key") as validate, self.assertRaises(main.HTTPException) as caught:
            main._resolve_llm_request(
                main.ChatRequest(question="x", llm_base_url="https://127.0.0.1:6333", llm_api_key="k")
            )
        self.assertEqual(caught.exception.status_code, 400)
        validate.assert_not_called()

    def test_configured_provider_url_is_trusted(self) -> None:
        # The test provider's host does not resolve; it must not be looked up.
        with patch("socket.getaddrinfo", side_effect=AssertionError("looked up")):
            resolved = main._resolve_llm_request(
                main.ChatRequest(question="x", llm_base_url="https://llm.test.invalid/v1/")
            )
        self.assertEqual(resolved[2], "test-key")


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


class ValidateApiKeyErrorTests(unittest.TestCase):
    def check(self, response=None, error=None) -> str:
        def get(url, **_):
            if error:
                raise error
            return httpx.Response(response, request=httpx.Request("GET", url), text="internal secret page")

        with patch("httpx.get", get), self.assertRaises(RuntimeError) as caught:
            validate_api_key("key", "https://api.example/v1")
        return str(caught.exception)

    def test_upstream_body_is_not_passed_on(self) -> None:
        self.assertEqual(self.check(401), "The API key was rejected (401).")
        self.assertEqual(self.check(500), "The API key could not be checked (500).")
        self.assertNotIn("secret", self.check(404))

    def test_unreachable_url_is_a_clear_error(self) -> None:
        self.assertEqual(self.check(error=httpx.ConnectError("boom")), "The API URL could not be reached.")


if __name__ == "__main__":
    unittest.main()
