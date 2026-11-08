// History and conversations when they do not live in the browser's
// localStorage: on the server, per account ("na serveru"), or only in this
// page until it closes ("neukládat"). The browser mode keeps its own code in
// app.js (quota handling, storage dialog); this store covers the other two.
//
// The page keeps a working copy in memory, so app.js can keep reading and
// writing whole lists synchronously. With a `request` function, every save is
// diffed against that copy and only the changed entries are sent, one request
// per entry, a little later: a conversation rewritten on every streamed token
// becomes one PUT once the stream pauses, not hundreds.

export const HISTORY_MODES = ["server", "browser", "none"];

export const HISTORY_MODE_LABELS = {
  server: "Na serveru",
  browser: "Jen v tomto prohlížeči",
  none: "Neukládat",
};

// The account line: "Historie se ukládá: …".
export const HISTORY_MODE_SHORT = {
  server: "na serveru",
  browser: "jen v tomto prohlížeči",
  none: "neukládá se",
};

export const HISTORY_MODE_NOTES = {
  server: "U tvého účtu. Uvidíš ji na každém zařízení, kde se přihlásíš.",
  browser: "Jen v tomto prohlížeči, jako bez účtu. Na jiném zařízení ji neuvidíš.",
  none: "Historie a konverzace vydrží jen do zavření nebo obnovení stránky. Odpovědi se neukládají ani do sdílené mezipaměti.",
};

const PATH_BY_KIND = { history: "history", conversation: "conversations" };

export function normalizeHistoryMode(mode, fallback = "server") {
  return HISTORY_MODES.includes(mode) ? mode : fallback;
}

// The server returns entries in no particular order. History is newest first
// by creation, conversations by their last change, as the browser keeps them.
export function sortStoredEntries(kind, entries) {
  const stamp = kind === "conversation"
    ? (entry) => String(entry?.updatedAt || entry?.createdAt || "")
    : (entry) => String(entry?.createdAt || "");
  return [...(entries || [])].sort(
    (a, b) => stamp(b).localeCompare(stamp(a)) || Number(b?.id || 0) - Number(a?.id || 0),
  );
}

// Browser entries the server does not have yet (matched by id).
export function entriesMissingOnServer(browserEntries, serverEntries) {
  const known = new Set((serverEntries || []).map((entry) => String(entry?.id)));
  return (browserEntries || []).filter((entry) => entry && entry.id !== undefined && !known.has(String(entry.id)));
}

export function historyUsageText(usage) {
  if (!usage || !usage.max_entries) {
    return "";
  }
  const size = (bytes) => bytes < 1024 * 1024
    ? `${Math.ceil(bytes / 1024)} kB`
    : `${(bytes / (1024 * 1024)).toLocaleString("cs-CZ", { maximumFractionDigits: 1 })} MB`;
  return `Na serveru máš ${size(usage.bytes)} z ${size(usage.max_bytes)}, položek ${usage.entries} z ${usage.max_entries}.`;
}

export function historyImportText(result) {
  // "Nahráno: 3." avoids Czech number agreement ("1 položka", "2 položky", "5 položek").
  const parts = [`Nahráno: ${result.imported || 0}.`];
  if (result.existing) {
    parts.push(`Už na serveru, beze změny: ${result.existing}.`);
  }
  if (result.over_limit) {
    parts.push(`Nevešlo se pod limit historie na serveru: ${result.over_limit}.`);
  }
  return parts.join(" ");
}

export class PageHistoryStore {
  // request(method, url, body) -> Promise of the parsed JSON; it rejects with
  // an Error carrying `status`. Without it, nothing leaves the page.
  constructor({
    request = null,
    onError = () => {},
    onSaved = () => {},
    onUsage = () => {},
    delayMs = 400,
    // Wrapped: a bare setTimeout called as this.setTimer() throws "Illegal invocation".
    setTimer = (fn, ms) => setTimeout(fn, ms),
  } = {}) {
    this.request = request;
    this.onError = onError;
    this.onSaved = onSaved;
    this.onUsage = onUsage;
    this.delayMs = delayMs;
    this.setTimer = setTimer;
    // kind -> [{ id, json }]: entries kept as JSON, so a caller mutating what
    // get() returned never changes the copy without a save.
    this.items = { history: [], conversation: [] };
    // "kind:id" -> { kind, id, json | null }; null deletes.
    this.pending = new Map();
    // "kind:id" whose last send failed: the next save sends it again.
    this.unsynced = new Set();
    this.timer = null;
    this.flushing = null;
    this.loaded = false;
  }

  get(kind) {
    return this.items[kind].map((item) => JSON.parse(item.json));
  }

  save(kind, entries, compact = (entry) => entry) {
    const next = (Array.isArray(entries) ? entries : []).map((entry) => {
      const stored = compact(entry);
      return { id: stored.id, json: JSON.stringify(stored) };
    });
    const before = new Map(this.items[kind].map((item) => [String(item.id), item.json]));
    this.items[kind] = next;
    if (this.request) {
      const seen = new Set();
      for (const item of next) {
        const id = String(item.id);
        seen.add(id);
        if (before.get(id) !== item.json || this.unsynced.has(`${kind}:${id}`)) {
          this.queue(kind, id, item.json);
        }
      }
      for (const id of before.keys()) {
        if (!seen.has(id)) {
          this.queue(kind, id, null);
        }
      }
    }
    return this.get(kind);
  }

