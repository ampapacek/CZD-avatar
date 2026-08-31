import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import { hasCurrentConversationSettings } from "./conversation-settings.js";

describe("conversation request UI", () => {
  it("starts loading the active WP's default question before prompt profiles finish", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");
    const loadSettingsBody = appSource.slice(
      appSource.indexOf("async function loadSettings()"),
      appSource.indexOf("// Shared by the"),
    );

    expect(loadSettingsBody).toContain("const initialQuestionsPromise = loadPredefinedQuestions(activeWpId");
    expect(loadSettingsBody.indexOf("initialQuestionsPromise"))
      .toBeLessThan(loadSettingsBody.indexOf("await loadPromptPresets()"));
    expect(loadSettingsBody).toContain("await initialQuestionsPromise");
  });

  it("shows request progress inside the scrollable conversation stream", () => {
    const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
    const document = dom.window.document;
    const messageStream = document.querySelector("#conversationMessages");
    const progress = document.querySelector("#conversationRequestStatus");

    expect(messageStream).not.toBeNull();
    expect(progress).not.toBeNull();
    expect(messageStream.contains(progress)).toBe(true);
    expect(document.querySelector(".conversation-composer")?.contains(progress)).toBe(false);
  });

  it("places query rewriting and its result before the sources heading", () => {
    const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
    const document = dom.window.document;
    const controls = document.querySelector(".conversation-rewrite-controls");
    const result = document.querySelector("#conversationRetrievalInfo");
    // The heading is rebound to whichever answer the panel is showing (see
    // conversation-turns.js), so it is addressed by id rather than by its text.
    const heading = document.querySelector("#conversationSourcesHeading");

    expect(controls).not.toBeNull();
    expect(result).not.toBeNull();
    expect(heading).not.toBeNull();
    expect(heading.tagName).toBe("H3");
    expect(heading.textContent.trim()).toBe("Zdroje poslední odpovědi");
    expect(controls.contains(result)).toBe(true);
    expect(controls.compareDocumentPosition(heading) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("wraps long conversation text while keeping structured blocks scrollable", () => {
    const css = readFileSync("app/static/styles.css", "utf8");
    const dom = new JSDOM(`
      <style>${css}</style>
      <article class="conversation-message user">
        <div class="conversation-message-body"><p>longtext</p><pre>code</pre></div>
      </article>
    `);
    const message = dom.window.document.querySelector(".conversation-message");
    const body = dom.window.document.querySelector(".conversation-message-body");
    const pre = dom.window.document.querySelector("pre");

    expect(dom.window.getComputedStyle(message).overflowWrap).toBe("anywhere");
    expect(dom.window.getComputedStyle(body).overflowWrap).toBe("anywhere");
    expect(dom.window.getComputedStyle(pre).overflowX).toBe("auto");
  });
});

describe("conversation mode is a view, not a dialog", () => {
  const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
  const document = dom.window.document;

  it("renders the conversation workspace inside the shell with no dialog", () => {
    const view = document.querySelector("#conversationView");

    expect(document.querySelector("#conversationDialog")).toBeNull();
    expect(view).not.toBeNull();
    expect(view.tagName).not.toBe("DIALOG");
    expect(view.closest("dialog")).toBeNull();
    expect(view.parentElement).toBe(document.querySelector("main.shell"));
    // Starts hidden: the single-question view is the default mode.
    expect(view.hasAttribute("hidden")).toBe(true);
  });

  it("keeps the topbar outside the swapped views so it stays reachable", () => {
    const shell = document.querySelector("main.shell");
    const topbar = document.querySelector(".topbar");

    expect(topbar.parentElement).toBe(shell);
    expect(document.querySelector(".workspace").contains(topbar)).toBe(false);
    expect(document.querySelector("#conversationView").contains(topbar)).toBe(false);
  });

  it("offers the two modes as peers in the topbar", () => {
    const single = document.querySelector("#modeSingleButton");
    const conversation = document.querySelector("#modeConversationButton");

    expect(document.querySelector("#conversationButton")).toBeNull();
    expect(single.closest(".topbar")).not.toBeNull();
    expect(conversation.closest(".mode-switch")).toBe(single.closest(".mode-switch"));
    expect(single.textContent.trim()).toBe("Jedna otázka");
    expect(conversation.textContent.trim()).toBe("Konverzace");
    expect(single.getAttribute("aria-selected")).toBe("true");
    expect(conversation.getAttribute("aria-selected")).toBe("false");
  });

  it("has no way to dismiss the mode by accident", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");

    expect(document.querySelector("#closeConversationButton")).toBeNull();
    // The backdrop-close handler went with the dialog rather than being orphaned.
    expect(appSource).not.toMatch(/conversationDialog/);
    expect(appSource).not.toMatch(/showModal\(\)[\s\S]{0,40}conversation/i);
  });

  it("puts the conversation settings in a composer popover, not above the thread", () => {
    const popover = document.querySelector("#conversationSettingsPopover");
    const messages = document.querySelector("#conversationMessages");
    const toggle = document.querySelector("#conversationSettingsToggle");

    expect(popover).not.toBeNull();
    expect(popover.hasAttribute("hidden")).toBe(true);
    expect(toggle.getAttribute("aria-controls")).toBe("conversationSettingsPopover");
    // Below the thread, and outside the form so Enter in a settings field cannot
    // submit a turn.
    expect(messages.compareDocumentPosition(popover) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(popover.closest("#conversationForm")).toBeNull();
    expect(document.querySelector("#convWpSelect").closest("#conversationSettingsPopover")).toBe(popover);
  });

  it("keeps the basic conversation settings compact and puts placeholders below them", () => {
    const basic = document.querySelector(".conversation-settings-basic");
    const labels = [...basic.querySelectorAll(":scope > label > span")].map((span) => span.textContent.trim());
    const placeholders = document.querySelector("#convPlaceholderControls");

    expect(labels).toEqual(["Oblast", "Profil", "Model"]);
    expect(basic.compareDocumentPosition(placeholders) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("moves all ten advanced controls into a closed disclosure", () => {
    const details = document.querySelector(".conversation-settings-advanced");
    const required = [
      "#convProvider",
      "#convAdvancedModel",
      "#convCustomModel",
      "#convContextWindowTokens",
      "#convMsearchCollection",
      "#convTopK",
      "#convMinRelativeScore",
      "#convMsearchMinConfidence",
      "#convMsearchRescore",
      "#convReasoningEffort",
    ];

    expect(details.open).toBe(false);
    expect(details.querySelector("summary").textContent.trim()).toBe("Pokročilé nastavení");
    for (const selector of required) {
      expect(details.querySelector(selector)).not.toBeNull();
    }
    expect(details.querySelector("#convPlaceholderControls")).toBeNull();
    expect(details.querySelector("#queryTransformSection")).toBeNull();
    expect(details.querySelector("#convContextWindowTokens").closest("label").nextElementSibling)
      .toBe(details.querySelector("#convReasoningEffortField"));
    expect(details.querySelectorAll(".conversation-retrieval-sliders > label")).toHaveLength(3);
  });

  it("enlarges the collapsed settings chips and resolves current profile names first", () => {
    const css = readFileSync("app/static/styles.css", "utf8");
    const appSource = readFileSync("app/static/app.js", "utf8");
    const historyBody = appSource.slice(
      appSource.indexOf("function promptPresetLabelFromSettings(settings)"),
      appSource.indexOf("function currentPromptPresetLabelFromSettings(settings)"),
    );
    const chipBody = appSource.slice(
      appSource.indexOf("function currentPromptPresetLabelFromSettings(settings)"),
      appSource.indexOf("function wpLabelFromSettings(settings)"),
    );

    expect(css).toMatch(/\.conversation-chips\[aria-expanded="false"\] \.conversation-chip/);
    // The chip describes still-editable settings, so it follows the live name;
    // history is the record of what an answer ran with, so it keeps the stored
    // one and survives a later rename of the profile.
    expect(chipBody).toContain("getPromptPresetById(presetId)?.name || settings?.prompt_preset_name");
    expect(historyBody).toContain("settings?.prompt_preset_name || getPromptPresetById(presetId)?.name");
    expect(appSource).toContain(
      'currentPromptPresetLabelFromSettings(settings) : "", "Profil", false',
    );
    expect(appSource).toContain(
      '${renderSetting("Prompt", promptPresetLabelFromSettings(entry.settings))}',
    );
  });

  it("places the turn rail outside the sources panel", () => {
    const view = document.querySelector("#conversationView");
    const rail = document.querySelector("#conversationTurnRail");
    const sources = document.querySelector("#conversationSourcesPanel");

    expect(view.contains(rail)).toBe(true);
    expect(sources.contains(rail)).toBe(false);
    expect(Array.from(view.children).includes(rail)).toBe(true);
    expect(rail.compareDocumentPosition(sources) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("collapses conversation sources independently of the single-turn shell", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");
    const css = readFileSync("app/static/styles.css", "utf8");

    expect(document.querySelector("#conversationSourcesCollapse")).not.toBeNull();
    expect(document.querySelector("#conversationSourcesReopen").closest("#conversationTurnRail")).not.toBeNull();
    expect(appSource).toMatch(/conversationView\?\.classList\.toggle\("conversation-sources-collapsed"/);
    expect(css).toMatch(/\.conversation-view\.conversation-sources-collapsed/);
    expect(appSource).not.toMatch(/setConversationSourcesCollapsed[\s\S]{0,500}shellEl\.classList/);
  });

  it("captures, applies and directly payload-overrides the four conversation retrieval settings", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");
    const snapshotBody = appSource.slice(
      appSource.indexOf("function captureSettingsSnapshot()"),
      appSource.indexOf("function currentMainSettings()"),
    );
    const applyBody = appSource.slice(
      appSource.indexOf("function applySettingsToGlobals(settings)"),
      appSource.indexOf("function applyConvWp("),
    );

    for (const key of ["top_k", "msearch_rescore", "msearch_min_confidence", "min_relative_score"]) {
      expect(snapshotBody).toContain(key);
      expect(applyBody).toContain(key);
    }
    expect(appSource).toContain("top_k: Number(convSettings.top_k)");
    expect(appSource).toContain("msearch_rescore: Boolean(convSettings.msearch_rescore)");
    expect(appSource).toContain("msearch_min_confidence: convSettings.msearch_min_confidence");
    expect(appSource).toContain("min_relative_score: convSettings.min_relative_score");
    expect(appSource).not.toContain("conversationRetrievalOverrides");
  });

  it("keeps incompatible conversations readable and asks for a new conversation", () => {
    const status = document.querySelector("#conversationCompatibilityStatus");
    const appSource = readFileSync("app/static/app.js", "utf8");

    expect(status).not.toBeNull();
    expect(status.hasAttribute("hidden")).toBe(true);
    expect(status.textContent.replace(/\s+/g, " ").trim())
      .toBe("Tato konverzace používá starší formát nastavení. Pro pokračování založte novou konverzaci.");
    expect(appSource).toContain("Avatar.hasCurrentConversationSettings(conversation?.settings)");
    expect(appSource).toContain(
      'conversationChipPrompt, settings ? currentPromptPresetLabelFromSettings(settings) : "", "Profil", false',
    );
    expect(appSource).not.toMatch(/conversation\.settings\) \|\| currentMainSettings/);
  });

  it("debounces Settings input propagation and preserves the owner prompt across WP excursions", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");

    expect(appSource).toContain('settingsDialog.addEventListener("input", scheduleSettingsDialogSync)');
    expect(appSource).toContain("settingsDialogOwnerPromptSnapshot");
    expect(appSource).toContain("restorePromptSettings(settingsDialogOwnerPromptSnapshot");
    expect(appSource).toContain("syncConversationControlsFromMain({ refreshOptions: true })");
  });

  it("keeps the turn rail DOM stable while streaming and moves focus when sources collapse", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");

    expect(appSource).toContain("Avatar.conversationTurnRailSignature(conversationId, messages)");
    expect(appSource).toContain("if (signature === conversationTurnRailSignature)");
    expect(appSource).toContain("conversationSourcesReopen?.focus()");
    expect(appSource).toContain("conversationSourcesCollapse?.focus()");
  });

  it("drops the composer label and helper line and surfaces the send shortcut", () => {
    const textarea = document.querySelector("#conversationQuestion");

    expect(textarea.closest("label")).toBeNull();
    expect(textarea.getAttribute("rows")).toBe("1");
    expect(document.querySelector(".conversation-note")).toBeNull();
    expect(document.body.textContent).not.toContain("Pokračování dotazu");
    expect(document.body.textContent).not.toContain("viz „Nastavení konverzace“ nahoře");
    expect(document.querySelector(".conversation-hint").textContent.replace(/\s+/g, " ").trim())
      .toBe("Odeslat: ⌘ + Enter");
  });

  it("makes New conversation a row of the list and deletion a per-item action", () => {
    const panel = document.querySelector(".conversation-list-panel");
    const newButton = document.querySelector("#newConversationButton");
    const appSource = readFileSync("app/static/app.js", "utf8");

    expect(newButton.closest(".conversation-list-scroll")).not.toBeNull();
    expect(panel.querySelector(".conversation-list-header h2").textContent.trim()).toBe("Konverzace");
    expect(document.querySelector("#deleteConversationButton")).toBeNull();
    // Deletion names the thread and asks first.
    expect(appSource).toMatch(/function deleteConversation\(id\)/);
    expect(appSource).toMatch(/window\.confirm\(`Smazat konverzaci/);
  });

  it("keeps the history browser's own chrome for the history browser", () => {
    const headers = [...document.querySelectorAll(".history-dialog-header")];

    expect(headers.length).toBeGreaterThan(0);
    for (const header of headers) {
      expect(header.closest("#conversationView")).toBeNull();
    }
    expect(document.querySelector("#conversationView .history-list")).toBeNull();
    expect(document.querySelector("#historyDialog .history-dialog-header")).not.toBeNull();
  });
});

describe("the assistant turn is prose, not a bubble", () => {
  const css = readFileSync("app/static/styles.css", "utf8");
  const dom = new JSDOM(`
    <style>${css}</style>
    <article class="conversation-message user"><div class="conversation-message-body">q</div></article>
    <article class="conversation-message assistant"><div class="conversation-message-body">a</div></article>
  `);
  const styleOf = (selector) =>
    dom.window.getComputedStyle(dom.window.document.querySelector(selector));

  it("keeps the card on the question and drops it from the answer", () => {
    const user = styleOf(".conversation-message.user");
    const assistant = styleOf(".conversation-message.assistant");

    expect(user.background).toContain("color-mix");
    expect(user.justifySelf).toBe("end");
    expect(user.maxWidth).toBe("92%");

    // Full-width prose: no card background, no width cap, no bubble alignment.
    expect(assistant.background).toBe("rgba(0, 0, 0, 0)");
    expect(assistant.justifySelf).toBe("stretch");
    expect(assistant.width).toBe("100%");
    expect(assistant.maxWidth).toBe("");
  });

  it("declares the border on the user turn only, not on the shared rule", () => {
    // jsdom does not resolve the `border` shorthand, so this reads the rules.
    const ruleBody = (selector) =>
      css.slice(css.indexOf(`${selector} {`) + selector.length + 2).split("}")[0];

    expect(ruleBody(".conversation-message")).not.toMatch(/\bborder:/);
    expect(ruleBody(".conversation-message")).not.toMatch(/\bbackground:/);
    expect(ruleBody(".conversation-message.user")).toMatch(/border: 1px solid/);
  });
});

// Every thread stored before settings_version 2 is "incompatible", and nothing
// migrates one forward — so this is the path a returning user actually hits.
// It has to render the banner and "—" chips, not throw on the way in.
describe("chips for a conversation stored before the current settings version", () => {
  const appSource = readFileSync("app/static/app.js", "utf8");
  const chipSource = appSource.slice(
    appSource.indexOf("function updateConversationChips(conversation) {"),
    appSource.indexOf("function conversationModelDisplayName(rawModel) {"),
  );

  function renderChips(conversation) {
    const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
    const document = dom.window.document;
    const chips = {
      model: document.querySelector("#conversationChipModel"),
      wp: document.querySelector("#conversationChipWp"),
      prompt: document.querySelector("#conversationChipPrompt"),
    };
    const updateConversationChips = new Function(
      "Avatar",
      "getWpConfig",
      "currentPromptPresetLabelFromSettings",
      "shortenText",
      "conversationModelDisplayName",
      "conversationChipModel",
      "conversationChipWp",
      "conversationChipPrompt",
      `${chipSource}\nreturn updateConversationChips;`,
    )(
      { hasCurrentConversationSettings },
      (wpId) => (wpId === "wp1" ? { id: "wp1", label: "Oblast jedna" } : null),
      (settings) => settings.prompt_preset_name || settings.prompt_preset_id,
      (text) => String(text || ""),
      (raw) => String(raw || ""),
      chips.model,
      chips.wp,
      chips.prompt,
    );

    updateConversationChips(conversation);
    return chips;
  }

  const staleSettings = { model: "openai/gpt-4o", wp_id: "wp1", prompt_preset_id: "p1" };

  it("renders placeholders instead of throwing on a version-less thread", () => {
    expect(() => renderChips({ settings: staleSettings })).not.toThrow();

    const chips = renderChips({ settings: staleSettings });

    expect(chips.model.textContent).toBe("—");
    expect(chips.wp.textContent).toBe("—");
    expect(chips.prompt.textContent).toBe("—");
    expect(chips.model.title).toBe("Model: —");
  });

  it("still renders the real values once the thread carries the current version", () => {
    const chips = renderChips({ settings: { ...staleSettings, settings_version: 2 } });

    expect(chips.model.textContent).toBe("openai/gpt-4o");
    expect(chips.wp.textContent).toBe("Oblast jedna");
    expect(chips.prompt.textContent).toBe("p1");
  });
});
