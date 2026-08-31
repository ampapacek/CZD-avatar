import { describe, expect, it } from "vitest";

import {
  assistantMessageIndexes,
  conversationTurnRailItems,
  conversationTurnRailSignature,
  conversationTurnTarget,
  conversationSourcesBinding,
  resolveSelectedAssistantIndex,
} from "./conversation-turns.js";

// A three-turn thread where every answer cites its own A1. This is the shape
// that made the old "always the latest answer" panel resolve [A1] in turn 1
// against turn 3's document.
const thread = [
  { role: "user", content: "první" },
  { role: "assistant", content: "odpověď 1 [A1]", sources: [{ citation_id: "A1", title: "Dokument A" }] },
  { role: "user", content: "druhá" },
  { role: "assistant", content: "odpověď 2 [A1]", sources: [{ citation_id: "A1", title: "Dokument B" }] },
  { role: "user", content: "třetí" },
  { role: "assistant", content: "odpověď 3 [A1]", sources: [{ citation_id: "A1", title: "Dokument C" }] },
];

describe("assistantMessageIndexes", () => {
  it("lists the assistant turns in thread order", () => {
    expect(assistantMessageIndexes(thread)).toEqual([1, 3, 5]);
  });

  it("tolerates an empty or missing thread", () => {
    expect(assistantMessageIndexes([])).toEqual([]);
    expect(assistantMessageIndexes(undefined)).toEqual([]);
  });
});

describe("conversationTurnRailItems", () => {
  it("creates one question-labelled mark per completed Q/A pair", () => {
    expect(conversationTurnRailItems(thread)).toEqual([
      { answerNumber: 1, assistantIndex: 1, userIndex: 0, question: "první" },
      { answerNumber: 2, assistantIndex: 3, userIndex: 2, question: "druhá" },
      { answerNumber: 3, assistantIndex: 5, userIndex: 4, question: "třetí" },
    ]);
  });

  it("omits a source-only streaming placeholder until it has output", () => {
    const streaming = [
      { role: "user", content: "čekající" },
      { role: "assistant", content: "", sources: [{ citation_id: "A1" }] },
    ];
    expect(conversationTurnRailItems(streaming)).toEqual([]);
  });

  it("keeps the same signature while answer tokens stream into an existing turn", () => {
    const early = thread.slice(0, 2);
    const later = [{ ...early[0] }, { ...early[1], content: `${early[1].content} další tokeny` }];

    expect(conversationTurnRailSignature(7, early)).toBe(conversationTurnRailSignature(7, later));
    expect(conversationTurnRailSignature(8, later)).not.toBe(conversationTurnRailSignature(7, later));
  });

  it("resolves a clicked mark to its answer and question indexes", () => {
    expect(conversationTurnTarget({
      conversationAssistantIndex: "3",
      conversationUserIndex: "2",
    })).toEqual({ assistantIndex: 3, scrollIndex: 2 });
    expect(conversationTurnTarget({ conversationAssistantIndex: "invalid" })).toBeNull();
  });
});

describe("resolveSelectedAssistantIndex", () => {
  it("follows the latest answer when nothing is selected", () => {
    expect(resolveSelectedAssistantIndex(thread, null)).toBe(5);
  });

  it("keeps a selected assistant turn", () => {
    expect(resolveSelectedAssistantIndex(thread, 1)).toBe(1);
  });

  it("falls back to the latest answer for a stale or non-assistant index", () => {
    expect(resolveSelectedAssistantIndex(thread, 2)).toBe(5);
    expect(resolveSelectedAssistantIndex(thread, 42)).toBe(5);
    expect(resolveSelectedAssistantIndex(thread.slice(0, 2), 5)).toBe(1);
  });

  it("has nothing to select before the first answer", () => {
    expect(resolveSelectedAssistantIndex([{ role: "user", content: "první" }], null)).toBeNull();
  });
});

describe("conversationSourcesBinding", () => {
  it("binds the panel to the latest answer by default", () => {
    const binding = conversationSourcesBinding(thread, null);

    expect(binding.selectedIndex).toBe(5);
    expect(binding.message.sources[0].title).toBe("Dokument C");
    expect(binding.isLatest).toBe(true);
    expect(binding.heading).toBe("Zdroje poslední odpovědi");
  });

  it("binds a citation in an older turn to that turn's own sources", () => {
    const binding = conversationSourcesBinding(thread, 1);

    // The bug this fixes: A1 in turn 1 is Dokument A, not the latest turn's A1.
    expect(binding.message.sources[0].title).toBe("Dokument A");
    expect(binding.isLatest).toBe(false);
    expect(binding.answerNumber).toBe(1);
    expect(binding.heading).toBe("Zdroje k 1. odpovědi");
  });

  it("numbers the heading by answer, not by message index", () => {
    expect(conversationSourcesBinding(thread, 3).heading).toBe("Zdroje k 2. odpovědi");
    expect(conversationSourcesBinding(thread, 3).message.sources[0].title).toBe("Dokument B");
  });

  it("goes back to the latest answer when a new turn arrives", () => {
    const pinned = conversationSourcesBinding(thread, 1);
    const afterNewTurn = conversationSourcesBinding(thread, null);

    expect(pinned.selectedIndex).toBe(1);
    expect(afterNewTurn.selectedIndex).toBe(5);
    expect(afterNewTurn.isLatest).toBe(true);
  });

  it("reports an empty thread as the latest with no message", () => {
    const binding = conversationSourcesBinding([], null);

    expect(binding.selectedIndex).toBeNull();
    expect(binding.message).toBeNull();
    expect(binding.answerCount).toBe(0);
    expect(binding.isLatest).toBe(true);
    expect(binding.heading).toBe("Zdroje poslední odpovědi");
  });
});
