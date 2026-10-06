// A streaming reasoning trace grows for seconds before the answer starts, and
// the reader may scroll back to its beginning or fold it away meanwhile. These
// helpers keep both choices across updates: the trace follows its newest line
// only while the reader is already at the bottom, and a re-rendered panel
// keeps the open state and scroll position it had.

// A few pixels of slack: a reader who scrolled "to the bottom" by hand rarely
// lands on the exact last pixel, and sub-pixel layout rounds the other way.
export const SCROLL_BOTTOM_TOLERANCE_PX = 24;

export function isScrolledToBottom(element, tolerance = SCROLL_BOTTOM_TOLERANCE_PX) {
  if (!element) {
    return true;
  }
  return element.scrollHeight - element.clientHeight - element.scrollTop <= tolerance;
}

// Replaces the trace text of a live panel. The first text of a stream opens the
// panel; after that the reader owns it, so a fold stays folded. Scrolling
// follows new lines only from the bottom.
export function updateStreamingReasoning(panel, textElement, text) {
  const wasEmpty = !textElement.textContent;
  const follow = wasEmpty || isScrolledToBottom(textElement);
  const scrollTop = textElement.scrollTop;
  textElement.textContent = text;
  if (wasEmpty && text) {
    panel.open = true;
  }
  textElement.scrollTop = follow ? textElement.scrollHeight : scrollTop;
}

// Conversation bubbles are re-rendered as HTML on every streamed delta, which
// would rebuild each panel closed-or-open as the markup says and scrolled to
// the top. Panels carry `data-reasoning-index` (their message index) so their
// state can be carried over the re-render.
export function captureReasoningPanels(container) {
  const states = new Map();
  if (!container) {
    return states;
  }
  for (const panel of container.querySelectorAll("details[data-reasoning-index]")) {
    const text = panel.querySelector(".reasoning-text");
    states.set(panel.dataset.reasoningIndex, {
      open: panel.open,
      streaming: panel.dataset.reasoningStreaming === "1",
      scrollTop: text?.scrollTop ?? 0,
      atBottom: isScrolledToBottom(text),
    });
  }
  return states;
}

export function restoreReasoningPanels(container, states) {
  if (!container || !states?.size) {
    return;
  }
  for (const panel of container.querySelectorAll("details[data-reasoning-index]")) {
    const state = states.get(panel.dataset.reasoningIndex);
    if (!state) {
      continue;
    }
    const streaming = panel.dataset.reasoningStreaming === "1";
    // The one moment the markup wins: the answer has just started, and the
    // trace folds away as it does on the main page.
    if (!(state.streaming && !streaming)) {
      panel.open = state.open;
    }
    const text = panel.querySelector(".reasoning-text");
    if (text) {
      text.scrollTop = streaming && state.atBottom ? text.scrollHeight : state.scrollTop;
    }
  }
}
