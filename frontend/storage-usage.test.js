import { describe, expect, it } from "vitest";

import {
  STORAGE_BUDGET_BYTES,
  bytesFreed,
  conversationBreakdown,
  dropByIds,
  dropOldest,
  historyBreakdown,
  rankBySize,
  storagePressure,
  stripConversationReasoning,
  stripHistoryReasoning,
  withoutSharedEntries,
} from "./storage-usage.js";

const entry = (id, extra = {}) => ({ id, answer: "a".repeat(10), reasoning: "r".repeat(100), ...extra });

describe("storagePressure", () => {
  it("warns at 80% and turns critical at 95% of the budget", () => {
    expect(storagePressure(STORAGE_BUDGET_BYTES * 0.79)).toBe("ok");
    expect(storagePressure(STORAGE_BUDGET_BYTES * 0.8)).toBe("warn");
    expect(storagePressure(STORAGE_BUDGET_BYTES * 0.95)).toBe("critical");
  });
});

describe("historyBreakdown", () => {
  it("splits reasoning, answers and shared entries", () => {
    const result = historyBreakdown([entry(2, { shared_id: "s" }), entry(1)]);
    expect(result.count).toBe(2);
    expect(result.reasoning).toBe(400);
    expect(result.answers).toBe(40);
    expect(result.sharedCount).toBe(1);
    expect(result.sharedBytes).toBeGreaterThan(0);
    expect(result.total).toBeGreaterThan(result.reasoning + result.answers);
  });
});

describe("conversationBreakdown", () => {
  it("counts reasoning on assistant messages", () => {
    const result = conversationBreakdown([
      { id: 1, messages: [{ role: "user", content: "q" }, { role: "assistant", content: "a", reasoning: "think" }] },
    ]);
    expect(result.count).toBe(1);
    expect(result.reasoning).toBe(10);
    expect(result.text).toBe(4);
  });
});

describe("free-up transforms", () => {
  it("keeps reasoning on the newest N entries only", () => {
    const stripped = stripHistoryReasoning([entry(3), entry(2), entry(1)], 1);
    expect(stripped.map((item) => item.reasoning.length)).toEqual([100, 0, 0]);
    expect(stripHistoryReasoning([entry(1)], 0)[0].reasoning).toBe("");
  });

  it("does not mutate its input", () => {
    const list = [entry(1)];
    stripHistoryReasoning(list, 0);
    expect(list[0].reasoning).toHaveLength(100);
  });

  it("strips conversation reasoning beyond the newest N", () => {
    const conversation = (id) => ({ id, messages: [{ role: "assistant", content: "a", reasoning: "x" }] });
    const stripped = stripConversationReasoning([conversation(2), conversation(1)], 1);
    expect(stripped[0].messages[0].reasoning).toBe("x");
    expect(stripped[1].messages[0].reasoning).toBe("");
  });

  it("drops shared entries, the oldest N and chosen ids", () => {
    const list = [entry(3, { shared_id: "s" }), entry(2), entry(1)];
    expect(withoutSharedEntries(list).map((item) => item.id)).toEqual([2, 1]);
    expect(dropOldest(list, 2).map((item) => item.id)).toEqual([3]);
    expect(dropOldest(list, 9)).toEqual([]);
    expect(dropOldest(list, 0)).toBe(list);
    expect(dropByIds(list, [2]).map((item) => item.id)).toEqual([3, 1]);
  });

  it("reports the bytes a transform frees", () => {
    const list = [entry(1)];
    expect(bytesFreed(list, stripHistoryReasoning(list, 0))).toBe(200);
    expect(bytesFreed(list, list)).toBe(0);
  });

  it("ranks rows largest first", () => {
    expect(rankBySize([{ bytes: 1 }, { bytes: 9 }, { bytes: 5 }]).map((row) => row.bytes)).toEqual([9, 5, 1]);
  });
});
