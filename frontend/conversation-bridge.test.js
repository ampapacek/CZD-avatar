import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import { conversationFromSingleTurn } from "./conversation-bridge.js";

const settings = { settings_version: 2, wp_id: "WP1-historie", model: "gpt-oss-120b" };

function turn(overrides = {}) {
  return {
    title: "Kdo byl Jan Hus?",
    question: "Kdo byl Jan Hus?",
    answer: "Jan Hus byl český kazatel [Z1].",
    settings,
    requestSettings: { top_k: 8, llm_base_url: "https://example.test/v1" },
    sources: [{ citation_id: "Z1", title: "Hus.pdf" }],
    retrievedChunks: [{ chunk_id: "msearch:1", text: "…" }],
    modelUsed: "gpt-oss-120b",
    responseTimeSeconds: 4.2,
    ...overrides,
  };
}

describe("conversationFromSingleTurn", () => {
  it("seeds a thread with the question and the answer as one complete turn", () => {
    const conversation = conversationFromSingleTurn(turn(), { id: 7, now: "2026-08-31T10:00:00.000Z" });

    expect(conversation.id).toBe(7);
    expect(conversation.title).toBe("Kdo byl Jan Hus?");
    expect(conversation.createdAt).toBe("2026-08-31T10:00:00.000Z");
    expect(conversation.updatedAt).toBe("2026-08-31T10:00:00.000Z");
    expect(conversation.messages.map((message) => message.role)).toEqual(["user", "assistant"]);
    expect(conversation.messages[0].content).toBe("Kdo byl Jan Hus?");
    expect(conversation.messages[1].content).toBe("Jan Hus byl český kazatel [Z1].");
    expect(conversation.messages[1].sources).toEqual([{ citation_id: "Z1", title: "Hus.pdf" }]);
    expect(conversation.messages[1].retrieved_chunks).toHaveLength(1);
  });

  it("carries the settings the answer was produced with, at both levels", () => {
    // The thread inherits the snapshot that was active for that question, and
    // the turn keeps the request payload the detail panel renders.
    const conversation = conversationFromSingleTurn(turn());

    expect(conversation.settings).toBe(settings);
    expect(conversation.messages[1].settings).toEqual({
      top_k: 8,
      llm_base_url: "https://example.test/v1",
    });
  });

  it("starts with nothing folded and the rewrite enabled", () => {
    const conversation = conversationFromSingleTurn(turn());

    expect(conversation.conversation_summary).toBe("");
    expect(conversation.conversation_compacted_through).toBe(0);
    expect(conversation.messages[1].conversation_compacted_through).toBe(0);
    expect(conversation.rewrite_query_for_retrieval).toBe(true);
    expect(conversation.messages[1].reasoning_streaming).toBe(false);
  });

  it("keeps the retrieval query the answer actually used", () => {
    const conversation = conversationFromSingleTurn(
      turn({
        retrievalInfo: {
          original_question: "kdo hus",
          retrieval_query: "Jan Hus kazatel",
          retrieval_query_was_rewritten: true,
        },
      }),
    );

    const assistant = conversation.messages[1];
    expect(assistant.original_question).toBe("kdo hus");
    expect(assistant.retrieval_query).toBe("Jan Hus kazatel");
    expect(assistant.retrieval_query_was_rewritten).toBe(true);
    expect(assistant.retrieval_query_rewrite_skip_reason).toBeNull();
  });

  it("falls back to the question when no retrieval info was reported", () => {
    const assistant = conversationFromSingleTurn(turn()).messages[1];

    expect(assistant.original_question).toBe("Kdo byl Jan Hus?");
    expect(assistant.retrieval_query).toBe("Kdo byl Jan Hus?");
    expect(assistant.retrieval_query_was_rewritten).toBe(false);
  });

  it("refuses to seed a thread there is nothing to continue from", () => {
    // A retrieve-only run has no answer, a cancelled stream has no answer yet,
    // and without the settings that produced it the thread would silently
    // continue under different ones.
    expect(conversationFromSingleTurn(turn({ answer: "" }))).toBeNull();
    expect(conversationFromSingleTurn(turn({ answer: "   " }))).toBeNull();
    expect(conversationFromSingleTurn(turn({ question: "" }))).toBeNull();
    expect(conversationFromSingleTurn(turn({ settings: null }))).toBeNull();
    expect(conversationFromSingleTurn(null)).toBeNull();
  });
});

describe("continue-in-conversation wiring", () => {
  const appSource = readFileSync("app/static/app.js", "utf8");

  it("offers the action beside the other answer actions, hidden until there is one", () => {
    const document = new JSDOM(readFileSync("app/static/index.html", "utf8")).window.document;
    const button = document.querySelector("#continueInConversationButton");

    expect(button).not.toBeNull();
    expect(document.querySelector("#answerActions").contains(button)).toBe(true);
    expect(button.hasAttribute("hidden")).toBe(true);
    expect(button.textContent.trim()).toBe("Pokračovat v konverzaci");
  });

  it("shows it only while a finished live answer is captured", () => {
    // The copy buttons work mid-stream; this one must not, and a restored
    // history entry is not a live answer either.
    const updateBody = appSource.slice(
      appSource.indexOf("function updateAnswerActions()"),
      appSource.indexOf("function renderAnswer(text)"),
    );
    expect(updateBody).toContain("continueInConversationButton.hidden = currentAnswerContinuation === null");

    const runQueryBody = appSource.slice(
      appSource.indexOf("async function runQuery(retrieveOnlyMode)"),
      appSource.indexOf("form.addEventListener(\"submit\""),
    );
    expect(runQueryBody).toContain("currentAnswerContinuation = null;");
    // Captured only on the answering path, never on the retrieve-only one.
    expect(runQueryBody.indexOf("currentAnswerContinuation = {"))
      .toBeGreaterThan(runQueryBody.indexOf('mode: "retrieve"'));

    const restoreBody = appSource.slice(
      appSource.indexOf("function restoreAnswerFromHistoryEntry(entry)"),
      appSource.indexOf("function formatHistoryTime(timestamp)"),
    );
    expect(restoreBody).toContain("currentAnswerContinuation = null;");
  });

  it("stores the seeded thread and switches modes through the one mode switch", () => {
    const body = appSource.slice(
      appSource.indexOf("function continueInConversation()"),
      appSource.indexOf("function ensureSelectedConversation()"),
    );

    expect(body).toContain("Avatar.conversationFromSingleTurn(currentAnswerContinuation");
    expect(body).toContain("storeNewConversation(conversation)");
    expect(body).toContain("setAppMode(APP_MODE_CONVERSATION)");
    // Storage can refuse the thread under quota pressure; do not switch then.
    expect(body.indexOf("storeNewConversation(conversation)"))
      .toBeLessThan(body.indexOf("setAppMode(APP_MODE_CONVERSATION)"));
  });
});
