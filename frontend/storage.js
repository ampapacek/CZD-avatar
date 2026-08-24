const REQUEST_ONLY_SETTINGS_FIELDS = new Set([
  "question",
  "conversation_history",
  "conversation_summary",
]);

export function storedAssistantSettings(settings) {
  if (!settings || typeof settings !== "object") {
    return settings || {};
  }
  return Object.fromEntries(
    Object.entries(settings).filter(([key]) => !REQUEST_ONLY_SETTINGS_FIELDS.has(key)),
  );
}

export function compactConversationForStorage(entry, { chunkTextLimit = 1200 } = {}) {
  const messages = Array.isArray(entry?.messages) ? entry.messages : [];
  let latestAssistantIndex = -1;
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index]?.role === "assistant") {
      latestAssistantIndex = index;
      break;
    }
  }

  return {
    ...entry,
    messages: messages.map((message, index) => {
      if (message?.role !== "assistant") {
        return message;
      }
      return {
        ...message,
        settings: storedAssistantSettings(message.settings),
        retrieved_chunks:
          index === latestAssistantIndex
            ? (message.retrieved_chunks || []).map((chunk) => compactChunk(chunk, chunkTextLimit))
            : [],
        omitted_chunks: [],
      };
    }),
  };
}

export function approximateLocalStorageMiB(value) {
  const characters = String(value || "").length;
  return (characters * 2) / (1024 * 1024);
}

export function saveJsonEntryList(storage, key, entries, compactEntry = (entry) => entry) {
  const candidate = (Array.isArray(entries) ? entries : []).map(compactEntry);
  try {
    storage.setItem(key, JSON.stringify(candidate));
    return { saved: true, entries: candidate };
  } catch (error) {
    if (!isStorageQuotaError(error)) {
      throw error;
    }
  }

  let previous = [];
  try {
    const parsed = JSON.parse(storage.getItem(key) || "[]");
    previous = Array.isArray(parsed) ? parsed : [];
  } catch {
    previous = [];
  }
  return { saved: false, entries: previous };
}

function isStorageQuotaError(error) {
  const message = String(error?.message || "").toLowerCase();
  return (
    error?.name === "QuotaExceededError" ||
    error?.name === "NS_ERROR_DOM_QUOTA_REACHED" ||
    error?.code === 22 ||
    error?.code === 1014 ||
    message.includes("quota")
  );
}

function compactChunk(chunk, textLimit) {
  if (!chunk || typeof chunk !== "object") {
    return chunk;
  }
  const text = String(chunk.text || "");
  return {
    ...chunk,
    text: text.length <= textLimit ? text : `${text.slice(0, Math.max(0, textLimit - 1)).trimEnd()}…`,
  };
}
