from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings
from app.rag.prompts import build_messages, format_context

try:
    import tiktoken
except Exception:  # pragma: no cover - exercised only when dependency is unavailable
    tiktoken = None


class PromptBudgetError(RuntimeError):
    """Raised when required non-source prompt content cannot fit the context window."""

    def __init__(
        self,
        message: str,
        *,
        context_window_tokens: int,
        usable_input_tokens: int,
        reserved_output_tokens: int,
        estimated_non_source_tokens: int,
        over_by_tokens: int,
    ) -> None:
        super().__init__(message)
        self.context_window_tokens = context_window_tokens
        self.usable_input_tokens = usable_input_tokens
        self.reserved_output_tokens = reserved_output_tokens
        self.estimated_non_source_tokens = estimated_non_source_tokens
        self.over_by_tokens = over_by_tokens

    def to_payload(self) -> dict[str, object]:
        return {
            "message": str(self),
            "context_window_tokens": self.context_window_tokens,
            "usable_input_tokens": self.usable_input_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "estimated_non_source_tokens": self.estimated_non_source_tokens,
            "over_by_tokens": self.over_by_tokens,
        }


@dataclass(frozen=True, slots=True)
class PromptBudgetConfig:
    context_window_tokens: int
    output_token_budget_short: int
    output_token_budget_medium: int
    output_token_budget_long: int
    min_prompt_chunks: int
    token_budget_safety_margin: float
    conversation_summary_trigger_tokens: int

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        context_window_tokens: int | None = None,
        output_token_budget_short: int | None = None,
        output_token_budget_medium: int | None = None,
        output_token_budget_long: int | None = None,
        min_prompt_chunks: int | None = None,
        token_budget_safety_margin: float | None = None,
        conversation_summary_trigger_tokens: int | None = None,
    ) -> "PromptBudgetConfig":
        return cls(
            context_window_tokens=context_window_tokens or settings.context_window_tokens,
            output_token_budget_short=output_token_budget_short or settings.output_token_budget_short,
            output_token_budget_medium=output_token_budget_medium or settings.output_token_budget_medium,
            output_token_budget_long=output_token_budget_long or settings.output_token_budget_long,
            min_prompt_chunks=settings.min_prompt_chunks if min_prompt_chunks is None else min_prompt_chunks,
            token_budget_safety_margin=(
                settings.token_budget_safety_margin
                if token_budget_safety_margin is None
                else token_budget_safety_margin
            ),
            conversation_summary_trigger_tokens=(
                conversation_summary_trigger_tokens or settings.conversation_summary_trigger_tokens
            ),
        )

    def output_budget_for_length(self, length: str) -> int:
        if length == "short":
            return self.output_token_budget_short
        if length == "long":
            return self.output_token_budget_long
        return self.output_token_budget_medium

    def usable_input_tokens(self, length: str) -> int:
        input_budget = self.context_window_tokens - self.output_budget_for_length(length)
        return max(0, math.floor(input_budget * (1 - self.token_budget_safety_margin)))


@dataclass(slots=True)
class PromptBudgetResult:
    messages: list[dict[str, str]]
    used_chunks: list[dict[str, Any]]
    omitted_chunks: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)
    context_window_tokens: int = 0
    usable_input_tokens: int = 0
    reserved_output_tokens: int = 0
    estimated_non_source_tokens: int = 0
    estimated_source_tokens: int = 0
    estimated_conversation_history_tokens: int = 0
    estimated_total_input_tokens: int = 0
    trimmed_chunk_count: int = 0
    conversation_summary_used: bool = False

    def metadata(self) -> dict[str, object]:
        return {
            "context_window_tokens": self.context_window_tokens,
            "usable_input_tokens": self.usable_input_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "estimated_non_source_tokens": self.estimated_non_source_tokens,
            "estimated_source_tokens": self.estimated_source_tokens,
            "estimated_conversation_history_tokens": self.estimated_conversation_history_tokens,
            "estimated_total_input_tokens": self.estimated_total_input_tokens,
            "used_chunk_count": len(self.used_chunks),
            "omitted_chunk_count": len(self.omitted_chunks),
            "trimmed_chunk_count": self.trimmed_chunk_count,
            "conversation_summary_used": self.conversation_summary_used,
        }


