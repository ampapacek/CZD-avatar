from __future__ import annotations

import json
from collections.abc import Iterator

import httpx


class LLMClient:
    """Replaceable LLM interface."""

    model: str

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> str:
        raise NotImplementedError

    def stream_generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> Iterator[str]:
        raise NotImplementedError


class OpenAICompatibleLLM(LLMClient):
    """OpenAI-compatible chat completions client, used for OpenRouter by default."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> str:
        resolved_api_key = api_key or self.api_key
        resolved_base_url = (base_url or self.base_url).rstrip("/")
        if not resolved_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to .env or provide an API key in the UI.")

        resolved_model = model or self.model
        response = httpx.post(
            f"{resolved_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {resolved_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "rag-avatar",
            },
            json={
                "model": resolved_model,
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = _extract_error_message(response)
            raise RuntimeError(_format_http_error(response, message)) from exc
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def stream_generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> Iterator[str]:
        resolved_api_key = api_key or self.api_key
        resolved_base_url = (base_url or self.base_url).rstrip("/")
        if not resolved_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to .env or provide an API key in the UI.")

        resolved_model = model or self.model
        payload = {
            "model": resolved_model,
            "messages": messages,
            "temperature": 0.2,
            "stream": True,
        }
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{resolved_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {resolved_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "rag-avatar",
                },
                json=payload,
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    message = _extract_error_message(response)
                    raise RuntimeError(_format_http_error(response, message)) from exc

                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except ValueError:
                        continue
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield str(content)


def _extract_error_message(response: httpx.Response) -> str:
    try:
        response.read()
    except httpx.ResponseNotRead:
        pass
    except Exception:
        pass

    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError):
        try:
            return response.text[:500] or "No response body."
        except httpx.ResponseNotRead:
            return "No response body."

    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error)
    if error:
        return str(error)
    return str(payload)[:500]


def _format_http_error(response: httpx.Response, message: str) -> str:
    retry_after = response.headers.get("retry-after")
    details = f"LLM request failed ({response.status_code}): {message}"
    if response.status_code == 429:
        if retry_after:
            return f"{details}. Retry after {retry_after} seconds."
        return f"{details}. The upstream model is rate-limiting requests."
    return details
