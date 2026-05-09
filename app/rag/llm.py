from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Iterator

import httpx


@dataclass(slots=True)
class LLMGeneration:
    answer: str
    model: str | None = None


class LLMClient:
    """Replaceable LLM interface."""

    model: str

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> LLMGeneration:
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
    """OpenAI-compatible chat completions client."""

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
    ) -> LLMGeneration:
        resolved_api_key = api_key or self.api_key
        resolved_base_url = (base_url or self.base_url).rstrip("/")

        resolved_model = model or self.model
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "rag-avatar",
        }
        if resolved_api_key:
            headers["Authorization"] = f"Bearer {resolved_api_key}"
        payload = _chat_payload(
            model=resolved_model,
            messages=messages,
        )
        response = httpx.post(
            f"{resolved_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = _extract_error_message(response)
            raise RuntimeError(_format_http_error(response, message)) from exc
        data = response.json()
        return LLMGeneration(
            answer=data["choices"][0]["message"]["content"].strip(),
            model=str(data.get("model") or resolved_model),
        )

    def stream_generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> Iterator[str]:
        return _OpenAICompatibleStream(
            api_key=api_key or self.api_key,
            model=model or self.model,
            base_url=(base_url or self.base_url).rstrip("/"),
            messages=messages,
            timeout=self.timeout,
        )


def validate_api_key(api_key: str, base_url: str, timeout: float = 20.0) -> None:
    resolved_api_key = api_key.strip()
    if not resolved_api_key:
        raise RuntimeError("API key is empty.")

    resolved_base_url = base_url.rstrip("/")
    response = httpx.get(
        f"{resolved_base_url}/models",
        headers={
            "Authorization": f"Bearer {resolved_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "rag-avatar",
        },
        timeout=timeout,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = _extract_error_message(response)
        raise RuntimeError(_format_http_error(response, message)) from exc


class _OpenAICompatibleStream:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        messages: list[dict[str, str]],
        timeout: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.messages = messages
        self.timeout = timeout
        self.upstream_model: str | None = None

    def __iter__(self) -> Iterator[str]:
        payload = _chat_payload(
            model=self.model,
            messages=self.messages,
            stream=True,
        )
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "rag-avatar",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
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
                    event_model = event.get("model")
                    if isinstance(event_model, str) and event_model.strip():
                        self.upstream_model = event_model.strip()
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


def _chat_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    stream: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": messages,
    }
    if stream:
        payload["stream"] = True
    if _supports_custom_temperature(model):
        payload["temperature"] = 0.2
    return payload


def _supports_custom_temperature(model: str) -> bool:
    normalized = model.lower().removeprefix("openai/").removeprefix("azure/")
    return not (
        normalized.startswith("gpt-5")
        or normalized.startswith("o1")
        or normalized.startswith("o3")
        or normalized.startswith("o4")
    )


def _format_http_error(response: httpx.Response, message: str) -> str:
    retry_after = response.headers.get("retry-after")
    details = f"LLM request failed ({response.status_code}): {message}"
    if response.status_code == 429:
        if retry_after:
            return f"{details}. Retry after {retry_after} seconds."
        return f"{details}. The upstream model is rate-limiting requests."
    return details
