import { describe, expect, it } from "vitest";

import {
  browserHistoryNotice,
  browserHoldsHistory,
  defaultHistoryMode,
  entriesMissingOnServer,
  historyCountsText,
  historyImportText,
  historyUsageText,
  normalizeHistoryMode,
  PageHistoryStore,
  sortStoredEntries,
} from "./history-store.js";

function fakeServer(data = { history: [], conversations: [] }) {
  const calls = [];
  const request = async (method, url, body) => {
    calls.push([method, url, body]);
    if (method === "GET") {
      return data;
    }
    if (url.endsWith("/fail")) {
      const error = new Error("plná");
      error.status = 413;
      throw error;
    }
    return { usage: { entries: 1 } };
  };
  return { calls, request };
}

// Timers fire only when the test says so.
function manualTimer() {
  const queued = [];
  return {
    setTimer: (fn) => {
      queued.push(fn);
      return queued.length;
    },
    fire: () => queued.splice(0).forEach((fn) => fn()),
    get size() {
      return queued.length;
    },
  };
}

describe("PageHistoryStore", () => {
  it("keeps entries in memory only without a request function", () => {
    const store = new PageHistoryStore();
    store.save("history", [{ id: 1, question: "a" }]);
    expect(store.get("history")).toEqual([{ id: 1, question: "a" }]);
    expect(store.hasUnsavedChanges()).toBe(false);
  });

  it("hands out copies, so mutating them changes nothing until a save", () => {
    const store = new PageHistoryStore();
    store.save("history", [{ id: 1, note: "" }]);
    store.get("history")[0].note = "changed";
    expect(store.get("history")[0].note).toBe("");
  });

  it("sends only changed entries, once, after the delay", async () => {
    const server = fakeServer();
    const timer = manualTimer();
    const store = new PageHistoryStore({ request: server.request, setTimer: timer.setTimer });
    store.save("conversation", [{ id: 1, text: "a" }, { id: 2, text: "b" }]);
    store.save("conversation", [{ id: 1, text: "ab" }, { id: 2, text: "b" }]);
    store.save("conversation", [{ id: 1, text: "abc" }, { id: 2, text: "b" }]);
    expect(timer.size).toBe(1);
    timer.fire();
    await store.flush();
    expect(server.calls).toEqual([
      ["PUT", "me/history/conversations/1", { entry: { id: 1, text: "abc" } }],
      ["PUT", "me/history/conversations/2", { entry: { id: 2, text: "b" } }],
    ]);
    server.calls.length = 0;
    store.save("conversation", [{ id: 1, text: "abc" }]);
    timer.fire();
    await store.flush();
    expect(server.calls).toEqual([["DELETE", "me/history/conversations/2", undefined]]);
  });

  it("applies the compaction before storing and sending", async () => {
    const server = fakeServer();
    const store = new PageHistoryStore({ request: server.request, setTimer: () => 0 });
    const saved = store.save("history", [{ id: 5, big: "x" }], ({ big, ...rest }) => rest);
    expect(saved).toEqual([{ id: 5 }]);
    await store.flush();
    expect(server.calls[0][2]).toEqual({ entry: { id: 5 } });
  });

  it("reports a refused save and retries it on the next save", async () => {
    const server = fakeServer();
    const errors = [];
    const store = new PageHistoryStore({
      request: server.request,
      setTimer: () => 0,
      onError: (error) => errors.push(error.status),
    });
    store.save("history", [{ id: "fail" }]);
    await store.flush();
    expect(errors).toEqual([413]);
    expect(store.get("history")).toEqual([{ id: "fail" }]);
    expect(store.hasUnsavedChanges()).toBe(true);
    store.save("history", [{ id: "fail" }]);
    await store.flush();
    expect(server.calls.filter(([method]) => method === "PUT")).toHaveLength(2);
  });

  it("loads sorted lists and keeps entries made before the load", async () => {
    const server = fakeServer({
      history: [
        { id: 1, createdAt: "2026-11-01T10:00:00Z" },
        { id: 2, createdAt: "2026-11-03T10:00:00Z" },
      ],
      conversations: [],
      usage: { entries: 2 },
    });
    const usages = [];
    const store = new PageHistoryStore({ request: server.request, setTimer: () => 0, onUsage: (u) => usages.push(u) });
    store.items.history = [{ id: 3, json: JSON.stringify({ id: 3, createdAt: "2026-11-05T10:00:00Z" }) }];
    await store.load();
    expect(store.get("history").map((entry) => entry.id)).toEqual([3, 2, 1]);
    expect(usages).toEqual([{ entries: 2 }]);
    await store.flush();
    expect(server.calls.at(-1)[0]).toBe("PUT");
    expect(server.calls.at(-1)[1]).toBe("me/history/history/3");
  });
});

