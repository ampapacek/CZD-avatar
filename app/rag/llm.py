from __future__ import annotations

import json
import time
from contextlib import nullcontext
from dataclasses import dataclass
from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import httpx

from app.analytics import bind_context, current_context, emit, endpoint_host, error_code, estimated_tokens, ms


@dataclass(slots=True)
class LLMGeneration:
    answer: str
    model: str | None = None
    # Reasoning traces the model returned. Kept rather than discarded: some
    # models cannot be told to stop reasoning, and silently dropping the text
    # hides both the cost and what the model was doing.
    reasoning: str = ""


# Providers disagree on the field name for reasoning traces.
REASONING_FIELDS = ("reasoning", "reasoning_content")


def _reasoning_text(payload: dict | None) -> str:
    for field_name in REASONING_FIELDS:
        value = (payload or {}).get(field_name)
        if isinstance(value, str) and value:
            return value
    return ""


ANSWER = "answer"
REASONING = "reasoning"

#: One piece of the stream: ``(ANSWER | REASONING, text)``.
StreamChunk = tuple[str, str]


@runtime_checkable
class TokenStream(Protocol):
    """Contract for ``stream_generate`` return values.

    Callers iterate the stream to receive ``(kind, text)`` chunks, then read
    ``upstream_model`` (populated as a side effect of iteration) to learn the
    model the upstream provider actually served. Implementations and test
    doubles must expose both; a bare generator does not satisfy this.

    The two kinds are interleaved as the provider sends them, which in practice
    means a reasoning model emits its whole trace before its first answer token.
    That is exactly why the kinds are yielded rather than the trace being held
    back until the end: waiting is the part the reader most wants to see into.
    ``reasoning_text`` still accumulates the whole trace for the caller that
    wants it in one piece.
    """

    upstream_model: str | None
    reasoning_text: str

    def __iter__(self) -> Iterator[StreamChunk]: ...


class LLMClient:
    """Replaceable LLM interface."""

    model: str

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        reasoning: dict[str, object] | None = None,
    ) -> LLMGeneration:
        raise NotImplementedError

    def stream_generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        reasoning: dict[str, object] | None = None,
    ) -> TokenStream:
        raise NotImplementedError


