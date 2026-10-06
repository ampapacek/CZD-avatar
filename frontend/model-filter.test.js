import { describe, expect, it } from "vitest";
import { curatedOpenRouterModels, modelSelectorView } from "./model-filter.js";

describe("curated OpenRouter catalogue", () => {
  it("replaces older versions within a variant using numeric comparison", () => {
    expect(curatedOpenRouterModels([
      "openai/gpt-5.6-luna", "openai/gpt-6-luna", "openai/gpt-6.1-sol", "openai/gpt-6-sol",
      "google/gemini-3.7-flash", "google/gemini-3.8-flash", "google/gemini-3.10-flash",
    ])).toEqual(["openai/gpt-6-luna", "openai/gpt-6.1-sol", "google/gemini-3.10-flash"]);
  });

  it("preserves sizes and variants instead of keeping one model per vendor", () => {
    const models = [
      "openai/gpt-6-luna", "openai/gpt-6-astra",
      "openai/gpt-5.4-mini", "openai/gpt-5.4-nano", "openai/gpt-oss-20b", "openai/gpt-oss-120b",
      "google/gemini-3.8-flash", "google/gemini-3.1-pro-preview", "google/gemini-3.5-flash-lite",
      "anthropic/claude-sonnet-5.5", "anthropic/claude-haiku-4.5",
      "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4.1-flash", "deepseek/deepseek-r1",
    ];
    expect(curatedOpenRouterModels(models)).toEqual(models);
  });

  it("only includes Claude Sonnet and Haiku, including older naming schemes", () => {
    expect(curatedOpenRouterModels([
      "anthropic/claude-3.5-sonnet", "anthropic/claude-sonnet-4.6", "anthropic/claude-sonnet-5.5",
      "anthropic/claude-3-haiku", "anthropic/claude-haiku-4.5",
      "anthropic/claude-opus-5.5", "anthropic/claude-fable-5.1",
    ])).toEqual(["anthropic/claude-sonnet-5.5", "anthropic/claude-haiku-4.5"]);
  });

  it("hides GPT Pro routes while preserving other families' Pro variants and Show all", () => {
    const models = [
      "openai/gpt-6.1-sol-pro", "openai/gpt-6-luna-pro", "openai/gpt-6-astra-pro",
      "openai/gpt-5.6-terra-pro", "openai/gpt-5.5-pro", "openai/gpt-5.5-pro-20260901",
      "openai/gpt-6-luna", "google/gemini-3.1-pro-preview", "deepseek/deepseek-v4-pro",
    ];
    expect(curatedOpenRouterModels(models)).toEqual(models.slice(6));
    expect(modelSelectorView({ id: "openrouter", model_presets: models }, { unlocked: true, showAll: true }).models)
      .toEqual(models);
  });

  it("drops unrelated, batch and specialized routes from the compact view", () => {
    expect(curatedOpenRouterModels([
      "meta-llama/llama-4-scout", "openai/gpt-6-luna:batch", "openai/gpt-5-image",
      "openai/gpt-audio", "openai/gpt-5.3-codex", "openai/gpt-oss-safeguard-20b",
      "google/gemini-3-pro-image", "google/gemini-3.1-pro-preview-customtools",
      "deepseek/deepseek-v4-flash-vision-exp", "other/gpt-6-luna",
    ])).toEqual([]);
  });

  it("prefers stable over preview for equal versions, but accepts newer previews", () => {
    expect(curatedOpenRouterModels([
      "google/gemini-3.1-flash-lite-preview", "google/gemini-3.1-flash-lite",
      "google/gemini-2.5-pro", "google/gemini-3.1-pro-preview",
    ])).toEqual(["google/gemini-3.1-flash-lite", "google/gemini-3.1-pro-preview"]);
  });

  it("collapses dated snapshots without splitting them into model families", () => {
    expect(curatedOpenRouterModels([
      "openai/gpt-4o-2024-05-13", "openai/gpt-4o-2024-11-20", "openai/gpt-4o",
      "deepseek/deepseek-v4-flash-0731", "deepseek/deepseek-v4.1-flash",
      "deepseek/deepseek-v4-pro-0813", "deepseek/deepseek-v4-pro",
      "deepseek/deepseek-r1", "deepseek/deepseek-r1-0528",
    ])).toEqual(["openai/gpt-4o", "deepseek/deepseek-v4.1-flash", "deepseek/deepseek-v4-pro", "deepseek/deepseek-r1"]);
  });

  it("keeps only the latest snapshot if no unpinned route exists", () => {
    expect(curatedOpenRouterModels([
      "openai/gpt-4o-2024-05-13", "openai/gpt-4o-2024-11-20",
    ])).toEqual(["openai/gpt-4o-2024-11-20"]);
  });

  it("folds generic DeepSeek V models into the newer Pro slot, preserving reasoning", () => {
    expect(curatedOpenRouterModels([
      "deepseek/deepseek-chat-v3-0324", "deepseek/deepseek-v3.2",
      "deepseek/deepseek-v4-pro", "deepseek/deepseek-r1",
    ])).toEqual(["deepseek/deepseek-v4-pro", "deepseek/deepseek-r1"]);
  });
});

describe("model selector access and selection", () => {
  const provider = {
    id: "openrouter",
    model_presets: ["openrouter/free", "openai/gpt-5.6-luna", "openai/gpt-6-luna", "anthropic/claude-opus-5.5"],
    public_models: ["openrouter/free", "unavailable/model"],
  };

  it("keeps the public router in the default curated view", () => {
    expect(modelSelectorView(provider, { unlocked: true }).models)
      .toEqual(["openrouter/free", "openai/gpt-6-luna"]);
  });

  it("shows every allowed model when Show all is enabled", () => {
    expect(modelSelectorView(provider, { unlocked: true, showAll: true }).models)
      .toEqual(provider.model_presets);
  });

  it("retains the current older or other-family selection when switching back", () => {
    for (const currentModel of ["openai/gpt-5.6-luna", "anthropic/claude-opus-5.5"]) {
      const view = modelSelectorView(provider, { unlocked: true, currentModel });
      expect(view.models).toContain(currentModel);
      expect(view.selectedOutsideFilter).toBe(true);
    }
  });

  it("does not unlock models via the toggle or a previous selection", () => {
    const view = modelSelectorView(provider, { showAll: true, currentModel: "openai/gpt-6-luna" });
    expect(view.models).toEqual(["openrouter/free"]);
    expect(view.filterAvailable).toBe(false);
  });

  it("does not filter other providers", () => {
    const view = modelSelectorView({ ...provider, id: "einfra" }, { unlocked: true });
    expect(view.models).toEqual(provider.model_presets);
    expect(view.filterAvailable).toBe(false);
  });

  it("does not reintroduce disappeared or custom model IDs", () => {
    expect(modelSelectorView(provider, { unlocked: true, currentModel: "openai/removed" }).models)
      .toEqual(["openrouter/free", "openai/gpt-6-luna"]);
    expect(modelSelectorView(null).models).toEqual([]);
  });
});
