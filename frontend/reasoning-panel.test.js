import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

import {
  captureReasoningPanels,
  isScrolledToBottom,
  restoreReasoningPanels,
  updateStreamingReasoning,
} from "./reasoning-panel.js";

// jsdom has no layout, so each element gets a fixed viewport and a content
// height that grows with its text.
function withLayout(element, { clientHeight = 100, lineHeight = 10 } = {}) {
  Object.defineProperty(element, "clientHeight", { configurable: true, get: () => clientHeight });
  Object.defineProperty(element, "scrollHeight", {
    configurable: true,
    get: () => Math.max(clientHeight, element.textContent.split("\n").length * lineHeight),
  });
  return element;
}

function lines(count) {
  return Array.from({ length: count }, (_, i) => `line ${i + 1}`).join("\n");
}

function livePanel() {
  const { document } = new JSDOM(
    `<details id="panel"><summary>Uvažování modelu</summary><pre id="text" class="reasoning-text"></pre></details>`,
  ).window;
  return { panel: document.querySelector("#panel"), text: withLayout(document.querySelector("#text")) };
}

function conversationList(messages) {
  const { document } = new JSDOM("<div id='list'></div>").window;
  const list = document.querySelector("#list");
  render(list, messages);
  return list;
}

function render(list, messages) {
  list.innerHTML = messages
    .map(
      (message, index) =>
        `<details class="reasoning-panel" data-reasoning-index="${index}" data-reasoning-streaming="${message.streaming ? "1" : "0"}"${message.streaming ? " open" : ""}>
          <summary>Uvažování modelu</summary><pre class="reasoning-text">${message.reasoning}</pre></details>`,
    )
    .join("");
  for (const text of list.querySelectorAll(".reasoning-text")) {
    withLayout(text);
  }
}

describe("isScrolledToBottom", () => {
  it("counts a near-bottom position as the bottom", () => {
    const el = { scrollHeight: 500, clientHeight: 100, scrollTop: 390 };
    expect(isScrolledToBottom(el)).toBe(true);
    expect(isScrolledToBottom({ ...el, scrollTop: 300 })).toBe(false);
  });

  it("treats a missing element as at the bottom", () => {
    expect(isScrolledToBottom(null)).toBe(true);
  });
});

describe("updateStreamingReasoning", () => {
  it("opens on the first text and follows new lines from the bottom", () => {
    const { panel, text } = livePanel();
    updateStreamingReasoning(panel, text, lines(5));
    expect(panel.open).toBe(true);
    updateStreamingReasoning(panel, text, lines(30));
    expect(text.scrollTop).toBe(text.scrollHeight);
  });

  it("leaves a reader who scrolled up where they are", () => {
    const { panel, text } = livePanel();
    updateStreamingReasoning(panel, text, lines(30));
    text.scrollTop = 0;
    updateStreamingReasoning(panel, text, lines(40));
    expect(text.scrollTop).toBe(0);
  });

  it("keeps a panel the reader folded folded", () => {
    const { panel, text } = livePanel();
    updateStreamingReasoning(panel, text, lines(3));
    panel.open = false;
    updateStreamingReasoning(panel, text, lines(4));
    expect(panel.open).toBe(false);
  });
});

describe("reasoning panels across a conversation re-render", () => {
  it("keeps the scroll position of a trace the reader scrolled up", () => {
    const list = conversationList([{ reasoning: lines(30), streaming: true }]);
    list.querySelector(".reasoning-text").scrollTop = 50;
    const states = captureReasoningPanels(list);
    render(list, [{ reasoning: lines(40), streaming: true }]);
    restoreReasoningPanels(list, states);
    expect(list.querySelector(".reasoning-text").scrollTop).toBe(50);
  });

  it("follows a streaming trace whose reader stayed at the bottom", () => {
    const list = conversationList([{ reasoning: lines(30), streaming: true }]);
    list.querySelector(".reasoning-text").scrollTop = 200;
    const states = captureReasoningPanels(list);
    render(list, [{ reasoning: lines(40), streaming: true }]);
    restoreReasoningPanels(list, states);
    // jsdom does not clamp scrollTop; a browser would stop at the last line.
    const text = list.querySelector(".reasoning-text");
    expect(text.scrollTop).toBe(text.scrollHeight);
  });

  it("keeps a fold while streaming, and folds once the answer starts", () => {
    const list = conversationList([{ reasoning: lines(3), streaming: true }]);
    list.querySelector("details").open = false;
    let states = captureReasoningPanels(list);
    render(list, [{ reasoning: lines(4), streaming: true }]);
    restoreReasoningPanels(list, states);
    expect(list.querySelector("details").open).toBe(false);

    list.querySelector("details").open = true;
    states = captureReasoningPanels(list);
    render(list, [{ reasoning: lines(4), streaming: false }]);
    restoreReasoningPanels(list, states);
    expect(list.querySelector("details").open).toBe(false);
  });

  it("keeps a finished trace the reader opened open", () => {
    const list = conversationList([{ reasoning: lines(3), streaming: false }]);
    list.querySelector("details").open = true;
    const states = captureReasoningPanels(list);
    render(list, [{ reasoning: lines(3), streaming: false }]);
    restoreReasoningPanels(list, states);
    expect(list.querySelector("details").open).toBe(true);
  });
});
