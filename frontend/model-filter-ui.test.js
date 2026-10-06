import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

const source = readFileSync("app/static/app.js", "utf8");

// Run the actual selector functions and change listeners with the served bundle
// and page markup. Stub only unrelated settings, token-budget and API work.
function selector() {
  const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"), { runScripts: "outside-only" });
  const w = dom.window;
  w.eval(readFileSync("app/static/avatar.bundle.js", "utf8"));
  for (const id of ["model", "customModel", "llmBaseUrl", "openRouterModelFilter", "showAllOpenRouterModels", "openRouterModelFilterNote"]) {
    w[id] = w.document.getElementById(id);
  }
  w.appSettings = {};
  w.CUSTOM_MODEL_VALUE = "__custom__";
  w.provider = {
    id: "openrouter", default_model: "openrouter/free", public_models: ["openrouter/free"],
    model_presets: ["openrouter/free", "openai/gpt-5.6-luna", "openai/gpt-6-luna", "anthropic/claude-opus-5.5"],
  };
  w.unlocked = true;
  w.selectedProviderConfig = () => w.provider;
  w.customModelAllowed = () => w.unlocked;
  w.selectedProviderApiKey = w.selectedProviderBaseUrl = () => "";
  w.escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
  w.updateCustomModelVisibility = w.updateLlmPolicyNote = w.updateContextWindowForSelectedModel = w.persistLlmSettings = () => {};
  w.eval(source.slice(source.indexOf("function populateModels("), source.indexOf("// System placeholders are filled by the server and never surfaced")));
  w.eval(source.match(/^showAllOpenRouterModels.addEventListener.*$/m)[0]);
  w.eval(source.slice(source.indexOf('model.addEventListener("change"'), source.indexOf('llmUnlockPassword.addEventListener("input"')));
  w.refreshModelOptions();
  return w;
}

describe("OpenRouter selector integration", () => {
  it("starts compact and the real toggle opens the full catalogue", () => {
    const w = selector();
    expect(w.model.value).toBe("openrouter/free");
    expect(w.openRouterModelFilter.hidden).toBe(false);
    expect([...w.model.options].map((o) => o.value)).toEqual(["openrouter/free", "openai/gpt-6-luna", "__custom__"]);
    w.showAllOpenRouterModels.checked = true;
    w.showAllOpenRouterModels.dispatchEvent(new w.Event("change"));
    expect([...w.model.options].map((o) => o.value)).toContain("anthropic/claude-opus-5.5");
    expect(w.model.value).toBe("openrouter/free");
  });

  it("retains an older selection on collapse, then removes it after choosing a current model", () => {
    const w = selector();
    w.showAllOpenRouterModels.checked = true;
    w.showAllOpenRouterModels.dispatchEvent(new w.Event("change"));
    w.model.value = "openai/gpt-5.6-luna";
    w.model.dispatchEvent(new w.Event("change"));
    w.showAllOpenRouterModels.checked = false;
    w.showAllOpenRouterModels.dispatchEvent(new w.Event("change"));
    expect(w.model.value).toBe("openai/gpt-5.6-luna");
    expect(w.openRouterModelFilterNote.textContent).toContain("mimo filtr");
    w.model.value = "openai/gpt-6-luna";
    w.model.dispatchEvent(new w.Event("change"));
    expect([...w.model.options].map((o) => o.value)).not.toContain("openai/gpt-5.6-luna");
    expect(w.model.value).toBe("openai/gpt-6-luna");
  });

  it("removes paid choices and hides the toggle when access is locked again", () => {
    const w = selector();
    w.model.value = "openai/gpt-6-luna";
    w.showAllOpenRouterModels.checked = true;
    w.unlocked = false;
    w.refreshModelOptions();
    expect(w.openRouterModelFilter.hidden).toBe(true);
    expect([...w.model.options].map((o) => o.value)).toEqual(["openrouter/free"]);
    expect(w.model.value).toBe("openrouter/free");
  });

  it("preserves a custom model choice and leaves other providers unfiltered", () => {
    const w = selector();
    w.customModel.value = "vendor/custom";
    w.model.value = "__custom__";
    w.model.dispatchEvent(new w.Event("change"));
    expect(w.model.value).toBe("__custom__");
    expect(w.customModel.value).toBe("vendor/custom");
    w.provider = { ...w.provider, id: "einfra" };
    w.refreshModelOptions();
    expect(w.openRouterModelFilter.hidden).toBe(true);
    expect([...w.model.options].map((o) => o.value)).toContain("anthropic/claude-opus-5.5");
  });
});
