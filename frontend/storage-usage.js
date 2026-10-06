// How full the browser's localStorage is, and the pure list transforms the
// "free up space" dialog offers. Nothing here touches the DOM or storage: the
// caller measures, previews the savings with these, and only then writes.

// localStorage holds ~5 million UTF-16 characters per origin in the browsers we
// care about, i.e. 5 MiB counted at two bytes a character. There is no API for
// "bytes left", so this is an assumed budget, not a measured one.
export const STORAGE_BUDGET_BYTES = 5 * 1024 * 1024;
export const STORAGE_WARN_FRACTION = 0.8;
export const STORAGE_CRITICAL_FRACTION = 0.95;

export function textBytes(value) {
  return String(value ?? "").length * 2;
}

export function jsonBytes(value) {
  try {
    return (JSON.stringify(value) || "").length * 2;
  } catch {
    return 0;
  }
}

export function storagePressure(usedBytes, budget = STORAGE_BUDGET_BYTES) {
  const fraction = budget > 0 ? usedBytes / budget : 0;
  if (fraction >= STORAGE_CRITICAL_FRACTION) {
    return "critical";
  }
  return fraction >= STORAGE_WARN_FRACTION ? "warn" : "ok";
}

function sumBytes(items, pick) {
  return items.reduce((total, item) => total + pick(item), 0);
}

// Where a history list's bytes go. `shared` counts entries that also exist on
// the server, so their local copy is the one that can go.
export function historyBreakdown(entries) {
  const list = Array.isArray(entries) ? entries : [];
  const total = jsonBytes(list);
  const reasoning = sumBytes(list, (entry) => textBytes(entry?.reasoning));
  const answers = sumBytes(list, (entry) => textBytes(entry?.answer));
  const sources = sumBytes(
    list,
    (entry) =>
      jsonBytes(entry?.retrieved_chunks || []) +
      jsonBytes(entry?.omitted_chunks || []) +
      jsonBytes(entry?.sources || []),
  );
  const sharedEntries = list.filter((entry) => entry?.shared_id);
  return {
    count: list.length,
    total,
    reasoning,
    answers,
    sources,
    other: Math.max(0, total - reasoning - answers - sources),
    sharedCount: sharedEntries.length,
    sharedBytes: jsonBytes(sharedEntries),
  };
}

export function conversationBreakdown(entries) {
  const list = Array.isArray(entries) ? entries : [];
  const total = jsonBytes(list);
  const messages = list.flatMap((entry) => (Array.isArray(entry?.messages) ? entry.messages : []));
  const reasoning = sumBytes(messages, (message) => textBytes(message?.reasoning));
  const text = sumBytes(messages, (message) => textBytes(message?.content));
  const sources = sumBytes(messages, (message) => jsonBytes(message?.retrieved_chunks || []));
  return {
    count: list.length,
    total,
    reasoning,
    text,
    sources,
    other: Math.max(0, total - reasoning - text - sources),
  };
}

// Lists are newest-first. Everything below returns a new list.

// Keep the reasoning of the newest `keepNewest` entries, drop the rest.
export function stripHistoryReasoning(entries, keepNewest = 0) {
  const keep = Math.max(0, Math.floor(Number(keepNewest) || 0));
  return entries.map((entry, index) =>
    index < keep || !entry?.reasoning ? entry : { ...entry, reasoning: "" },
  );
}

export function stripConversationReasoning(conversations, keepNewest = 0) {
  const keep = Math.max(0, Math.floor(Number(keepNewest) || 0));
  return conversations.map((conversation, index) => {
    const messages = Array.isArray(conversation?.messages) ? conversation.messages : [];
    if (index < keep || !messages.some((message) => message?.reasoning)) {
      return conversation;
    }
    return {
      ...conversation,
      messages: messages.map((message) => (message?.reasoning ? { ...message, reasoning: "" } : message)),
    };
  });
}

export function withoutSharedEntries(entries) {
  return entries.filter((entry) => !entry?.shared_id);
}

export function dropOldest(entries, count) {
  const drop = Math.max(0, Math.floor(Number(count) || 0));
  return drop ? entries.slice(0, Math.max(0, entries.length - drop)) : entries;
}

export function dropByIds(entries, ids) {
  const doomed = new Set(ids);
  return entries.filter((entry) => !doomed.has(entry?.id));
}

export function bytesFreed(before, after) {
  return Math.max(0, jsonBytes(before) - jsonBytes(after));
}

// Largest first, for the manual-delete list.
export function rankBySize(rows) {
  return [...rows].sort((a, b) => b.bytes - a.bytes);
}

export function formatMiB(bytes) {
  const mib = bytes / (1024 * 1024);
  return `${mib >= 10 ? mib.toFixed(0) : mib.toFixed(2)} MiB`;
}
