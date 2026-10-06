// Turning a finished single-turn answer into the first turn of a conversation.
//
// The two modes store the same things under different names: a conversation
// keeps its own settings snapshot (`captureSettingsSnapshot` shape) plus a list
// of messages, while an assistant message carries the sanitized request payload
// it was answered with. This module builds both from the answer that is on
// screen, so the thread continues under the settings that produced it rather
// than under whatever the controls happen to say now.

/**
 * The seeded conversation, or `null` when there is nothing to continue.
 *
 * A turn without a question, without an answer, or without the settings that
 * produced it cannot be continued honestly — a retrieve-only run and a stream
 * still in flight both land here — so no empty thread is created for it.
 *
 * `settings` is the conversation-level snapshot; `requestSettings` is the
 * sanitized payload the answer was produced with, which is what the turn detail
 * and the history-style renderers read.
 */
export function conversationFromSingleTurn(turn, { id, now } = {}) {
  const question = String(turn?.question || "").trim();
  const answer = String(turn?.answer || "").trim();
  if (!question || !answer || !turn?.settings) {
    return null;
  }

  const timestamp = now || new Date().toISOString();
  const retrieval = turn.retrievalInfo || {};
  return {
    id: id ?? Date.now(),
    // The caller shortens the title the same way a conversation's own first
    // turn does, so a continued thread is named like any other.
    title: String(turn.title || question),
    createdAt: timestamp,
    updatedAt: timestamp,
    // Nothing has been folded yet: the seeded turn is the whole history.
    conversation_summary: "",
    conversation_compacted_through: 0,
    rewrite_query_for_retrieval: true,
    settings: turn.settings,
    messages: [
      {
        role: "user",
        content: question,
        createdAt: timestamp,
      },
      {
        role: "assistant",
        question,
        original_question: retrieval.original_question || question,
        retrieval_query: retrieval.retrieval_query || question,
        retrieval_query_was_rewritten: retrieval.retrieval_query_was_rewritten === true,
        retrieval_query_rewrite_attempted: retrieval.retrieval_query_rewrite_attempted === true,
        retrieval_query_rewrite_skip_reason: retrieval.retrieval_query_rewrite_skip_reason ?? null,
        content: answer,
        settings: turn.requestSettings || {},
        sources: turn.sources || [],
        retrieved_chunks: turn.retrievedChunks || [],
        omitted_chunks: turn.omittedChunks || [],
        token_budget: turn.tokenBudget || null,
        chunk_budget_warnings: turn.chunkBudgetWarnings || [],
        reasoning: turn.reasoning || "",
        reasoning_streaming: false,
        conversation_compacted_through: 0,
        model_used: turn.modelUsed || null,
        upstream_model: turn.upstreamModel || null,
        response_time_seconds: turn.responseTimeSeconds ?? null,
        createdAt: timestamp,
      },
    ],
  };
}

// The conversation settings snapshot keys a stored answer's request payload can
// fill in. The payload names them the same way; everything else it carries
// (budgets, retrieval backend, keys) is request-only.
const SNAPSHOT_KEYS_FROM_REQUEST = [
  "wp_id",
  "prompt_preset_id",
  "prompt_preset_name",
  "prompt_preset_note",
  "system_prompt",
  "user_prompt_template",
  "selections",
  "placeholder_defs",
  "llm_provider",
  "model",
  "msearch_collection",
  "context_window_tokens",
  "reasoning_effort",
  "top_k",
  "msearch_rescore",
  "msearch_min_confidence",
  "min_relative_score",
];

/**
 * The single-turn shape `conversationFromSingleTurn` takes, built from a stored
 * history entry or shared item, or `null` for a retrieve-only entry or one
 * without an answer.
 *
 * History keeps the request payload rather than a settings snapshot, so the
 * snapshot starts from `baseSettings` (the current main-page snapshot) and the
 * entry overrides every key it recorded: an older entry missing a field gets
 * today's value for it instead of nothing.
 *
 * Sources come back without their snippet text, which costs the thread
 * nothing: earlier turns reach the model as question and answer only.
 */
export function continuationFromHistoryEntry(entry, { baseSettings = {}, title } = {}) {
  if (!entry || entry.mode === "retrieve" || !String(entry.answer || "").trim()) {
    return null;
  }
  const request = entry.settings || {};
  const settings = { ...baseSettings };
  for (const key of SNAPSHOT_KEYS_FROM_REQUEST) {
    if (Object.prototype.hasOwnProperty.call(request, key) && request[key] !== undefined) {
      settings[key] = request[key];
    }
  }
  // The payload sends "no choice" as null; the snapshot keeps the select value.
  if (settings.reasoning_effort === null) {
    settings.reasoning_effort = "";
  }
  const question = entry.question || "";
  return {
    title: title || question,
    question,
    answer: entry.answer,
    settings,
    requestSettings: request,
    retrievalInfo: {
      original_question: entry.original_question || question,
      retrieval_query: entry.retrieval_query || request.retrieval_query || question,
    },
    sources: entry.sources || [],
    retrievedChunks: entry.retrieved_chunks || [],
    omittedChunks: entry.omitted_chunks || [],
    tokenBudget: entry.token_budget || null,
    chunkBudgetWarnings: entry.chunk_budget_warnings || [],
    reasoning: entry.reasoning || "",
    modelUsed: entry.model_used || request.model || null,
    upstreamModel: entry.upstream_model || null,
    responseTimeSeconds: entry.response_time_seconds ?? null,
  };
}
