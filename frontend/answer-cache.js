// Answers the server replayed from its answer cache instead of generating them
// (`cache_hit` in the `done` event; see docs/architecture.md#answer-cache).

export function isCachedAnswer(data) {
  return data?.cache_hit === true;
}

// `cached_at` is the server's Unix time in seconds.
export function formatCachedAt(cachedAt, timeZone = undefined) {
  const seconds = Number(cachedAt);
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "";
  }
  return new Date(seconds * 1000).toLocaleString("cs-CZ", {
    day: "numeric",
    month: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  });
}

export function cachedAnswerStatus(doneData, modelLabel = "", timeZone = undefined) {
  let label = "Odpověď z mezipaměti";
  const when = formatCachedAt(doneData?.cached_at, timeZone);
  if (when) {
    label += ` (vygenerováno ${when})`;
  }
  if (modelLabel) {
    label += ` · ${modelLabel}`;
  }
  return label;
}
