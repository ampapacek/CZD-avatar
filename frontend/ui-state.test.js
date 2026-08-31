import { describe, expect, it } from "vitest";

import { nextTabIndex, sourcePanelPresentation, wpTopicLabel } from "./ui-state.js";

describe("sourcePanelPresentation", () => {
  it("hides the entire column when retrieval returns no sources", () => {
    expect(sourcePanelPresentation(0, false)).toMatchObject({
      panelHidden: true,
      bodyHidden: true,
      reopenHidden: true,
    });
  });

  it("opens non-empty sources with an accurate count", () => {
    expect(sourcePanelPresentation(6, false)).toMatchObject({
      panelHidden: false,
      bodyHidden: false,
      reopenHidden: true,
      label: "Zdroje (6)",
    });
  });

  it("collapses only presentation, retaining a clear reopen label", () => {
    expect(sourcePanelPresentation(6, true)).toMatchObject({
      panelHidden: false,
      bodyHidden: true,
      reopenHidden: false,
      isCollapsed: true,
      label: "Zdroje (6)",
    });
  });
});

describe("nextTabIndex", () => {
  it("wraps arrow navigation and supports Home and End", () => {
    expect(nextTabIndex(2, "ArrowRight", 3)).toBe(0);
    expect(nextTabIndex(0, "ArrowLeft", 3)).toBe(2);
    expect(nextTabIndex(1, "Home", 3)).toBe(0);
    expect(nextTabIndex(1, "End", 3)).toBe(2);
  });
});

describe("wpTopicLabel", () => {
  it("removes the technical WP prefix from the user-facing topic", () => {
    expect(wpTopicLabel("WP1 – Historie")).toBe("Historie");
    expect(wpTopicLabel("WP2-média")).toBe("média");
  });

  it("provides a grammatical fallback for a missing label", () => {
    expect(wpTopicLabel("")).toBe("vybranému v nabídce");
  });
});
