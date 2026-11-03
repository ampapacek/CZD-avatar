import { describe, expect, it } from "vitest";

import { cachedAnswerStatus, formatCachedAt, isCachedAnswer } from "./answer-cache.js";

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
