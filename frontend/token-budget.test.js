import { describe, expect, it } from "vitest";

import {
  conversationQueryRewriteView,
  formatRequestErrorDetail,
  isTokenBudgetErrorDetail,
  removeLegacyTokenBudgetRejectedTurns,
  requestStatusMessage,
  rollbackRejectedTurn,
  tokenBudgetView,
} from "./token-budget.js";

describe("token budget presentation", () => {
  it("keeps conversation history as a subset of the non-source prompt", () => {
    const view = tokenBudgetView(
      {
        context_window_tokens: 40000,
        reserved_output_tokens: 1000,
        usable_input_tokens: 35000,
        estimated_non_source_tokens: 8000,
        estimated_conversation_history_tokens: 3000,
        estimated_retrieved_source_tokens: 3500,
        estimated_source_tokens: 2000,
        safety_margin_tokens: 4000,
        safety_margin_ratio: 0.1,
      },
      { foldedMessages: 6, conversationSummary: "Earlier turns" },
    );

    expect(view.totalInput).toBe(10000);
    expect(view.nonSourceTokens).toBe(8000);
    expect(view.retrievedSourceTokens).toBe(3500);
    expect(view.historyTokens).toBe(3000);
    expect(view.inputUsagePercent).toBe(29);
    expect(view.summaryUsed).toBe(true);
    expect(view.foldedMessages).toBe(6);
  });

  it("shows a reason instead of duplicate queries when rewrite was skipped", () => {
    const view = conversationQueryRewriteView({
      retrieval_query_was_rewritten: false,
      retrieval_query_rewrite_attempted: false,
      retrieval_query_rewrite_skip_reason: "no_conversation_history",
      settings: { rewrite_query_for_retrieval: true },
    });

    expect(view.showQueries).toBe(false);
    expect(view.skippedMessage).toContain("první zprávu konverzace");
  });

  it("shows both queries when rewrite ran but kept the text unchanged", () => {
    const view = conversationQueryRewriteView({
      retrieval_query_was_rewritten: false,
      retrieval_query_rewrite_attempted: true,
      settings: { rewrite_query_for_retrieval: true },
    });

    expect(view.showQueries).toBe(true);
    expect(view.unchangedMessage).toContain("zůstal stejný");
    expect(view.skippedMessage).toBe("");
  });

  it("recovers totals and safety margin for older stored entries", () => {
    const view = tokenBudgetView({
      context_window_tokens: 10000,
      reserved_output_tokens: 1000,
      usable_input_tokens: 8000,
      estimated_non_source_tokens: 2000,
      estimated_source_tokens: 500,
    });

    expect(view.totalInput).toBe(2500);
    expect(view.safetyMargin).toBe(1000);
  });

  it("maps the streamed preparation phase to visible Czech copy", () => {
    expect(requestStatusMessage("query_rewrite")).toBe("Připravuji vyhledávací dotaz…");
    expect(requestStatusMessage("retrieval")).toBe("Vyhledávám zdroje…");
    expect(requestStatusMessage("unknown")).toBe("");
  });

  it("formats a structured token-budget rejection for the conversation UI", () => {
    const detail = {
      estimated_non_source_tokens: 38742,
      usable_input_tokens: 35308,
      over_by_tokens: 3434,
      message: "English backend detail",
    };
    expect(formatRequestErrorDetail(detail)).toBe(
      "Dotaz se nevejde do kontextu: prompt má přibližně 38 742 tokenů, limit je 35 308 (o 3 434 více). " +
        "Zkrať dotaz nebo instrukce, případně zvol větší kontextové okno.",
    );
    expect(isTokenBudgetErrorDetail(detail)).toBe(true);
    expect(isTokenBudgetErrorDetail({ message: "Network failed" })).toBe(false);
  });

  it("removes only the rejected request from conversation history", () => {
    const messages = [
      { role: "user", content: "successful question" },
      { role: "assistant", content: "successful answer" },
      { role: "user", content: "oversized prompt", request_turn_id: "turn-2" },
      { role: "assistant", content: "partial", request_turn_id: "turn-2" },
    ];

    expect(rollbackRejectedTurn(messages, "turn-2")).toEqual(messages.slice(0, 2));
    expect(rollbackRejectedTurn(messages, "unknown")).toEqual(messages);
  });

  it("cleans a token-budget failure saved before request turn IDs existed", () => {
    const successful = [
      { role: "user", content: "successful question" },
      { role: "assistant", content: "successful answer" },
    ];
    const messages = [
      ...successful,
      { role: "user", content: "oversized legacy prompt" },
      {
        role: "assistant",
        content:
          "Nepodařilo se dokončit odpověď: Dotaz se nevejde do kontextu: prompt má přibližně 38 742 tokenů.",
      },
    ];

    expect(removeLegacyTokenBudgetRejectedTurns(messages)).toEqual(successful);
  });
});