  // Loads the server's lists. Entries this page made before (while the mode was
  // still unknown) are kept and sent, so nothing typed meanwhile is lost.
  async load() {
    const data = await this.request("GET", "me/history");
    for (const [kind, key] of [["history", "history"], ["conversation", "conversations"]]) {
      const server = sortStoredEntries(kind, data?.[key]);
      const local = entriesMissingOnServer(this.get(kind), server);
      const merged = sortStoredEntries(kind, [...local, ...server]);
      this.items[kind] = merged.map((entry) => ({ id: entry.id, json: JSON.stringify(entry) }));
      for (const entry of local) {
        this.queue(kind, String(entry.id), JSON.stringify(entry));
      }
    }
    this.loaded = true;
    if (data?.usage) {
      this.onUsage(data.usage);
    }
    return data;
  }

  queue(kind, id, json) {
    this.pending.set(`${kind}:${id}`, { kind, id, json });
    if (!this.timer && !this.flushing) {
      this.timer = this.setTimer(() => {
        this.timer = null;
        this.flush();
      }, this.delayMs);
    }
  }

  // Sends what is queued, one request at a time, and returns once the queue
  // is empty. A failure is reported and the entry retried on its next save.
  async flush() {
    if (this.flushing) {
      return this.flushing;
    }
    this.flushing = (async () => {
      while (this.pending.size) {
        const batch = [...this.pending.values()];
        this.pending.clear();
        for (const { kind, id, json } of batch) {
          const key = `${kind}:${id}`;
          const url = `me/history/${PATH_BY_KIND[kind]}/${encodeURIComponent(id)}`;
          try {
            const data = json === null
              ? await this.request("DELETE", url)
              : await this.request("PUT", url, { entry: JSON.parse(json) });
            this.unsynced.delete(key);
            this.onSaved({ kind, id, deleted: json === null });
            if (data?.usage) {
              this.onUsage(data.usage);
            }
          } catch (error) {
            if (json !== null) {
              this.unsynced.add(key);
            }
            this.onError(error, { kind, id, deleted: json === null });
          }
        }
      }
    })();
    try {
      await this.flushing;
    } finally {
      this.flushing = null;
      // Queued between the loop's last check and here: send it as usual.
      if (this.pending.size && !this.timer) {
        this.timer = this.setTimer(() => {
          this.timer = null;
          this.flush();
        }, this.delayMs);
      }
    }
  }

  hasUnsavedChanges() {
    return this.pending.size > 0 || this.unsynced.size > 0 || Boolean(this.flushing);
  }
}

// Conversations that hold at least one message. An empty "Nová konverzace" is
// made automatically whenever the list is empty, so it is not history.
export function conversationsWithMessages(conversations) {
  return (conversations || []).filter((entry) => Array.isArray(entry?.messages) && entry.messages.length > 0);
}

export function browserHoldsHistory(history, conversations) {
  return (history || []).length > 0 || conversationsWithMessages(conversations).length > 0;
}

// Before the user chooses, a browser that already holds history keeps showing
// it ("browser"); only a browser with nothing in it starts on the server.
export function defaultHistoryMode(chosenMode, holdsHistory) {
  if (HISTORY_MODES.includes(chosenMode)) {
    return chosenMode;
  }
  return holdsHistory ? "browser" : "server";
}

function czechCount(count, [one, few, many]) {
  if (count === 1) {
    return `${count} ${one}`;
  }
  return `${count} ${count >= 2 && count <= 4 ? few : many}`;
}

// "12 dotazů a 3 konverzace" (accusative, after "máš").
export function historyCountsText(historyCount, conversationCount) {
  const parts = [];
  if (historyCount) {
    parts.push(czechCount(historyCount, ["dotaz", "dotazy", "dotazů"]));
  }
  if (conversationCount) {
    parts.push(czechCount(conversationCount, ["konverzaci", "konverzace", "konverzací"]));
  }
  return parts.join(" a ");
}

// The notice above "Moje historie" about history in this browser, or null.
// `choose`: the user has not picked a mode and this browser holds history, so
// it is shown from the browser; offer the server. `upload`: the server copy is
// shown and the browser holds entries the server lacks.
export function browserHistoryNotice({ chosenMode, mode, browser, missing, uploadDismissed = false }) {
  if (mode === "browser" && !chosenMode) {
    const counts = historyCountsText(
      (browser?.history || []).length,
      conversationsWithMessages(browser?.conversations).length,
    );
    if (!counts) {
      return null;
    }
    return {
      kind: "choose",
      text: `V tomto prohlížeči máš ${counts}. Teď lze historii ukládat na server místo prohlížeče. Díky tomu není vázaná na konkrétní prohlížeč a uvidíš ji všude, kde se přihlásíš.`,
      primary: "Ukládat na server",
      secondary: "Nechat v prohlížeči",
    };
  }
  if (mode === "server" && !uploadDismissed) {
    const counts = historyCountsText(
      (missing?.history || []).length,
      conversationsWithMessages(missing?.conversations).length,
    );
    if (!counts) {
      return null;
    }
    return {
      kind: "upload",
      text: `V tomto prohlížeči máš ještě ${counts}, které nejsou na serveru. Nahráním se přidají k historii na serveru.`,
      primary: "Nahrát na server",
      secondary: "Skrýt",
    };
  }
  return null;
}
