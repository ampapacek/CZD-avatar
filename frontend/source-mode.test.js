import { describe, expect, it } from "vitest";

import {
  NO_SOURCES_COLLECTION,
  collectionUsesSources,
  pickPromptForMode,
  promptTextsForModeSwitch,
  promptUsesSources,
  promptsForMode,
  requestPromptTexts,
} from "./source-mode.js";

const PROMPTS = [
  { id: "ucitel" },
  { id: "historik", uses_sources: true },
  { id: "obecny", uses_sources: false },
  { id: "local-bare", uses_sources: false },
];

describe("source mode", () => {
  it("reads the mode from the collection selector value", () => {
    expect(collectionUsesSources(NO_SOURCES_COLLECTION)).toBe(false);
    expect(collectionUsesSources("64d6f521")).toBe(true);
    // Before collections load the selector is empty; that is not "Bez zdrojů".
    expect(collectionUsesSources("")).toBe(true);
  });

  it("treats a prompt without the flag as one that uses sources", () => {
    expect(promptUsesSources({ id: "legacy" })).toBe(true);
    expect(promptUsesSources({ uses_sources: false })).toBe(false);
    expect(promptUsesSources(null)).toBe(true);
    expect(promptsForMode(PROMPTS, false).map((preset) => preset.id)).toEqual(["obecny", "local-bare"]);
    expect(promptsForMode(PROMPTS, true).map((preset) => preset.id)).toEqual(["ucitel", "historik"]);
  });

  it("prefers the prompt last used in the mode, then the WP default, then the first one", () => {
    expect(pickPromptForMode(PROMPTS, false, { rememberedId: "local-bare", defaultId: "ucitel" })).toBe("local-bare");
    // A remembered prompt from the other mode does not count.
    expect(pickPromptForMode(PROMPTS, true, { rememberedId: "obecny", defaultId: "historik" })).toBe("historik");
    expect(pickPromptForMode(PROMPTS, false, { defaultId: "ucitel" })).toBe("obecny");
    expect(pickPromptForMode([{ id: "ucitel" }], false)).toBeNull();
  });
});

describe("request prompt texts", () => {
  const defaults = { system_prompt: "RAG system", user_prompt_template: "RAG user" };

  it("sends the built-in defaults as null when sources are used", () => {
    expect(requestPromptTexts({ systemPrompt: "RAG system", userPromptTemplate: "Custom", defaults })).toEqual({
      system_prompt: null,
      user_prompt_template: "Custom",
    });
  });

  it("sends the texts verbatim without sources, so an empty system prompt stays empty", () => {
    expect(
      requestPromptTexts({ systemPrompt: "", userPromptTemplate: "RAG user", defaults, useSources: false }),
    ).toEqual({ system_prompt: "", user_prompt_template: "RAG user" });
  });
});

describe("prompt texts after flipping Používá zdroje", () => {
  const defaults = {
    sources: { system_prompt: "RAG system", user_prompt_template: "RAG user" },
    noSources: { system_prompt: "Generic system", user_prompt_template: "{question}" },
  };

  it("swaps untouched starting texts for the new mode's", () => {
    expect(
      promptTextsForModeSwitch({ systemPrompt: "RAG system", userPromptTemplate: "", useSources: false, defaults }),
    ).toEqual({ systemPrompt: "Generic system", userPromptTemplate: "{question}" });
    expect(
      promptTextsForModeSwitch({ systemPrompt: "Generic system", userPromptTemplate: "{question}", useSources: true, defaults }),
    ).toEqual({ systemPrompt: "RAG system", userPromptTemplate: "RAG user" });
  });

  it("keeps anything the user wrote", () => {
    expect(
      promptTextsForModeSwitch({ systemPrompt: "Mine", userPromptTemplate: "Also mine", useSources: false, defaults }),
    ).toEqual({ systemPrompt: "Mine", userPromptTemplate: "Also mine" });
  });
});