class OpenAICompatibleLLM(LLMClient):
    """OpenAI-compatible chat completions client."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 120.0) -> None:
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
        reasoning: dict[str, object] | None = None,
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
            reasoning=reasoning,
        )
        started = time.perf_counter()
        response = None
        try:
            response = httpx.post(
                f"{resolved_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            answer = message["content"].strip()
            reasoning_text = _reasoning_text(message).strip()
            upstream_model = str(data.get("model") or resolved_model)
            _emit_upstream(
                started, messages, answer, resolved_model, upstream_model, resolved_base_url,
                streaming=False, status="ok", upstream_http_status=response.status_code,
            )
            return LLMGeneration(answer=answer, model=upstream_model, reasoning=reasoning_text)
        except Exception as exc:
            status = response.status_code if response is not None else None
            _emit_upstream(
                started, messages, "", resolved_model, None, resolved_base_url,
                streaming=False, status="error", upstream_http_status=status,
                event_error_code=error_code(exc, status),
            )
            if isinstance(exc, httpx.HTTPStatusError) and response is not None:
                message = _extract_error_message(response)
                raise RuntimeError(_format_http_error(response, message)) from exc
            raise

    def stream_generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        reasoning: dict[str, object] | None = None,
    ) -> TokenStream:
        return _OpenAICompatibleStream(
            api_key=api_key or self.api_key,
            model=model or self.model,
            base_url=(base_url or self.base_url).rstrip("/"),
            messages=messages,
            timeout=self.timeout,
            analytics_context=current_context(),
            reasoning=reasoning,
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
        analytics_context=None,
        reasoning: dict[str, object] | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.messages = messages
        self.timeout = timeout
        self.upstream_model: str | None = None
        self.analytics_context = analytics_context
        self.reasoning = reasoning
        # Reasoning deltas arrive interleaved with content and are yielded under
        # their own kind, so a caller can show the trace as it is written while
        # keeping it out of the answer. Also joined here for the caller that
        # wants the finished trace in one piece.
        self.reasoning_text: str = ""

    def __iter__(self) -> Iterator[StreamChunk]:
        started = time.perf_counter()
        answer_parts: list[str] = []
        reasoning_parts: list[str] = []
        payload = _chat_payload(
            model=self.model,
            messages=self.messages,
            stream=True,
            reasoning=self.reasoning,
        )
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "rag-avatar",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = None
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                ) as response:
                    _raise_for_status_with_body(response)
                    for line in response.iter_lines():
                        if not line or not line.startswith("data:"):
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
                        reasoning_delta = _reasoning_text(delta)
                        if reasoning_delta:
                            reasoning_parts.append(reasoning_delta)
                            self.reasoning_text = "".join(reasoning_parts)
                            yield (REASONING, reasoning_delta)
                        content = delta.get("content")
                        if content:
                            text = str(content)
                            answer_parts.append(text)
                            yield (ANSWER, text)
            context_manager = bind_context(self.analytics_context) if self.analytics_context else nullcontext()
            with context_manager:
                _emit_upstream(
                    started, self.messages, "".join(answer_parts), self.model,
                    self.upstream_model or self.model, self.base_url, streaming=True,
                    status="ok", upstream_http_status=response.status_code if response else None,
                )
        except GeneratorExit:
            context_manager = bind_context(self.analytics_context) if self.analytics_context else nullcontext()
            with context_manager:
                _emit_upstream(
                    started, self.messages, "".join(answer_parts), self.model, self.upstream_model,
                    self.base_url, streaming=True, status="cancelled",
                    upstream_http_status=response.status_code if response else None,
                    event_error_code="client_cancelled",
                )
            raise
        except Exception as exc:
            status = response.status_code if response is not None else None
            context_manager = bind_context(self.analytics_context) if self.analytics_context else nullcontext()
            with context_manager:
                _emit_upstream(
                    started, self.messages, "".join(answer_parts), self.model, self.upstream_model,
                    self.base_url, streaming=True, status="error", upstream_http_status=status,
                    event_error_code=error_code(exc, status),
                )
            if isinstance(exc, httpx.HTTPStatusError) and response is not None:
                message = _extract_error_message(response)
                raise RuntimeError(_format_http_error(response, message)) from exc
            raise


def _emit_upstream(
    started: float,
    messages: list[dict[str, str]],
    answer: str,
    requested_model: str,
    upstream_model: str | None,
    base_url: str,
    *,
    streaming: bool,
    status: str,
    upstream_http_status: int | None,
    event_error_code: str | None = None,
) -> None:
    context = current_context()
    input_text = "\n".join(str(message.get("content") or "") for message in messages)
    emit(
        "upstream_call",
        status=status,
        duration_ms=ms(time.perf_counter() - started),
        purpose=context.purpose if context else "other",
        provider=context.provider if context else None,
        requested_model=requested_model,
        upstream_model=upstream_model,
        endpoint_host=endpoint_host(base_url),
        key_source=context.key_source if context else ("server" if base_url else "none"),
        streaming=streaming,
        upstream_http_status=upstream_http_status,
        input_chars=len(input_text),
        input_tokens_estimated=estimated_tokens(input_text),
        output_chars=len(answer),
        output_tokens_estimated=estimated_tokens(answer),
        error_code=event_error_code,
    )


def _raise_for_status_with_body(response: httpx.Response) -> None:
    """`raise_for_status`, but keep the error body readable.

    A streaming response only holds its body while `client.stream(...)` is open.
    Raising here and reading later got us the opposite of an error message: the
    body was gone, so `_extract_error_message` reported httpx complaining about
    an unread stream instead of the "rate limit exceeded" the provider sent.
    Read it while we still can — it is an error payload, so it is small.
    """
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        try:
            response.read()
        except Exception:  # A body we cannot read must not mask the status.
            pass
        raise


def _extract_error_message(response: httpx.Response) -> str:
    try:
        response.read()
    except Exception:
        # Already read, or no longer readable. Either way the decoding below
        # says what is actually available.
        pass

    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError, httpx.ResponseNotRead, httpx.StreamError):
        try:
            return response.text[:500] or "No response body."
        except (httpx.ResponseNotRead, httpx.StreamError):
            return "No response body."

    if not isinstance(payload, dict):
        # Not every gateway answers an error with an object.
        return str(payload)[:500]

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
    reasoning: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": messages,
    }
    if stream:
        payload["stream"] = True
    if _supports_custom_temperature(model):
        payload["temperature"] = 0.2
    # Only ever what the model's declared metadata produced; strict servers 400
    # on unknown fields, so nothing is sent speculatively.
    if reasoning:
        payload.update(reasoning)
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
