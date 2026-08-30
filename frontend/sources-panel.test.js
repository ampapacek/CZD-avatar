import { describe, expect, it } from "vitest";

import {
  CITATION_ORDER,
  RETRIEVED_ORDER,
  completedSourcesView,
  createSourcesView,
  extractOrderedCitationIds,
  layoutSources,
  sourceCardLabel,
  sourceScoreParts,
} from "./sources-panel.js";

const sources = ["Z1", "Z2", "Z3", "Z4"].map((citation_id, index) => ({
  citation_id,
  title: `Zdroj ${index + 1}`,
}));

function idsOf(entries) {
  return entries.map((entry) => entry.citationId);
}

describe("extractOrderedCitationIds", () => {
  it("returns first-appearance order without duplicates", () => {
    expect(extractOrderedCitationIds("a[^Z3] b[^Z1] c[^Z3] d[^Z2]")).toEqual(["Z3", "Z1", "Z2"]);
  });

  it("accepts both [^Zn] and [Zn] marker spellings", () => {
    expect(extractOrderedCitationIds("a[Z2] b[^Z1]")).toEqual(["Z2", "Z1"]);
  });

  it("ignores ids that only occur in a stripped footnote-definition block", () => {
    // The answer body never renders those lines, so they must not claim numbers.
    expect(extractOrderedCitationIds("Věta.[^Z1]\n\n[^Z1]: popis\n[^Z9]: vymyšlené")).toEqual(["Z1"]);
  });

  it("ignores ids after a model-written Použité zdroje heading", () => {
    expect(extractOrderedCitationIds("Věta.[^Z1]\n\n## Použité zdroje\n- [Z7] něco")).toEqual(["Z1"]);
  });

  it("is empty for text without markers", () => {
    expect(extractOrderedCitationIds("Odpověď bez citací.")).toEqual([]);
    expect(extractOrderedCitationIds("")).toEqual([]);
  });
});

describe("layout while the answer streams", () => {
  it("keeps retrieved order, every source visible, and no citation numbers", () => {
    const layout = layoutSources(sources, createSourcesView(), { orderedCitationIds: ["Z3"] });
    expect(idsOf(layout.visible)).toEqual(["Z1", "Z2", "Z3", "Z4"]);
    expect(layout.showCitationNumbers).toBe(false);
    expect(layout.hiddenCount).toBe(0);
  });

  it("shows the provisional-order notice and no toggles", () => {
    const layout = layoutSources(sources, createSourcesView(), { orderedCitationIds: ["Z3"] });
    expect(layout.showNotice).toBe(true);
    expect(layout.showOrderToggle).toBe(false);
    expect(layout.showUncitedToggle).toBe(false);
  });
});

describe("layout after the answer finishes", () => {
  const ordered = ["Z3", "Z1"];
  const view = completedSourcesView(createSourcesView(), ordered);

  it("flips to citation order and hides uncited sources", () => {
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    expect(view.order).toBe(CITATION_ORDER);
    expect(idsOf(layout.visible)).toEqual(["Z3", "Z1"]);
    expect(layout.hiddenCount).toBe(2);
    expect(layout.uncitedCount).toBe(2);
  });

  it("numbers cited cards the same way the answer numbers its superscripts", () => {
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    expect(layout.visible.map((entry) => entry.citationNumber)).toEqual([1, 2]);
    expect(layout.showCitationNumbers).toBe(true);
  });

  it("swaps the notice for the order toggle", () => {
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    expect(layout.showNotice).toBe(false);
    expect(layout.showOrderToggle).toBe(true);
    expect(layout.showUncitedToggle).toBe(true);
  });

  it("keeps the numbers when the user switches back to retrieved order", () => {
    const back = { ...view, order: RETRIEVED_ORDER };
    const layout = layoutSources(sources, back, { orderedCitationIds: ordered });
    expect(idsOf(layout.visible)).toEqual(["Z1", "Z2", "Z3", "Z4"]);
    expect(layout.visible.map((entry) => entry.citationNumber)).toEqual([2, null, 1, null]);
    // Relevance order shows the ranking whole, so there is nothing to collapse.
    expect(layout.hiddenCount).toBe(0);
    expect(layout.showUncitedToggle).toBe(false);
  });

  it("keeps the numbers when uncited sources are revealed", () => {
    const shown = { ...view, showUncited: true };
    const layout = layoutSources(sources, shown, { orderedCitationIds: ordered });
    expect(idsOf(layout.visible)).toEqual(["Z3", "Z1", "Z2", "Z4"]);
    expect(layout.hiddenCount).toBe(0);
    expect(layout.visible.map((entry) => entry.citationNumber)).toEqual([1, 2, null, null]);
  });
});