def estimate_text_tokens(text: str, model: str | None = None) -> int:
    if not text:
        return 0
    encoding = _encoding_for_model(model)
    if encoding is not None:
        return len(encoding.encode(text))
    # Conservative fallback for Czech and markdown-ish prompts.
    return max(1, math.ceil(len(text) / 3.2))


def estimate_messages_tokens(messages: list[dict[str, str]], model: str | None = None) -> int:
    total = 3
    for message in messages:
        total += 4
        total += estimate_text_tokens(str(message.get("role") or ""), model)
        total += estimate_text_tokens(str(message.get("content") or ""), model)
    return total


def prepare_prompt_budget(
    *,
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    style: str,
    length: str,
    model: str,
    config: PromptBudgetConfig,
    custom_instructions: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
    style_prompts: dict[str, str] | None = None,
    length_prompts: dict[str, str] | None = None,
) -> PromptBudgetResult:
    empty_context = ""
    non_source_messages = build_messages(
        question,
        [],
        style,
        length,
        custom_instructions,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        style_prompts=style_prompts,
        length_prompts=length_prompts,
        context_text=empty_context,
    )
    usable_input = config.usable_input_tokens(length)
    reserved_output = config.output_budget_for_length(length)
    non_source_tokens = estimate_messages_tokens(non_source_messages, model)
    history_tokens = estimate_history_tokens_for_prompt(conversation_history, model)
    if non_source_tokens > usable_input:
        over_by = non_source_tokens - usable_input
        raise PromptBudgetError(
            (
                "Prompt is too long before any retrieved sources can be added. "
                f"Configured context window: {config.context_window_tokens} tokens. "
                f"Reserved answer budget: {reserved_output} tokens. "
                f"Usable input budget after safety margin: {usable_input} tokens. "
                f"Current prompt without sources: about {non_source_tokens} tokens, "
                f"which is {over_by} tokens over the limit. "
                "Shorten the system prompt, custom instructions, conversation, or question; "
                "choose a larger-context model; or increase the context window setting."
            ),
            context_window_tokens=config.context_window_tokens,
            usable_input_tokens=usable_input,
            reserved_output_tokens=reserved_output,
            estimated_non_source_tokens=non_source_tokens,
            over_by_tokens=over_by,
        )

    source_budget = max(0, usable_input - non_source_tokens)
    used_chunks, omitted_chunks, warnings = _fit_chunks(
        question=question,
        chunks=retrieved_chunks,
        source_budget=source_budget,
        min_prompt_chunks=config.min_prompt_chunks,
        model=model,
    )
    context_text = format_context(used_chunks)
    messages = build_messages(
        question,
        used_chunks,
        style,
        length,
        custom_instructions,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        style_prompts=style_prompts,
        length_prompts=length_prompts,
        context_text=context_text,
    )
    source_tokens = max(0, estimate_messages_tokens(messages, model) - non_source_tokens)
    total_input_tokens = non_source_tokens + source_tokens
    trimmed_count = sum(1 for chunk in used_chunks if chunk.get("metadata", {}).get("budget_status") == "trimmed")
    if omitted_chunks:
        warnings.append(f"{len(omitted_chunks)} retrieved chunks were omitted because of the context budget.")
    if trimmed_count:
        warnings.append(f"{trimmed_count} chunks were trimmed before being sent to the model.")
    if retrieved_chunks and not used_chunks:
        warnings.append("No retrieved chunks fit into the remaining context budget; the model answered without sources.")

    return PromptBudgetResult(
        messages=messages,
        used_chunks=used_chunks,
        omitted_chunks=omitted_chunks,
        warnings=warnings,
        context_window_tokens=config.context_window_tokens,
        usable_input_tokens=usable_input,
        reserved_output_tokens=reserved_output,
        estimated_non_source_tokens=non_source_tokens,
        estimated_source_tokens=source_tokens,
        estimated_conversation_history_tokens=history_tokens,
        estimated_total_input_tokens=total_input_tokens,
        trimmed_chunk_count=trimmed_count,
    )


