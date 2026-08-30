from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings
from app.rag.prompts import PlaceholderDef, build_messages, format_context

try:
    import tiktoken
except Exception:  # pragma: no cover - exercised only when dependency is unavailable
    tiktoken = None


DEFAULT_CONVERSATION_RECENT_MESSAGES = 6
DEFAULT_CONVERSATION_SUMMARY_TRIGGER_MESSAGES = 16


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
    # Defaults so callers that build a config by hand (tests, scripts) do not
    # have to know about compaction; `from_settings` always fills them in.
    conversation_recent_messages: int = DEFAULT_CONVERSATION_RECENT_MESSAGES
    conversation_summary_trigger_messages: int = DEFAULT_CONVERSATION_SUMMARY_TRIGGER_MESSAGES

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
        conversation_recent_messages: int | None = None,
        conversation_summary_trigger_messages: int | None = None,
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
            conversation_recent_messages=(
                conversation_recent_messages or settings.conversation_recent_messages
            ),
            conversation_summary_trigger_messages=(
                conversation_summary_trigger_messages or settings.conversation_summary_trigger_messages
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

    def effective_conversation_trigger_tokens(self, length: str) -> int:
        adaptive = 250 + math.floor(self.usable_input_tokens(length) * 0.25)
        return min(self.conversation_summary_trigger_tokens, adaptive)

    def conversation_summary_target_tokens(self, length: str) -> int:
        return min(768, max(256, self.effective_conversation_trigger_tokens(length) // 8))


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
    estimated_retrieved_source_tokens: int = 0
    estimated_source_tokens: int = 0
    estimated_conversation_history_tokens: int = 0
    conversation_history_message_count: int = 0
    conversation_history_used_message_count: int = 0
    conversation_history_omitted_message_count: int = 0
    effective_conversation_trigger_tokens: int = 0
    conversation_summary_trigger_messages: int = DEFAULT_CONVERSATION_SUMMARY_TRIGGER_MESSAGES
    estimated_total_input_tokens: int = 0
    trimmed_chunk_count: int = 0
    conversation_summary_used: bool = False
    safety_margin_ratio: float = 0.0

    @property
    def safety_margin_tokens(self) -> int:
        """The safety margin as the residual of the subtraction the UI shows.

        Derived from the three numbers already reported rather than from
        `token_budget_safety_margin`, so the displayed column adds up by
        construction even if the flooring or the formula changes.
        """

        return max(0, self.context_window_tokens - self.reserved_output_tokens - self.usable_input_tokens)

    def metadata(self) -> dict[str, object]:
        return {
            "context_window_tokens": self.context_window_tokens,
            "usable_input_tokens": self.usable_input_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "safety_margin_tokens": self.safety_margin_tokens,
            "safety_margin_ratio": self.safety_margin_ratio,
            "estimated_non_source_tokens": self.estimated_non_source_tokens,
            "estimated_retrieved_source_tokens": self.estimated_retrieved_source_tokens,
            "estimated_source_tokens": self.estimated_source_tokens,
            "estimated_conversation_history_tokens": self.estimated_conversation_history_tokens,
            "conversation_history_message_count": self.conversation_history_message_count,
            "conversation_history_used_message_count": self.conversation_history_used_message_count,
            "conversation_history_omitted_message_count": self.conversation_history_omitted_message_count,
            "effective_conversation_trigger_tokens": self.effective_conversation_trigger_tokens,
            "conversation_summary_trigger_messages": self.conversation_summary_trigger_messages,
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


def truncate_text_to_token_limit(text: str, limit: int, model: str | None = None) -> str:
    """Return a readable prefix whose estimated size does not exceed ``limit``."""

    clean = text.strip()
    if not clean or limit <= 0:
        return ""
    if estimate_text_tokens(clean, model) <= limit:
        return clean

    suffix = "…"
    low, high = 0, len(clean)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = clean[:middle].rstrip() + suffix
        if estimate_text_tokens(candidate, model) <= limit:
            low = middle
        else:
            high = middle - 1

    candidate = clean[:low].rstrip()
    # Prefer a nearby paragraph or sentence boundary so the enforced cap does
    # not normally leave the summary halfway through a statement.
    boundaries = [
        candidate.rfind("\n\n"),
        candidate.rfind(". "),
        candidate.rfind("! "),
        candidate.rfind("? "),
        candidate.rfind("; "),
    ]
    boundary = max(boundaries)
    if boundary >= math.floor(len(candidate) * 0.6):
        candidate = candidate[: boundary + 1].rstrip()
    result = candidate + suffix
    while result and estimate_text_tokens(result, model) > limit:
        candidate = candidate[:-1].rstrip()
        result = candidate + suffix
    return result


def _clean_history_messages(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    return [
        {"role": turn.get("role", ""), "content": (turn.get("content") or "").strip()}
        for turn in (history or [])
        if turn.get("role") in {"user", "assistant"} and (turn.get("content") or "").strip()
    ]


def _last_complete_turn(history: list[dict[str, str]]) -> list[dict[str, str]]:
    if len(history) >= 2 and history[-2]["role"] == "user" and history[-1]["role"] == "assistant":
        return history[-2:]
    return history[-1:]


def _history_turns_newest_first(history: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Return chronological message blocks ordered from newest to oldest."""

    turns: list[list[dict[str, str]]] = []
    cursor = len(history)
    while cursor:
        if (
            cursor >= 2
            and history[cursor - 2]["role"] == "user"
            and history[cursor - 1]["role"] == "assistant"
        ):
            start = cursor - 2
        else:
            start = cursor - 1
        turns.append(history[start:cursor])
        cursor = start
    return turns


def prepare_prompt_budget(
    *,
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    length: str,
    model: str,
    config: PromptBudgetConfig,
    placeholder_defs: dict[str, "PlaceholderDef"] | None = None,
    selections: dict[str, str] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    conversation_summary: str | None = None,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
) -> PromptBudgetResult:
    usable_input = config.usable_input_tokens(length)
    reserved_output = config.output_budget_for_length(length)
    clean_history = _clean_history_messages(conversation_history)
    last_turn = _last_complete_turn(clean_history)

    def prompt_messages(
        chunks: list[dict[str, Any]],
        history: list[dict[str, str]],
        *,
        summary: str | None = conversation_summary,
    ) -> list[dict[str, str]]:
        return build_messages(
            question,
            chunks,
            placeholder_defs,
            selections,
            conversation_history=history,
            conversation_summary=summary,
            history_limit=len(history),
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            context_text=format_context(chunks),
        )

    # The summary and immediately preceding complete turn are required context.
    # Older raw turns and non-minimum chunks compete for the remaining space in
    # the explicit order documented below.
    required_non_source_messages = prompt_messages([], last_turn)
    required_non_source_tokens = estimate_messages_tokens(required_non_source_messages, model)
    if required_non_source_tokens > usable_input:
        over_by = required_non_source_tokens - usable_input
        raise PromptBudgetError(
            (
                "Prompt is too long before any retrieved sources can be added. "
                f"Configured context window: {config.context_window_tokens} tokens. "
                f"Reserved answer budget: {reserved_output} tokens. "
                f"Usable input budget after safety margin: {usable_input} tokens. "
                f"Current prompt without sources: about {required_non_source_tokens} tokens, "
                f"which is {over_by} tokens over the limit. "
                "Shorten the system prompt, custom instructions, conversation, or question; "
                "choose a larger-context model; or increase the context window setting."
            ),
            context_window_tokens=config.context_window_tokens,
            usable_input_tokens=usable_input,
            reserved_output_tokens=reserved_output,
            estimated_non_source_tokens=required_non_source_tokens,
            over_by_tokens=over_by,
        )

    # Packing priority:
    #   1. configured minimum chunks (trimmed when needed),
    #   2. summary + last complete turn (already reserved above),
    #   3. every additional chunk except the final lowest-ranked one,
    #   4. older complete conversation turns, newest first,
    #   5. the final lowest-ranked chunk.
    required_count = min(max(config.min_prompt_chunks, 0), len(retrieved_chunks))
    source_budget = max(0, usable_input - required_non_source_tokens)
    required_chunks, _, warnings = _fit_chunks(
        question=question,
        chunks=retrieved_chunks[:required_count],
        source_budget=source_budget,
        min_prompt_chunks=required_count,
        model=model,
    )
    used_chunks = list(required_chunks)
    selected_history = list(last_turn)

    deferred_last_index = len(retrieved_chunks) - 1 if len(retrieved_chunks) > required_count else None
    additional_end = deferred_last_index if deferred_last_index is not None else len(retrieved_chunks)
    for chunk in retrieved_chunks[required_count:additional_end]:
        candidate = [*used_chunks, _mark_chunk(chunk, "used")]
        if estimate_messages_tokens(prompt_messages(candidate, selected_history), model) > usable_input:
            break
        used_chunks = candidate

    older_history = clean_history[: len(clean_history) - len(last_turn)] if last_turn else clean_history
    for turn in _history_turns_newest_first(older_history):
        candidate_history = [*turn, *selected_history]
        if estimate_messages_tokens(prompt_messages(used_chunks, candidate_history), model) > usable_input:
            break
        selected_history = candidate_history

    if deferred_last_index is not None:
        last_chunk = _mark_chunk(retrieved_chunks[deferred_last_index], "used")
        candidate = [*used_chunks, last_chunk]
        if estimate_messages_tokens(prompt_messages(candidate, selected_history), model) <= usable_input:
            used_chunks = candidate

    messages = prompt_messages(used_chunks, selected_history)
    non_source_messages = prompt_messages([], selected_history)
    non_source_tokens = estimate_messages_tokens(non_source_messages, model)
    all_source_messages = prompt_messages(retrieved_chunks, selected_history)
    retrieved_source_tokens = max(0, estimate_messages_tokens(all_source_messages, model) - non_source_tokens)
    source_tokens = max(0, estimate_messages_tokens(messages, model) - non_source_tokens)
    total_input_tokens = non_source_tokens + source_tokens
    history_tokens = conversation_history_tokens(selected_history, model)
    used_ids = {chunk.get("chunk_id") for chunk in used_chunks}
    omitted_chunks = [
        _mark_chunk(chunk, "omitted")
        for chunk in retrieved_chunks
        if chunk.get("chunk_id") not in used_ids
    ]
    trimmed_count = sum(1 for chunk in used_chunks if chunk.get("metadata", {}).get("budget_status") == "trimmed")
    if omitted_chunks:
        warnings.append(f"Kvůli limitu kontextu nebylo modelu posláno {len(omitted_chunks)} nalezených chunků.")
    if trimmed_count:
        warnings.append(f"Před odesláním modelu bylo zkráceno {trimmed_count} chunků.")
    if retrieved_chunks and not used_chunks:
        warnings.append("Do zbývajícího kontextového limitu se nevešel žádný nalezený chunk; model odpověděl bez zdrojů.")
    omitted_history_count = len(clean_history) - len(selected_history)
    if omitted_history_count:
        warnings.append(
            f"Kvůli limitu kontextu nebylo modelu posláno {omitted_history_count} starších zpráv konverzace."
        )
    return PromptBudgetResult(
        messages=messages,
        used_chunks=used_chunks,
        omitted_chunks=omitted_chunks,
        warnings=warnings,
        context_window_tokens=config.context_window_tokens,
        usable_input_tokens=usable_input,
        reserved_output_tokens=reserved_output,
        estimated_non_source_tokens=non_source_tokens,
        estimated_retrieved_source_tokens=retrieved_source_tokens,
        estimated_source_tokens=source_tokens,
        estimated_conversation_history_tokens=history_tokens,
        conversation_history_message_count=len(clean_history),
        conversation_history_used_message_count=len(selected_history),
        conversation_history_omitted_message_count=omitted_history_count,
        effective_conversation_trigger_tokens=config.effective_conversation_trigger_tokens(length),
        conversation_summary_trigger_messages=config.conversation_summary_trigger_messages,
        estimated_total_input_tokens=total_input_tokens,
        trimmed_chunk_count=trimmed_count,
        safety_margin_ratio=config.token_budget_safety_margin,
    )


def conversation_history_tokens(history: list[dict[str, str]] | None, model: str | None = None) -> int:
    messages = [
        {"role": turn.get("role", ""), "content": (turn.get("content") or "").strip()}
        for turn in (history or [])
        if turn.get("role") in {"user", "assistant"} and (turn.get("content") or "").strip()
    ]
    return estimate_messages_tokens(messages, model) if messages else 0
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