describe("cases where the flip must not happen", () => {
  it("stays in retrieved order for an aborted or errored stream", () => {
    // The stream never completes, so the view state is never marked complete.
    const layout = layoutSources(sources, createSourcesView(), { orderedCitationIds: ["Z3", "Z1"] });
    expect(idsOf(layout.visible)).toEqual(["Z1", "Z2", "Z3", "Z4"]);
    expect(layout.showCitationNumbers).toBe(false);
  });

  it("stays in retrieved order in retrieve-only mode, with no notice", () => {
    const view = completedSourcesView(createSourcesView({ canFlip: false }), []);
    const layout = layoutSources(sources, view, { orderedCitationIds: [] });
    expect(view.order).toBe(RETRIEVED_ORDER);
    expect(idsOf(layout.visible)).toEqual(["Z1", "Z2", "Z3", "Z4"]);
    expect(layout.showNotice).toBe(false);
    expect(layout.showOrderToggle).toBe(false);
    expect(layout.showNoCitationsNotice).toBe(false);
  });

  it("does not flip when the answer cites nothing, and says so", () => {
    const view = completedSourcesView(createSourcesView(), []);
    const layout = layoutSources(sources, view, { orderedCitationIds: [] });
    expect(view.order).toBe(RETRIEVED_ORDER);
    expect(idsOf(layout.visible)).toEqual(["Z1", "Z2", "Z3", "Z4"]);
    expect(layout.showNoCitationsNotice).toBe(true);
    expect(layout.showUncitedToggle).toBe(false);
  });
});

describe("edge cases", () => {
  it("hides the uncited control when every source is cited", () => {
    const ordered = ["Z4", "Z3", "Z2", "Z1"];
    const view = completedSourcesView(createSourcesView(), ordered);
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    expect(layout.showUncitedToggle).toBe(false);
    expect(layout.uncitedCount).toBe(0);
    expect(idsOf(layout.visible)).toEqual(ordered);
  });

  it("ignores a citation of an id that was never retrieved", () => {
    const ordered = ["Z9", "Z2"];
    const view = completedSourcesView(createSourcesView(), ordered);
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    // Z9 is unknown, so Z2 is citation number 1 — matching the answer, where the
    // markdown plugin renders [Z9] as literal text rather than a superscript.
    expect(layout.visible.map((entry) => [entry.citationId, entry.citationNumber])).toEqual([["Z2", 1]]);
  });

  it("marks budget-omitted sources so they can carry their own badge", () => {
    const ordered = ["Z1"];
    const view = completedSourcesView(createSourcesView(), ordered);
    const layout = layoutSources(sources, { ...view, showUncited: true }, {
      orderedCitationIds: ordered,
      omittedCitationIds: ["Z4"],
    });
    const omitted = layout.entries.filter((entry) => entry.omitted).map((entry) => entry.citationId);
    expect(omitted).toEqual(["Z4"]);
  });

  it("survives an empty source list", () => {
    const layout = layoutSources([], createSourcesView(), { orderedCitationIds: [] });
    expect(layout.visible).toEqual([]);
    expect(layout.showNoCitationsNotice).toBe(false);
  });
});

