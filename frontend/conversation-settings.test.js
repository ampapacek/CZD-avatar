import { describe, expect, it } from "vitest";

import {
  CONVERSATION_SETTINGS_VERSION,
  effectiveConversationSettings,
  hasCurrentConversationSettings,
  hasUsableConversationSettings,
  mergeChangedSettings,
} from "./conversation-settings.js";

describe("conversation settings format", () => {
  it("accepts only the current explicit settings version", () => {
    expect(hasCurrentConversationSettings({ settings_version: CONVERSATION_SETTINGS_VERSION })).toBe(true);
    expect(hasCurrentConversationSettings({})).toBe(false);
    expect(hasCurrentConversationSettings(null)).toBe(false);
  });

  it("keeps version-less settings usable without calling them current", () => {
    expect(hasUsableConversationSettings({ model: "legacy-model" })).toBe(true);
    expect(hasCurrentConversationSettings({ model: "legacy-model" })).toBe(false);
    expect(hasUsableConversationSettings(null)).toBe(false);
    expect(hasUsableConversationSettings([])).toBe(false);
  });

  it("lets settings-less legacy conversations borrow the live fallback", () => {
    const fallback = {
      settings_version: CONVERSATION_SETTINGS_VERSION,
      model: "live-model",
      prompt_preset_id: "wp1-default",
    };

    expect(effectiveConversationSettings(null, fallback)).toEqual(fallback);
    expect(effectiveConversationSettings(null, fallback)).not.toBe(fallback);
  });

  it("fills only missing version-2 retrieval settings from the live fallback", () => {
    const legacy = {
      model: "legacy-model",
      top_k: 7,
      msearch_rescore: undefined,
    };
    const fallback = {
      model: "live-model",
      top_k: 20,
      msearch_rescore: true,
      msearch_min_confidence: 0.4,
      min_relative_score: 0.25,
    };

    expect(effectiveConversationSettings(legacy, fallback)).toEqual({
      model: "legacy-model",
      top_k: 7,
      msearch_rescore: true,
      msearch_min_confidence: 0.4,
      min_relative_score: 0.25,
    });
    expect(legacy).toEqual({
      model: "legacy-model",
      top_k: 7,
      msearch_rescore: undefined,
    });
  });

  it("preserves explicit legacy retrieval values, including false and null", () => {
    const legacy = {
      top_k: 0,
      msearch_rescore: false,
      msearch_min_confidence: null,
      min_relative_score: 0,
    };
    const fallback = {
      top_k: 20,
      msearch_rescore: true,
      msearch_min_confidence: 0.4,
      min_relative_score: 0.25,
    };

    expect(effectiveConversationSettings(legacy, fallback)).toEqual(legacy);
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