def estimate_history_tokens_for_prompt(history: list[dict[str, str]] | None, model: str | None = None) -> int:
    messages = _history_messages_for_prompt(history)
    if not messages:
        return 0
    return sum(
        4
        + estimate_text_tokens(message["role"], model)
        + estimate_text_tokens(message["content"], model)
        for message in messages
    )


def conversation_history_tokens(history: list[dict[str, str]] | None, model: str | None = None) -> int:
    messages = [
        {"role": turn.get("role", ""), "content": (turn.get("content") or "").strip()}
        for turn in (history or [])
        if turn.get("role") in {"user", "assistant"} and (turn.get("content") or "").strip()
    ]
    return estimate_messages_tokens(messages, model) if messages else 0


def summarized_history(summary: str, history: list[dict[str, str]] | None, recent_turns: int = 6) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    clean_summary = summary.strip()
    if clean_summary:
        result.append(
            {
                "role": "assistant",
                "content": f"Shrnutí předchozí konverzace pro navazující odpověď:\n{clean_summary}",
            }
        )
    result.extend((history or [])[-recent_turns:])
    return result


def _history_messages_for_prompt(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    messages = []
    for turn in (history or [])[-8:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    return messages


def _fit_chunks(
    *,
    question: str,
    chunks: list[dict[str, Any]],
    source_budget: int,
    min_prompt_chunks: int,
    model: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    original_chunks = chunks
    if not chunks or source_budget <= 0:
        return [], [_mark_chunk(chunk, "omitted") for chunk in chunks], warnings

    selected: list[dict[str, Any]] = []
    for chunk in chunks:
        candidate = [*selected, _mark_chunk(chunk, "used")]
        if estimate_text_tokens(format_context(candidate), model) <= source_budget:
            selected = candidate
        else:
            break

    if len(selected) >= min(min_prompt_chunks, len(chunks)) or len(selected) == len(chunks):
        omitted_ids = {chunk.get("chunk_id") for chunk in selected}
        omitted = [_mark_chunk(chunk, "omitted") for chunk in chunks if chunk.get("chunk_id") not in omitted_ids]
        return selected, omitted, warnings

    target_count = min(max(min_prompt_chunks, 0), len(chunks))
    if target_count <= 0:
        omitted_ids = {chunk.get("chunk_id") for chunk in selected}
        omitted = [_mark_chunk(chunk, "omitted") for chunk in chunks if chunk.get("chunk_id") not in omitted_ids]
        return selected, omitted, warnings

    trimmed = [_trim_chunk(chunk, question, max(40, source_budget // target_count), model) for chunk in chunks[:target_count]]
    while trimmed and estimate_text_tokens(format_context(trimmed), model) > source_budget:
        largest = max(range(len(trimmed)), key=lambda index: estimate_text_tokens(trimmed[index].get("text", ""), model))
        text_budget = max(24, math.floor(estimate_text_tokens(trimmed[largest].get("text", ""), model) * 0.72))
        if text_budget >= estimate_text_tokens(trimmed[largest].get("text", ""), model):
            break
        trimmed[largest] = _trim_chunk(trimmed[largest], question, text_budget, model)

    while trimmed and estimate_text_tokens(format_context(trimmed), model) > source_budget:
        trimmed.pop()
        target_count -= 1

    used_ids = {chunk.get("chunk_id") for chunk in trimmed}
    omitted = [_mark_chunk(chunk, "omitted") for chunk in original_chunks if chunk.get("chunk_id") not in used_ids]
    if len(trimmed) < min(min_prompt_chunks, len(original_chunks)):
        warnings.append("The source budget was too small to include the requested minimum number of chunks.")
    return trimmed, omitted, warnings


def _trim_chunk(chunk: dict[str, Any], question: str, text_budget: int, model: str) -> dict[str, Any]:
    original_text = str(chunk.get("text") or "")
    trimmed_text = _sentence_window(original_text, question, text_budget, model)
    if not trimmed_text or trimmed_text == original_text:
        return _mark_chunk(chunk, "used")
    marked = _mark_chunk(chunk, "trimmed")
    metadata = dict(marked.get("metadata") or {})
    metadata["original_text"] = original_text
    metadata["budget_status"] = "trimmed"
    metadata["budget_note"] = "Only this excerpt was sent to the model."
    marked["metadata"] = metadata
    marked["text"] = trimmed_text
    return marked


def _sentence_window(text: str, question: str, budget: int, model: str) -> str:
    if estimate_text_tokens(text, model) <= budget:
        return text
    sentences = _split_sentences(text)
    if not sentences:
        return _trim_to_budget(text, budget, model)
    terms = _query_terms(question)
    best_index = 0
    if terms:
        best_score = -1
        for index, sentence in enumerate(sentences):
            normalized = sentence.casefold()
            score = sum(1 for term in terms if term in normalized)
            if score > best_score:
                best_score = score
                best_index = index
    selected = [sentences[best_index]]
    left = best_index - 1
    right = best_index + 1
    while True:
        candidates: list[tuple[str, int]] = []
        if left >= 0:
            candidates.append(("left", left))
        if right < len(sentences):
            candidates.append(("right", right))
        added = False
        for side, index in candidates:
            candidate_sentences = [*selected]
            if side == "left":
                candidate_sentences.insert(0, sentences[index])
            else:
                candidate_sentences.append(sentences[index])
            candidate = " ".join(candidate_sentences)
            if estimate_text_tokens(candidate, model) <= budget:
                selected = candidate_sentences
                if side == "left":
                    left -= 1
                else:
                    right += 1
                added = True
                break
        if not added:
            break
    result = " ".join(selected).strip()
    if estimate_text_tokens(result, model) > budget:
        return _trim_to_budget(result, budget, model)
    return result


def _trim_to_budget(text: str, budget: int, model: str) -> str:
    words = text.split()
    if not words:
        return ""
    low = 1
    high = len(words)
    best = words[0]
    while low <= high:
        mid = (low + high) // 2
        candidate = " ".join(words[:mid]).rstrip(" ,;:")
        if mid < len(words):
            candidate = f"{candidate}..."
        if estimate_text_tokens(candidate, model) <= budget:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best


def _mark_chunk(chunk: dict[str, Any], status: str) -> dict[str, Any]:
    marked = dict(chunk)
    metadata = dict(marked.get("metadata") or {})
    metadata["budget_status"] = status
    marked["metadata"] = metadata
    return marked


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _query_terms(question: str) -> list[str]:
    stopwords = {
        "aby",
        "ale",
        "byl",
        "byla",
        "byli",
        "bylo",
        "co",
        "do",
        "jak",
        "jako",
        "je",
        "jsou",
        "kde",
        "kdo",
        "když",
        "má",
        "mezi",
        "nebo",
        "pod",
        "pro",
        "před",
        "při",
        "se",
        "tak",
        "to",
        "tom",
        "už",
        "vedle",
        "ze",
    }
    tokens = re.findall(r"[\wá-žÁ-Ž]+", question.casefold())
    return [token for token in dict.fromkeys(tokens) if len(token) >= 4 and token not in stopwords]


def _encoding_for_model(model: str | None):
    if tiktoken is None:
        return None
    normalized = (model or "").strip().lower()
    for prefix in ("openai/", "azure/"):
        normalized = normalized.removeprefix(prefix)
    try:
        return tiktoken.encoding_for_model(normalized or "gpt-4o-mini")
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None
