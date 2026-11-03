import { describe, expect, it } from "vitest";

import {
  cacheFilterBody,
  cacheFilterQuery,
  cacheProfileLabel,
  cacheSettingsSummary,
  cacheStatsText,
  cacheWarmBody,
  cacheWarmStatusText,
  cachedAnswerStatus,
  formatBytes,
  formatCachedAt,
  isCachedAnswer,
} from "./answer-cache.js";

// 2026-11-03 16:23:19 UTC
const cachedAt = 1793722999.77;

describe("answer cache labels", () => {
  it("recognises only an explicit hit", () => {
    expect(isCachedAnswer({ cache_hit: true })).toBe(true);
    expect(isCachedAnswer({ cache_hit: false })).toBe(false);
    expect(isCachedAnswer({})).toBe(false);
    expect(isCachedAnswer(null)).toBe(false);
  });

  it("formats the time it was generated", () => {
    expect(formatCachedAt(cachedAt, "Europe/Prague")).toBe("3. 11. 2026 17:23");
    expect(formatCachedAt(null)).toBe("");
    expect(formatCachedAt("nonsense")).toBe("");
  });

  it("builds the status line", () => {
    expect(cachedAnswerStatus({ cached_at: cachedAt }, "gpt-oss-120b", "Europe/Prague")).toBe(
      "Odpověď z mezipaměti (vygenerováno 3. 11. 2026 17:23) · gpt-oss-120b",
    );
    expect(cachedAnswerStatus({})).toBe("Odpověď z mezipaměti");
  });
});

describe("admin Cache dialog", () => {
  it("formats sizes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1536)).toBe("1,5 kB");
    expect(formatBytes(25 * 1024 * 1024)).toBe("25 MB");
    expect(formatBytes(undefined)).toBe("");
  });

  it("turns the filter into a query and a delete body", () => {
    const filter = { wp_id: "WP1", pinned: "false", stale: "", q: "  Hus " };
    expect(cacheFilterQuery(filter)).toBe("wp_id=WP1&pinned=false&q=Hus");
    expect(cacheFilterQuery({})).toBe("");
    expect(cacheFilterBody(filter)).toEqual({ wp_id: "WP1", pinned: false, stale: null, q: "Hus" });
    expect(cacheFilterBody({ stale: "true" })).toEqual({ wp_id: null, pinned: null, stale: true, q: null });
  });

  it("summarises the stats and how much the filter shows", () => {
    const stats = { entries: 3, pinned: 1, stale: 0, hits: 7, size_bytes: 2048, ttl_days: 14, max_entries: 10000 };
    expect(cacheStatsText(stats, 3, 3)).toBe(
      "3 odpovědí · 1 připnutých · 0 starých · 7 použití · 2 kB · nepřipnuté vyprší po 14 dnech, nejvýš 10000 nepřipnutých",
    );
    expect(cacheStatsText(stats, 2, 2)).toMatch(/Filtru odpovídá 2\.$/);
    expect(cacheStatsText(stats, 3, 1)).toMatch(/Filtru odpovídá 3, zobrazeno prvních 1\.$/);
    expect(cacheStatsText(null, 0, 0)).toBe("");
  });

  it("labels the profile and the settings", () => {
    expect(cacheProfileLabel({ prompt_preset_id: "x", prompt_preset_name: "Učitel" })).toBe("Učitel");
    expect(cacheProfileLabel({ prompt_preset_id: "local-1" })).toBe("local-1");
    expect(cacheProfileLabel({})).toBe("—");
    expect(cacheSettingsSummary({
      wp_id: "WP1", llm_provider: "aiufal", model: "m", reasoning_effort: null, output_length: "medium",
      retrieval_backend: "msearch", msearch_collection: "c1", msearch_mode: "hybrid", top_k: 10, context_window_tokens: 32000,
    })).toBe("WP: WP1 · Model: aiufal / m · Délka: medium · Vyhledávání: c1, hybrid · Počet zdrojů: 10 · Context window: 32000");
  });

  it("builds the warm request from the form", () => {
    expect(cacheWarmBody({
      wp: "WP1", questions: "custom", custom: " A?\n\n B? \n", profile: "all", provider: "aiufal",
      models: ["m1", "m2"], force: true, concurrency: "8",
    }, { dryRun: true })).toEqual({
      wp: ["WP1"], questions: ["A?", "B?"], profile: ["all"], provider: "aiufal",
      model: ["m1", "m2"], force: true, concurrency: 8, dry_run: true,
    });
    expect(cacheWarmBody({ questions: "prepared", custom: "ignored", concurrency: "" })).toEqual({
      wp: ["all"], questions: "prepared", profile: ["default"], provider: null,
      model: [], force: false, concurrency: 4, dry_run: false,
    });
    expect(cacheWarmBody({ concurrency: "50" }).concurrency).toBe(20);
    expect(cacheWarmBody({ concurrency: "0" }).concurrency).toBe(1);
    expect(cacheWarmBody({ concurrency: "x" }).concurrency).toBe(4);
  });

  it("describes the warming run", () => {
    const counts = { total: 10, done: 4, generated: 2, cached: 1, failed: 1 };
    expect(cacheWarmStatusText({ state: "idle" })).toBe("");
    expect(cacheWarmStatusText({ ...counts, state: "running", running: 2, pending: 4 }))
      .toBe("Běží 2, čeká 4 · 4 / 10 · vygenerováno 2 · už v cache 1 · chyby 1");
    expect(cacheWarmStatusText({ ...counts, state: "running", cancelled: true, running: 2, pending: 0 }))
      .toMatch(/^Ruším, dobíhá 2 · /);
    expect(cacheWarmStatusText({ ...counts, state: "cancelled" })).toMatch(/^Zrušeno · 4 \/ 10/);
    expect(cacheWarmStatusText({ ...counts, done: 10, state: "finished" })).toMatch(/^Hotovo · 10 \/ 10/);
  });
});
