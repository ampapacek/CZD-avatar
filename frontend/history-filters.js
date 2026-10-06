// Pure helpers behind the history dialog's filter bar and the per-WP cap on the
// locally stored history. `app.js` maps each entry to a flat facet record
// ({ wp, author, prompt, model, time, text }) so these never read entry shapes.

export const HISTORY_PERIODS = ["all", "today", "7d", "30d"];
export const HISTORY_GROUPINGS = ["none", "day", "question", "author", "prompt", "model"];
export const OTHER_QUESTIONS_KEY = "__other__";

const DAY_MS = 24 * 60 * 60 * 1000;

// Earliest timestamp (ms) a period admits, or null for "all". "today" means the
// local calendar day, the others are rolling windows.
export function periodStart(period, now = new Date()) {
  if (period === "today") {
    return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  }
  if (period === "7d") {
    return now.getTime() - 7 * DAY_MS;
  }
  if (period === "30d") {
    return now.getTime() - 30 * DAY_MS;
  }
  return null;
}

function normalizeText(value) {
  return String(value || "")
    .toLocaleLowerCase("cs")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

// Every filter is optional; an empty value means "any". Text search ignores case
// and diacritics so "husite" finds "husité".
export function filterHistory(items, facetsOf, filters = {}, now = new Date()) {
  const since = periodStart(filters.period, now);
  const needle = normalizeText(filters.text).trim();
  return items.filter((item) => {
    const facets = facetsOf(item);
    if (filters.wp && facets.wp !== filters.wp) {
      return false;
    }
    for (const field of ["author", "prompt", "model"]) {
      if (filters[field] && facets[field] !== filters[field]) {
        return false;
      }
    }
    if (since !== null) {
      const time = Date.parse(facets.time || "");
      if (!Number.isFinite(time) || time < since) {
        return false;
      }
    }
    if (needle && !normalizeText(facets.text).includes(needle)) {
      return false;
    }
    return true;
  });
}

// Distinct non-empty values of one facet, alphabetically.
export function facetOptions(items, facetsOf, field) {
  const values = new Set();
  for (const item of items) {
    const value = facetsOf(item)[field];
    if (value) {
      values.add(value);
    }
  }
  return [...values].sort((a, b) => a.localeCompare(b, "cs"));
}

// Groups keep the incoming (newest-first) order, both between groups and inside
// them: a group sits where its newest item would. "day" groups by `dayLabel`,
// which the caller formats for the local time zone. "question" matches ignoring
// case, diacritics and surrounding whitespace, labels each group with its newest
// item's wording, and gathers questions asked only once into a last
// `otherLabel` group so the repeated ones stand out.
export function groupHistory(items, facetsOf, groupBy, { emptyLabel = "—", dayLabel, otherLabel = "Ostatní" } = {}) {
  if (!groupBy || groupBy === "none") {
    return [{ key: "", label: "", items: [...items] }];
  }
  const groups = new Map();
  for (const item of items) {
    const facets = facetsOf(item);
    let raw;
    if (groupBy === "day") {
      raw = dayLabel ? dayLabel(facets.time) : String(facets.time || "").slice(0, 10);
    } else if (groupBy === "question") {
      raw = String(facets.question || "").trim();
    } else {
      raw = facets[groupBy];
    }
    const label = raw || emptyLabel;
    const key = groupBy === "question" ? normalizeText(raw).trim() : label;
    if (!groups.has(key)) {
      groups.set(key, { key, label, items: [] });
    }
    groups.get(key).items.push(item);
  }
  if (groupBy !== "question") {
    return [...groups.values()];
  }
  const repeated = [];
  const other = { key: OTHER_QUESTIONS_KEY, label: otherLabel, items: [] };
  for (const group of groups.values()) {
    if (group.items.length > 1) {
      repeated.push(group);
    } else {
      other.items.push(...group.items);
    }
  }
  return other.items.length ? [...repeated, other] : repeated;
}

// Keep at most `maxPerWp` entries per WP; entries are newest-first, so the
// oldest of each WP go. Other WPs' entries are untouched.
export function trimHistoryPerWp(entries, maxPerWp, wpOf) {
  const counts = new Map();
  return entries.filter((entry) => {
    const wp = wpOf(entry);
    const count = (counts.get(wp) || 0) + 1;
    counts.set(wp, count);
    return count <= maxPerWp;
  });
}