describe("helpers", () => {
  it("normalizes the mode", () => {
    expect(normalizeHistoryMode("none")).toBe("none");
    expect(normalizeHistoryMode("cloud")).toBe("server");
    expect(normalizeHistoryMode(undefined, "browser")).toBe("browser");
  });

  it("sorts conversations by their last change", () => {
    const sorted = sortStoredEntries("conversation", [
      { id: 1, updatedAt: "2026-11-01" },
      { id: 2, updatedAt: "2026-11-09" },
    ]);
    expect(sorted.map((entry) => entry.id)).toEqual([2, 1]);
  });

  it("finds browser entries the server lacks", () => {
    expect(entriesMissingOnServer([{ id: 1 }, { id: 2 }], [{ id: 1 }])).toEqual([{ id: 2 }]);
  });

  it("describes usage and an import", () => {
    expect(historyUsageText({ entries: 3, bytes: 2115, max_entries: 2000, max_bytes: 52428800 }))
      .toBe("Na serveru máš 3 kB z 50 MB, položek 3 z 2000.");
    expect(historyImportText({ imported: 2, existing: 1, over_limit: 0 }))
      .toBe("Nahráno: 2. Už na serveru, beze změny: 1.");
  });
});

describe("browser history before a choice", () => {
  const withMessages = { id: 7, messages: [{ role: "user", content: "a" }] };
  const empty = { id: 8, messages: [] };

  it("keeps a browser that holds history on the browser until the user chooses", () => {
    expect(defaultHistoryMode(null, browserHoldsHistory([], [withMessages]))).toBe("browser");
    expect(defaultHistoryMode(null, browserHoldsHistory([], [empty]))).toBe("server");
    expect(defaultHistoryMode("none", true)).toBe("none");
  });

  it("counts in Czech", () => {
    expect(historyCountsText(12, 3)).toBe("12 dotazů a 3 konverzace");
    expect(historyCountsText(1, 0)).toBe("1 dotaz");
    expect(historyCountsText(0, 1)).toBe("1 konverzaci");
    expect(historyCountsText(0, 0)).toBe("");
  });

  it("offers the server while nothing is chosen", () => {
    const notice = browserHistoryNotice({
      chosenMode: null,
      mode: "browser",
      browser: { history: [{ id: 1 }, { id: 2 }], conversations: [withMessages, empty] },
    });
    expect(notice.kind).toBe("choose");
    expect(notice.text).toMatch(/^V tomto prohlížeči máš 2 dotazy a 1 konverzaci\. Teď lze/);
    expect(browserHistoryNotice({ chosenMode: "browser", mode: "browser", browser: { history: [{ id: 1 }] } })).toBeNull();
  });

  it("offers an upload on the server until hidden", () => {
    const args = { chosenMode: "server", mode: "server", missing: { history: [{ id: 1 }], conversations: [] } };
    expect(browserHistoryNotice(args).kind).toBe("upload");
    expect(browserHistoryNotice({ ...args, uploadDismissed: true })).toBeNull();
    expect(browserHistoryNotice({ ...args, missing: { history: [], conversations: [empty] } })).toBeNull();
  });
});