describe("sourceCardLabel", () => {
  it("shows the citation number alone for a cited card", () => {
    // The retrieval id moved to the diagnostics line; the title keeps the number
    // the answer superscripts.
    expect(sourceCardLabel({ cited: true, citationNumber: 2, citationId: "Z7" }, true)).toBe("[2]");
  });

  it("labels an uncited card with nothing", () => {
    expect(sourceCardLabel({ cited: false, citationNumber: null, citationId: "Z7" }, true)).toBe("");
  });

  it("labels nothing before the answer settles and numbers exist", () => {
    expect(sourceCardLabel({ cited: true, citationNumber: 1, citationId: "Z7" }, false)).toBe("");
  });
});

describe("highlightCited", () => {
  it("is on while cited and uncited cards are visible together", () => {
    const ordered = ["Z3", "Z1"];
    const view = { ...completedSourcesView(createSourcesView(), ordered), showUncited: true };
    expect(layoutSources(sources, view, { orderedCitationIds: ordered }).highlightCited).toBe(true);
  });

  it("is off once the settled panel hides the uncited sources", () => {
    // Every visible card is then cited, so the green would distinguish nothing.
    const ordered = ["Z3", "Z1"];
    const view = completedSourcesView(createSourcesView(), ordered);
    const layout = layoutSources(sources, view, { orderedCitationIds: ordered });
    expect(layout.visible.every((entry) => entry.cited)).toBe(true);
    expect(layout.highlightCited).toBe(false);
  });

  it("is off when the answer cites every retrieved source", () => {
    const ordered = ["Z1", "Z2", "Z3", "Z4"];
    const view = completedSourcesView(createSourcesView(), ordered);
    expect(layoutSources(sources, view, { orderedCitationIds: ordered }).highlightCited).toBe(false);
  });

  it("is off when the answer cites nothing", () => {
    const view = completedSourcesView(createSourcesView(), []);
    expect(layoutSources(sources, view, { orderedCitationIds: [] }).highlightCited).toBe(false);
  });

  it("is on while the answer streams and only some sources are cited", () => {
    const layout = layoutSources(sources, createSourcesView(), { orderedCitationIds: ["Z3"] });
    expect(layout.highlightCited).toBe(true);
  });

  it("is off for an empty panel", () => {
    expect(layoutSources([], createSourcesView(), {}).highlightCited).toBe(false);
  });
});

describe("sourceScoreParts", () => {
  it("keeps all three numbers for local hybrid retrieval", () => {
    // Both channels are always set locally (0.0 for a channel that missed), and
    // `score` is their weighted blend, so the three numbers say three things.
    expect(sourceScoreParts({ score: 0.48 }, { dense_score: 0.61, bm25_score: 0.22 })).toEqual([
      "score 0.48",
      "emb 0.61",
      "BM25 0.22",
    ]);
  });

  it("keeps the numbers when one local channel missed the document", () => {
    expect(sourceScoreParts({ score: 0.43 }, { dense_score: 0.61, bm25_score: 0 })).toEqual([
      "score 0.43",
      "emb 0.61",
      "BM25 0.00",
    ]);
  });

  it("names the channel for an mSearch semantic hit instead of repeating the score", () => {
    expect(sourceScoreParts({ score: 0.53 }, { dense_score: 0.53, bm25_score: null })).toEqual([
      "score 0.53",
      "sémanticky",
    ]);
  });

  it("names the channel for an mSearch keyword hit", () => {
    expect(sourceScoreParts({ score: 0.53 }, { dense_score: null, bm25_score: 0.53 })).toEqual([
      "score 0.53",
      "klíčová slova",
    ]);
  });

  it("still prints a lone component that differs from the score", () => {
    expect(sourceScoreParts({ score: 0.4 }, { dense_score: 0.53, bm25_score: null })).toEqual([
      "score 0.40",
      "emb 0.53",
    ]);
  });

  it("survives a missing chunk and a missing score", () => {
    expect(sourceScoreParts({ score: 0.53 }, undefined)).toEqual(["score 0.53"]);
    expect(sourceScoreParts({}, { dense_score: 0.61, bm25_score: 0.22 })).toEqual([
      "score",
      "emb 0.61",
      "BM25 0.22",
    ]);
  });
});
