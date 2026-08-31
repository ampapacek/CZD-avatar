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
