export function tokenBudgetView(tokenBudget, { foldedMessages = 0, conversationSummary = "" } = {}) {
  if (!tokenBudget) {
    return null;
  }

  const contextWindow = nullableNumber(tokenBudget.context_window_tokens);
  const reservedOutput = nullableNumber(tokenBudget.reserved_output_tokens);
  const usableInput = nullableNumber(tokenBudget.usable_input_tokens);
  const nonSourceTokens = nullableNumber(tokenBudget.estimated_non_source_tokens);
  const retrievedSourceTokens = nullableNumber(tokenBudget.estimated_retrieved_source_tokens);
  const sourceTokens = nullableNumber(tokenBudget.estimated_source_tokens);
  const historyTokens = nullableNumber(tokenBudget.estimated_conversation_history_tokens);
  const historyMessages = Number(tokenBudget.conversation_history_message_count || 0);
  const usedHistoryMessages = Number(tokenBudget.conversation_history_used_message_count || 0);
  const omittedHistoryMessages = Number(tokenBudget.conversation_history_omitted_message_count || 0);
  const effectiveCompactionTrigger = nullableNumber(tokenBudget.effective_conversation_trigger_tokens);
  const compactionMessageTrigger = Number(tokenBudget.conversation_summary_trigger_messages || 16);
  const totalInput =
    nullableNumber(tokenBudget.estimated_total_input_tokens) ??
    (nonSourceTokens !== null && sourceTokens !== null ? nonSourceTokens + sourceTokens : null);
  const safetyMargin =
    nullableNumber(tokenBudget.safety_margin_tokens) ??
    (contextWindow !== null && reservedOutput !== null && usableInput !== null
      ? Math.max(0, contextWindow - reservedOutput - usableInput)
      : null);
  const safetyMarginRatio = nullableNumber(tokenBudget.safety_margin_ratio);
  const inputUsagePercent =
    usableInput && totalInput !== null ? Math.round((totalInput / usableInput) * 100) : null;
  const windowUsagePercent =
    contextWindow && totalInput !== null
      ? Math.max(0, Math.min(100, Math.round(((totalInput + (reservedOutput || 0)) / contextWindow) * 100)))
      : null;

  return {
    contextWindow,
    reservedOutput,
    usableInput,
    nonSourceTokens,
    retrievedSourceTokens,
    sourceTokens,
    historyTokens,
    historyMessages,
    usedHistoryMessages,
    omittedHistoryMessages,
    effectiveCompactionTrigger,
    compactionMessageTrigger,
    totalInput,
    safetyMargin,
    safetyMarginPercent:
      safetyMarginRatio !== null && safetyMarginRatio > 0 ? Math.round(safetyMarginRatio * 100) : null,
    inputUsagePercent,
    windowUsagePercent,
    usedChunks: Number(tokenBudget.used_chunk_count || 0),
    trimmedChunks: Number(tokenBudget.trimmed_chunk_count || 0),
    omittedChunks: Number(tokenBudget.omitted_chunk_count || 0),
    summaryUsed: Boolean(tokenBudget.conversation_summary_used || conversationSummary),
    conversationSummary: String(conversationSummary || ""),
    foldedMessages: Math.max(0, Number(foldedMessages) || 0),
  };
}

export function conversationQueryRewriteView(message) {
  const rewritten = message?.retrieval_query_was_rewritten === true;
  const attempted = message?.retrieval_query_rewrite_attempted === true;
  const enabled = message?.settings?.rewrite_query_for_retrieval === true;
  const skipReason = String(message?.retrieval_query_rewrite_skip_reason || "");
  const skipMessages = {
    no_conversation_history: "Vyhledávací dotaz nebyl upraven, protože jde o první zprávu konverzace.",
    question_too_long: "Vyhledávací dotaz nebyl upraven, protože zpráva je příliš dlouhá; pro vyhledávání byl použit původní text.",
    empty_question: "Vyhledávací dotaz nebyl upraven, protože zpráva neobsahovala žádný text.",
  };

  return {
    showQueries: attempted || rewritten,
    rewritten,
    attempted,
    unchangedMessage:
      attempted && !rewritten ? "Úprava dotazu proběhla, ale výsledný dotaz zůstal stejný." : "",
    skippedMessage: !attempted && !rewritten && enabled ? (skipMessages[skipReason] || "") : "",
  };
}

export function requestStatusMessage(phase) {
  if (phase === "thinking") {
    return "Přemýšlím…";
  }
  if (phase === "query_rewrite") {
    return "Připravuji vyhledávací dotaz…";
  }
  if (phase === "retrieval") {
    return "Vyhledávám zdroje…";
  }
  if (phase === "conversation_compaction") {
    return "Komprimuji starší část konverzace…";
  }
  return "";
}

export function formatRequestErrorDetail(detail, fallback = "Request failed") {
  if (!detail || typeof detail === "string") {
    return detail || fallback;
  }
  if (
    detail.estimated_non_source_tokens !== undefined &&
    detail.usable_input_tokens !== undefined &&
    detail.over_by_tokens !== undefined
  ) {
    return (
      `Dotaz se nevejde do kontextu: prompt má přibližně ${formatInteger(detail.estimated_non_source_tokens)} tokenů, ` +
      `limit je ${formatInteger(detail.usable_input_tokens)} (o ${formatInteger(detail.over_by_tokens)} více). ` +
      "Zkrať dotaz nebo instrukce, případně zvol větší kontextové okno."
    );
  }
  if (detail.message) {
    return String(detail.message);
  }
  return JSON.stringify(detail);
}

export function isTokenBudgetErrorDetail(detail) {
  return Boolean(
    detail &&
      typeof detail === "object" &&
      detail.estimated_non_source_tokens !== undefined &&
      detail.usable_input_tokens !== undefined &&
      detail.over_by_tokens !== undefined,
  );
}

export function rollbackRejectedTurn(messages, requestTurnId) {
  if (!requestTurnId) {
    return Array.isArray(messages) ? [...messages] : [];
  }
  return (Array.isArray(messages) ? messages : []).filter(
    (message) => message?.request_turn_id !== requestTurnId,
  );
}

export function removeLegacyTokenBudgetRejectedTurns(messages) {
  const cleaned = [];
  for (const message of Array.isArray(messages) ? messages : []) {
    if (isLegacyTokenBudgetErrorMessage(message)) {
      if (cleaned[cleaned.length - 1]?.role === "user") {
        cleaned.pop();
      }
      continue;
    }
    cleaned.push(message);
  }
  return cleaned;
}

function isLegacyTokenBudgetErrorMessage(message) {
  if (message?.role !== "assistant") {
    return false;
  }
  const content = String(message.content || "");
  return (
    content.startsWith("Nepodařilo se dokončit odpověď:") &&
    (content.includes("Dotaz se nevejde do kontextu:") ||
      content.includes("Prompt is too long before any retrieved sources can be added."))
  );
}

function formatInteger(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return String(value);
  }
  return String(Math.round(number)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function nullableNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
