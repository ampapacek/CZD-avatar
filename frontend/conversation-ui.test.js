import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

describe("conversation request UI", () => {
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
