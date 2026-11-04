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
  for (const name of ["wp_id", "llm_provider", "model", "pinned", "stale", "q"]) {
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
    llm_provider: String(filter.llm_provider ?? "").trim() || null,
    model: String(filter.model ?? "").trim() || null,
    pinned: flag(filter.pinned),
    stale: flag(filter.stale),
    q: String(filter.q ?? "").trim() || null,
  };
}

// The provider and model filter options as [value, entries] pairs, from the
// "models" counts of the listing; the models only of `provider` when one is
// chosen. A chosen value with no entries left stays, with 0.
export function cacheFilterOptions(models = [], { provider = "", model = "" } = {}) {
  const count = (items, valueOf) => {
    const counts = new Map();
    for (const item of items) {
      const value = valueOf(item) || "";
      if (value) {
        counts.set(value, (counts.get(value) || 0) + item.entries);
      }
    }
    return counts;
  };
  const providers = count(models, (item) => item.llm_provider);
  const providerModels = count(models.filter((item) => !provider || item.llm_provider === provider), (item) => item.model);
  if (provider && !providers.has(provider)) {
    providers.set(provider, 0);
  }
  if (model && !providerModels.has(model)) {
    providerModels.set(model, 0);
  }
  return { providers: [...providers], models: [...providerModels] };
}

export function cacheStatsText(stats, matching, shown) {
  if (!stats) {
    return "";
  }
  const parts = [
    `${stats.entries} odpovědí`,
    `${stats.pinned} připnutých (zůstávají v cache i po uplynutí doby)`,
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

// The settings that tell apart answers to the same question, from the stored key
// input. `collectionLabel` names a collection id (the id itself if unknown).
export function cacheSettingsSummary(settings = {}, collectionLabel = (id) => id) {
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
  if (settings.retrieval_backend === "msearch") {
    add("Kolekce", settings.msearch_collection ? collectionLabel(settings.msearch_collection) : null);
    add("Vyhledávání", settings.msearch_mode);
  } else {
    add("Vyhledávání", settings.retrieval_backend);
  }
  add("Počet zdrojů", settings.top_k);
  add("Context window", settings.context_window_tokens);
  return parts.join(" · ");
}

// The warm form as the body of POST answer-cache/warm. Custom questions are
// one per line; no model means the provider's default model.
export function cacheWarmBody(form = {}, { dryRun = false } = {}) {
  const concurrency = String(form.concurrency ?? "").trim() ? Math.round(Number(form.concurrency)) : NaN;
  return {
    wp: [form.wp || "all"],
    questions: form.questions === "custom"
      ? String(form.custom ?? "").split("\n").map((line) => line.trim()).filter(Boolean)
      : "prepared",
    profile: [form.profile || "default"],
    provider: form.provider || null,
    model: (form.models || []).filter(Boolean),
    force: Boolean(form.force),
    concurrency: Number.isFinite(concurrency) ? Math.min(Math.max(concurrency, 1), 20) : 4,
    dry_run: dryRun,
  };
}

// The question before warming, from the dry run's counts.
export function cacheWarmConfirmText({ jobs, cached = 0 }, { force = false, concurrency } = {}) {
  let what = `Vygenerovat ${force ? jobs : jobs - cached} odpovědí a připnout?`;
  if (cached) {
    what += force
      ? ` ${cached} z nich už v cache jsou, vygenerují se znovu.`
      : ` Dalších ${cached} už v cache je, ty se jen připnou.`;
  }
  return `${what} Concurrency ${concurrency}.`;
}

export function cacheWarmStatusText(status) {
  if (!status || status.state === "idle") {
    return "";
  }
  const counts = [
    `${status.done} / ${status.total}`,
    `vygenerováno ${status.generated}`,
    `už v cache ${status.cached}`,
    `chyby ${status.failed}`,
  ];
  if (status.state === "running") {
    const waiting = status.cancelled
      ? `Ruším, dobíhá ${status.running}`
      : `Běží ${status.running}, čeká ${status.pending}`;
    return `${waiting} · ${counts.join(" · ")}`;
  }
  const finished = status.state === "cancelled" ? "Zrušeno" : "Hotovo";
  return `${finished} · ${counts.join(" · ")}`;
}
