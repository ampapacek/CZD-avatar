import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
const document = dom.window.document;
const css = readFileSync("app/static/styles.css", "utf8");
const appSource = readFileSync("app/static/app.js", "utf8");

describe("selected main-screen structure", () => {
  it("keeps Oblast visible and groups response choices in a matching disclosure", () => {
    const topicControls = document.querySelector(".composer > .topic-controls");
    const responseSettings = document.querySelector(".composer > .response-settings");
    expect(topicControls.querySelector("label > span").textContent.trim()).toBe("Oblast");
    expect(responseSettings.tagName).toBe("DETAILS");
    expect(responseSettings.hasAttribute("open")).toBe(false);
    expect(responseSettings.querySelector("summary").textContent.trim()).toBe("Podoba odpovědi");
    expect(responseSettings.querySelector(".prompt-control > span").textContent.trim()).toBe("Profil");
    expect(responseSettings.querySelector("#placeholderControls")).not.toBeNull();
    expect(document.querySelector(".composer > .model-settings > summary").textContent.trim()).toBe("Model");
    const collection = document.querySelector("#msearchCollection");
    expect(collection.closest("details")?.querySelector("summary")?.textContent.trim()).toBe("Pokročilé nastavení");
    expect(document.querySelector("#placeholderControls").closest("details")).toBe(responseSettings);
  });

  it("places the topic-aware quick-start around the question and hides the empty answer panel", () => {
    const topicControls = document.querySelector(".topic-controls");
    const welcome = document.querySelector("#answerWelcome");
    const question = document.querySelector(".question-field");
    const examples = document.querySelector("#answerWelcomeExamples");
    const questionActions = document.querySelector(".question-actions");
    const questionStatus = document.querySelector("#questionStatus");
    const responseSettings = document.querySelector(".response-settings");
    const modelSettings = document.querySelector(".composer > .model-settings");
    const guide = document.querySelector("#answerWelcomeGuide");
    expect(welcome.querySelector(".answer-welcome-title").textContent).toContain("Polož otázku k tématu");
    expect(welcome.querySelector(".answer-welcome-title #answerWelcomeWp")).not.toBeNull();
    expect(topicControls.compareDocumentPosition(welcome) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(welcome.compareDocumentPosition(question) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(question.compareDocumentPosition(examples) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(examples.compareDocumentPosition(questionActions) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(questionActions.compareDocumentPosition(questionStatus) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(questionStatus.getAttribute("role")).toBe("status");
    expect(questionActions.compareDocumentPosition(guide) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(guide.compareDocumentPosition(responseSettings) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(responseSettings.compareDocumentPosition(modelSettings) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(guide.textContent).toContain("Oblast");
    expect(guide.textContent).toContain("Podoba odpovědi");
    expect(guide.textContent).toContain("vyhledá relevantní zdroje");
    expect(guide.textContent).toContain("Pokročilé nastavení");
    expect(document.querySelector("#answerPanel").hidden).toBe(true);
    expect(document.querySelector("#sourcesPanel").hidden).toBe(true);
    expect(document.querySelector("#sourcesReopen").getAttribute("aria-controls")).toBe("sourcesBody");
  });

  it("submits a welcome example through the normal answer form", () => {
    expect(appSource).toMatch(
      /answerWelcomeList\?\.addEventListener\("click",[\s\S]*?form\.requestSubmit\(submitButton\);/,
    );
  });

  it("shows random-question feedback outside the hidden answer panel", () => {
    const questionStatus = document.querySelector("#questionStatus");
    expect(questionStatus.closest("#answerPanel")).toBeNull();
    expect(appSource).toMatch(
      /randomQuestionButton\.addEventListener\("click",[\s\S]*?questionStatus\.hidden = false;[\s\S]*?questionStatus\.className = "status error";/,
    );
  });
});

describe("selected Settings and Help organization", () => {
  it("has exactly three Settings categories with one panel each", () => {
    const tabs = [...document.querySelectorAll("#settingsCategoryTabs [role='tab']")];
    const panels = [...document.querySelectorAll(".settings-body > [role='tabpanel']")];
    expect(tabs.map((tab) => tab.textContent.trim())).toEqual([
      "Profily a proměnné",
      "Modely a tokeny",
      "API a přístup",
    ]);
    expect(panels).toHaveLength(3);
    expect(panels.map((panel) => panel.dataset.settingsPanel)).toEqual(["profiles", "models", "access"]);
    expect(document.querySelector(".settings-wp-section").closest("[role='tabpanel']")).toBe(panels[0]);
  });

  it("puts normal workflow and verification before disclosed technical help", () => {
    const helpBody = document.querySelector(".help-body");
    const start = helpBody.querySelector(".help-start");
    const verification = helpBody.querySelector(".help-verification");
    const firstDetails = helpBody.querySelector("details.help-details");
    expect(start.querySelector("h3").textContent.trim()).toBe("Jak začít");
    expect(verification.textContent).toContain("Odpovědi ověřuj");
    expect(start.compareDocumentPosition(verification) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(verification.compareDocumentPosition(firstDetails) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("selected typography and accessibility contracts", () => {
  it("self-hosts all three selected families with latin and latin-ext subsets", () => {
    for (const family of ["Source Serif 4", "IBM Plex Sans", "IBM Plex Mono"]) {
      expect(css).toContain(`font-family: "${family}"`);
    }
    expect(css).toContain("-latin-ext.woff2");
    expect(css).not.toMatch(/https?:\/\//);
  });

  it("keeps the answer full-width and defines a theme-aware focus token", () => {
    expect(css).not.toMatch(/(?:max-)?width\s*:[^;]*\d+ch/);
    expect(css).toContain("max-width: none");
    expect(css.match(/--focus-ring:/g)).toHaveLength(2);
    expect(css).toContain(":focus-visible");
  });
});
