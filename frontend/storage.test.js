import { describe, expect, it } from "vitest";

import {
  approximateLocalStorageMiB,
  compactConversationForStorage,
  saveJsonEntryList,
  storedAssistantSettings,
} from "./storage.js";

describe("conversation storage", () => {
  it("drops request-only fields from assistant settings", () => {
    expect(
      storedAssistantSettings({
        question: "duplicate",
        conversation_history: [{ role: "user", content: "duplicate" }],
        conversation_summary: "stored on the message itself",
        model: "model-a",
        system_prompt: "keep for the history detail",
      }),
    ).toEqual({ model: "model-a", system_prompt: "keep for the history detail" });
  });

  it("keeps retrieved chunks only for the latest assistant turn", () => {
    const conversation = compactConversationForStorage(
      {
        id: 1,
        conversation_summary: "canonical summary",
        messages: [
          { role: "user", content: "first" },
          {
            role: "assistant",
            content: "first answer",
            conversation_summary: "obsolete first snapshot",
            settings: { question: "first", model: "m" },
            retrieved_chunks: [{ chunk_id: "old", text: "old excerpt" }],
            omitted_chunks: [{ chunk_id: "omitted" }],
          },
          { role: "user", content: "second" },
          {
            role: "assistant",
            content: "second answer",
            conversation_summary: "obsolete second snapshot",
            settings: { conversation_history: ["duplicate"], model: "m" },
            retrieved_chunks: [{ chunk_id: "new", text: "123456789" }],
          },
        ],
      },
      { chunkTextLimit: 6 },
    );

    expect(conversation.messages[1].retrieved_chunks).toEqual([]);
    expect(conversation.messages[1].omitted_chunks).toEqual([]);
    expect(conversation.messages[1].settings).toEqual({ model: "m" });
    expect(conversation.conversation_summary).toBe("canonical summary");
    expect(conversation.messages[1]).not.toHaveProperty("conversation_summary");
    expect(conversation.messages[3]).not.toHaveProperty("conversation_summary");
    expect(conversation.messages[3].retrieved_chunks[0].text).toBe("12345…");
  });

  it("estimates localStorage strings using two bytes per character", () => {
    expect(approximateLocalStorageMiB("x".repeat(524288))).toBe(1);
  });

  it("preserves the previous list when a quota write fails", () => {
    const previous = [{ id: "old-1" }, { id: "old-2" }];
    const storage = {
      getItem: () => JSON.stringify(previous),
      setItem: () => {
        throw new DOMException("quota full", "QuotaExceededError");
      },
    };

    expect(saveJsonEntryList(storage, "conversations", [{ id: "new" }])).toEqual({
      saved: false,
      entries: previous,
    });
  });

  it("compacts before writing without dropping entries", () => {
    let stored = "";
    const storage = {
      getItem: () => stored,
      setItem: (_key, value) => {
        stored = value;
      },
    };

    const result = saveJsonEntryList(
      storage,
      "conversations",
      [{ id: 1, extra: "large" }, { id: 2, extra: "large" }],
      ({ id }) => ({ id }),
    );
    expect(result).toEqual({ saved: true, entries: [{ id: 1 }, { id: 2 }] });
    expect(JSON.parse(stored)).toHaveLength(2);
  });
});
