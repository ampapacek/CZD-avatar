import { describe, expect, it } from "vitest";

import {
  CONVERSATION_SETTINGS_VERSION,
  hasCurrentConversationSettings,
  mergeChangedSettings,
} from "./conversation-settings.js";

describe("conversation settings format", () => {
  it("accepts only the current explicit settings version", () => {
    expect(hasCurrentConversationSettings({ settings_version: CONVERSATION_SETTINGS_VERSION })).toBe(true);
    expect(hasCurrentConversationSettings({})).toBe(false);
    expect(hasCurrentConversationSettings(null)).toBe(false);
  });
});

describe("Settings-dialog propagation", () => {
  it("patches only dialog changes into the saved main settings", () => {
    const main = { model: "main-model", system_prompt: "old", top_k: 10 };
    const conversationBefore = { model: "conversation-model", system_prompt: "old", top_k: 20 };
    const conversationAfter = { model: "conversation-model", system_prompt: "edited", top_k: 20 };

    expect(mergeChangedSettings(main, conversationBefore, conversationAfter)).toEqual({
      model: "main-model",
      system_prompt: "edited",
      top_k: 10,
    });
  });
});
