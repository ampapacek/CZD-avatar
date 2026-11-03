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

// Admin Cache dialog ----------------------------------------------------------

export function formatBytes(bytes) {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value < 0) {
    return "";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  const units = ["kB", "MB", "GB"];
  let scaled = value / 1024;
  let unit = 0;
  while (scaled >= 1024 && unit < units.length - 1) {
    scaled /= 1024;
    unit += 1;
  }
  return `${scaled.toLocaleString("cs-CZ", { maximumFractionDigits: scaled < 10 ? 1 : 0 })} ${units[unit]}`;
}

// The filter as the query of GET answer-cache; empty fields are left out.
export function cacheFilterQuery(filter = {}) {
  const params = new URLSearchParams();
  for (const name of ["wp_id", "pinned", "stale", "q"]) {
    const value = String(filter[name] ?? "").trim();
    if (value) {
      params.set(name, value);
    }
  }
  return params.toString();
}

// The same filter as the body of POST answer-cache/delete.
export function cacheFilterBody(filter = {}) {
  const flag = (value) => (value === "true" ? true : value === "false" ? false : null);
  return {
    wp_id: String(filter.wp_id ?? "").trim() || null,
    pinned: flag(filter.pinned),
    stale: flag(filter.stale),
    q: String(filter.q ?? "").trim() || null,
  };
}

export function cacheStatsText(stats, matching, shown) {
  if (!stats) {
    return "";
  }
  const parts = [
    `${stats.entries} odpovědí`,
    `${stats.pinned} připnutých`,
    `${stats.stale} starých`,
    `${stats.hits} použití`,
    formatBytes(stats.size_bytes),
    `nepřipnuté vyprší po ${stats.ttl_days} dnech, nejvýš ${stats.max_entries} nepřipnutých`,
  ];
  let text = parts.join(" · ");
  if (shown < matching) {
    text += `. Filtru odpovídá ${matching}, zobrazeno prvních ${shown}.`;
  } else if (matching !== stats.entries) {
    text += `. Filtru odpovídá ${matching}.`;
  }
  return text;
}

export function cacheProfileLabel(entry) {
  return entry?.prompt_preset_name || entry?.prompt_preset_id || "—";
}

// The settings that tell apart answers to the same question, from the stored key input.
export function cacheSettingsSummary(settings = {}) {
  const parts = [];
  const add = (label, value) => {
    if (value !== null && value !== undefined && value !== "") {
      parts.push(`${label}: ${value}`);
    }
  };
  add("WP", settings.wp_id);
  add("Model", [settings.llm_provider, settings.model].filter(Boolean).join(" / "));
  add("Uvažování", settings.reasoning_effort);
  add("Délka", settings.output_length);
  add("Vyhledávání", settings.retrieval_backend === "msearch"
    ? [settings.msearch_collection, settings.msearch_mode].filter(Boolean).join(", ")
    : settings.retrieval_backend);
  add("Počet zdrojů", settings.top_k);
  add("Context window", settings.context_window_tokens);
  return parts.join(" · ");
}
