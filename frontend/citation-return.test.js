import { JSDOM } from "jsdom";
import { describe, expect, it, vi } from "vitest";

import { createCitationReturn, isInViewport } from "./citation-return.js";

const VIEWPORT = 800;

// jsdom has no layout: each marker gets a settable position, and an empty
// client-rect list stands for a marker hidden with display: none.
function placed(element, state) {
  element.getBoundingClientRect = () => ({ top: state.top, bottom: state.top + 20 });
  element.getClientRects = () => (state.hidden ? [] : [{}]);
  element.scrollIntoView = vi.fn();
  return element;
}

function setup(markup = `<p><a id="marker">1</a></p>`) {
  const { document } = new JSDOM(`<body>${markup}<button id="back" hidden>↑ Zpět k textu</button></body>`).window;
  const state = { top: 100, hidden: false };
  const marker = placed(document.querySelector("#marker"), state);
  const button = document.querySelector("#back");
  const controller = createCitationReturn({ button, viewportHeight: () => VIEWPORT });
  return { document, state, marker, button, controller };
}

describe("isInViewport", () => {
  it("counts any overlap with the screen as visible", () => {
    const element = { getBoundingClientRect: () => ({ top: -10, bottom: 5 }) };
    expect(isInViewport(element, VIEWPORT)).toBe(true);
    element.getBoundingClientRect = () => ({ top: VIEWPORT, bottom: VIEWPORT + 20 });
    expect(isInViewport(element, VIEWPORT)).toBe(false);
  });
});

describe("createCitationReturn", () => {
  it("shows the button only once the marker has scrolled away", () => {
    const { state, marker, button, controller } = setup();
    controller.arm(marker);
    expect(button.hidden).toBe(true);
    state.top = -400;
    controller.update();
    expect(button.hidden).toBe(false);
  });

  it("scrolls back to the marker and hides when used", () => {
    const { state, marker, button, controller } = setup();
    controller.arm(marker);
    state.top = -400;
    controller.update();
    controller.returnToMarker();
    expect(marker.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "center" });
    expect(button.hidden).toBe(true);
    expect(controller.marker).toBe(null);
  });

  it("goes away when the reader scrolls back to the marker by hand", () => {
    const { state, marker, button, controller } = setup();
    controller.arm(marker);
    state.top = -400;
    controller.update();
    state.top = 300;
    controller.update();
    expect(button.hidden).toBe(true);
    state.top = -400;
    controller.update();
    expect(button.hidden).toBe(true);
  });

  it("disarms when the marker is re-rendered away or hidden", () => {
    const { state, marker, button, controller } = setup();
    controller.arm(marker);
    state.top = -400;
    state.hidden = true;
    controller.update();
    expect(button.hidden).toBe(true);
    expect(controller.marker).toBe(null);

    const again = setup();
    again.controller.arm(again.marker);
    again.state.top = -400;
    again.marker.remove();
    again.controller.update();
    expect(again.button.hidden).toBe(true);
  });

  it("moves the button into the marker's dialog, which sits above the page", () => {
    const { document, state, marker, button, controller } = setup(
      `<dialog id="dialog" open><a id="marker">1</a></dialog>`,
    );
    const dialog = document.querySelector("#dialog");
    controller.arm(marker);
    expect(button.parentElement).toBe(dialog);
    state.top = -400;
    controller.update();
    expect(button.hidden).toBe(false);
    dialog.open = false;
    controller.update();
    expect(button.hidden).toBe(true);
  });
});
