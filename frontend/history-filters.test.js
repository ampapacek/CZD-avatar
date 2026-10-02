import { describe, expect, it } from "vitest";

import {
  evictOldestFromLargestWp,
  facetOptions,
  filterHistory,
  groupHistory,
  periodStart,
  trimHistoryPerWp,
} from "./history-filters.js";

const facets = (item) => item;
const NOW = new Date(2026, 9, 2, 12, 0); // 2 Oct 2026, 12:00 local

const items = [
  { id: 1, wp: "wp1", author: "Ada", prompt: "Stručný", model: "gpt-oss-120b", time: new Date(2026, 9, 2, 9).toISOString(), text: "Husité a Žižka" },
  { id: 2, wp: "wp2", author: "Bob", prompt: "Podrobný", model: "gemma-4", time: new Date(2026, 9, 1, 9).toISOString(), text: "Média" },
  { id: 3, wp: "wp1", author: "Bob", prompt: "Stručný", model: "gemma-4", time: new Date(2026, 8, 20).toISOString(), text: "Karel IV." },
  { id: 4, wp: "wp1", author: "", prompt: "", model: "", time: "", text: "bez metadat" },
];
const ids = (list) => list.map((item) => item.id);

describe("filterHistory", () => {
  it("passes everything with no filters", () => {
    expect(ids(filterHistory(items, facets, {}, NOW))).toEqual([1, 2, 3, 4]);
  });

  it("combines WP, author, prompt and model filters", () => {
    expect(ids(filterHistory(items, facets, { wp: "wp1" }, NOW))).toEqual([1, 3, 4]);
    expect(ids(filterHistory(items, facets, { wp: "wp1", author: "Bob" }, NOW))).toEqual([3]);
    expect(ids(filterHistory(items, facets, { prompt: "Stručný", model: "gemma-4" }, NOW))).toEqual([3]);
  });

  it("searches text ignoring case and diacritics", () => {
    expect(ids(filterHistory(items, facets, { text: "HUSITE" }, NOW))).toEqual([1]);
    expect(ids(filterHistory(items, facets, { text: "  žižka " }, NOW))).toEqual([1]);
  });

  it("filters by period and drops entries without a time", () => {
    expect(ids(filterHistory(items, facets, { period: "today" }, NOW))).toEqual([1]);
    expect(ids(filterHistory(items, facets, { period: "7d" }, NOW))).toEqual([1, 2]);
    expect(ids(filterHistory(items, facets, { period: "30d" }, NOW))).toEqual([1, 2, 3]);
  });

  it("treats today as the local calendar day", () => {
    expect(periodStart("today", NOW)).toBe(new Date(2026, 9, 2).getTime());
    expect(periodStart("all", NOW)).toBeNull();
  });
});

describe("facetOptions", () => {
  it("lists distinct non-empty values alphabetically", () => {
    expect(facetOptions(items, facets, "author")).toEqual(["Ada", "Bob"]);
    expect(facetOptions(items, facets, "model")).toEqual(["gemma-4", "gpt-oss-120b"]);
  });
});

describe("groupHistory", () => {
  it("returns a single unlabelled group for none", () => {
    expect(groupHistory(items, facets, "none")).toEqual([{ key: "", label: "", items }]);
  });

  it("orders groups by their newest item and keeps item order", () => {
    const groups = groupHistory(items, facets, "author", { emptyLabel: "Bez autora" });
    expect(groups.map((group) => [group.label, ids(group.items)])).toEqual([
      ["Ada", [1]],
      ["Bob", [2, 3]],
      ["Bez autora", [4]],
    ]);
  });

  it("groups by day through the caller's label", () => {
    const groups = groupHistory(items.slice(0, 3), facets, "day", {
      dayLabel: (time) => new Date(time).getDate().toString(),
    });
    expect(groups.map((group) => group.label)).toEqual(["2", "1", "20"]);
  });
});

describe("per-WP history cap", () => {
  const wpOf = (entry) => entry.wp;
  const entries = [
    { id: 6, wp: "a" },
    { id: 5, wp: "b" },
    { id: 4, wp: "a" },
    { id: 3, wp: "a" },
    { id: 2, wp: "b" },
    { id: 1, wp: "a" },
  ];

  it("keeps the newest entries of each WP up to the cap", () => {
    expect(ids(trimHistoryPerWp(entries, 2, wpOf))).toEqual([6, 5, 4, 2]);
  });

  it("evicts the oldest entry of the largest WP, never the newest entry", () => {
    expect(ids(evictOldestFromLargestWp(entries, wpOf))).toEqual([6, 5, 4, 3, 2]);
    expect(ids(evictOldestFromLargestWp([{ id: 2, wp: "a" }, { id: 1, wp: "b" }], wpOf))).toEqual([2]);
    expect(evictOldestFromLargestWp([{ id: 1, wp: "a" }], wpOf)).toBeNull();
  });
});
