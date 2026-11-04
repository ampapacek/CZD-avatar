import { describe, expect, it } from "vitest";

import {
  NO_SOURCES_COLLECTION,
  collectionUsesSources,
  promptUsesSources,
  retrievalEnabled,
} from "./source-mode.js";

const DEFAULTS = {
  system_prompt: "Jsi RAG asistent.",
  user_prompt_template: "Otázka:\n{question}\n\nNalezený kontext:\n{retrieved_snippets}",
};

describe("source mode", () => {
  it("reads the mode from the collection selector value", () => {
    expect(collectionUsesSources(NO_SOURCES_COLLECTION)).toBe(false);
    expect(collectionUsesSources("64d6f521")).toBe(true);
    // Before collections load the selector is empty; that is not "Bez zdrojů".
    expect(collectionUsesSources("")).toBe(true);
  });

  it("treats Bez zdrojů and zero documents as retrieval off", () => {
    expect(retrievalEnabled({ collection: "64d6f521", topK: 10 })).toBe(true);
    expect(retrievalEnabled({ collection: "64d6f521", topK: "0" })).toBe(false);
    expect(retrievalEnabled({ collection: NO_SOURCES_COLLECTION, topK: 10 })).toBe(false);
  });

  it("finds {retrieved_snippets} in either prompt text", () => {
    expect(promptUsesSources({ systemPrompt: "Kontext: {retrieved_snippets}", userPromptTemplate: "{question}" }, DEFAULTS)).toBe(true);
    expect(promptUsesSources({ systemPrompt: "Jsi asistent.", userPromptTemplate: "{question}" }, DEFAULTS)).toBe(false);
    expect(promptUsesSources({ systemPrompt: "", userPromptTemplate: "{question}\n{retrieved_snippets!s}" }, DEFAULTS)).toBe(true);
  });

  it("reads an empty text as the server default", () => {
    expect(promptUsesSources({ systemPrompt: "", userPromptTemplate: "" }, DEFAULTS)).toBe(true);
    expect(promptUsesSources({ systemPrompt: "Jsi asistent.", userPromptTemplate: "  " }, DEFAULTS)).toBe(true);
    expect(promptUsesSources({ systemPrompt: "", userPromptTemplate: "{question}" }, DEFAULTS)).toBe(false);
  });
});
