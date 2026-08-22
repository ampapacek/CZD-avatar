/**
 * View model for the `Zdroje` panel.
 *
 * The answer body renumbers citations by first appearance
 * (`orderedCitationIds.indexOf(id) + 1` in `citations.js`), while the panel used
 * to label every card with its retrieval rank `Z*`. Clicking superscript ² in
 * the answer therefore scrolled to a card labelled `[Z7]`. This module computes
 * the panel layout so both agree.
 *
 * Everything here is pure: it takes sources plus a view state and returns what
 * to draw. The DOM assembly, highlighting and event wiring stay in `app.js`, and
 * the view state is passed in rather than read from a module global so the main
 * panel, conversation mode and history cannot desync.
 */

import { prepareCitationMarkdown } from "./citations.js";

export const RETRIEVED_ORDER = "retrieved";
export const CITATION_ORDER = "citation";

const CITATION_MARKER_PATTERN = /\[\^([A-Z]{1,3}\d+)\]|\[([A-Z]{1,3}\d+)\]/g;

/**
 * Citation ids in order of first appearance in the answer.
 *
 * Runs on `prepareCitationMarkdown` output, not the raw text, so ids that only
 * occur inside a model-emitted `[^Zn]:` definition block (which is never
 * rendered) cannot claim a citation number the answer does not show.
 */
export function extractOrderedCitationIds(text) {
  const prepared = prepareCitationMarkdown(text);
  const ordered = [];
  const seen = new Set();
  for (const match of prepared.matchAll(CITATION_MARKER_PATTERN)) {
    const citationId = match[1] || match[2];
    if (citationId && !seen.has(citationId)) {
      seen.add(citationId);
      ordered.push(citationId);
    }
  }
  return ordered;
}

/** Fresh view state: retrieved order, everything visible, nothing cited yet. */
export function createSourcesView(overrides = {}) {
  return {
    order: RETRIEVED_ORDER,
    showUncited: true,
    // `complete` gates the flip and the citation numbers. It stays false for an
    // aborted or errored stream, where the citation set is incomplete.
    complete: false,
    // `Pouze vyhledat zdroje` has no answer, so there is nothing to flip to.
    canFlip: true,
    ...overrides,
  };
}

/**
 * The view state an answer settles into once its stream finishes cleanly.
 *
 * No citations at all means no flip: keep retrieved order and keep every source
 * visible, because "the answer cites nothing" is a quality signal that must stay
 * on screen rather than becoming a silent no-op.
 */
export function completedSourcesView(view, orderedCitationIds = []) {
  const base = { ...view, complete: true };
  if (!view.canFlip || !orderedCitationIds.length) {
    return base;
  }
  return { ...base, order: CITATION_ORDER, showUncited: false };
}

function citationIdsOf(sources) {
  return new Set((sources || []).map((source) => source?.citation_id).filter(Boolean));
}

/**
 * Lay the panel out.
 *
 * `orderedCitationIds` is filtered against the sources actually on screen, the
 * same way the markdown plugin refuses to render a marker whose id it does not
 * know — otherwise an invented `[Z9]` would shift every number away from the
 * superscripts in the answer.
 */
export function layoutSources(sources, view, { orderedCitationIds = [], omittedCitationIds = [] } = {}) {
  const list = sources || [];
  const known = citationIdsOf(list);
  const cited = orderedCitationIds.filter((citationId) => known.has(citationId));
  const citationNumbers = new Map(cited.map((citationId, index) => [citationId, index + 1]));
  const omitted = new Set(omittedCitationIds);
  // Numbers appear only once the answer is final. While it streams the panel
  // stays exactly as it was before this feature: retrieved order, `[Z*]` labels.
  const showCitationNumbers = Boolean(view.complete) && cited.length > 0;

  const entries = list.map((source, index) => {
    const citationId = source?.citation_id || "";
    const citationNumber = citationNumbers.get(citationId) ?? null;
    return {
      source,
      citationId,
      citationNumber,
      cited: citationNumber !== null,
      omitted: omitted.has(citationId),
      retrievalRank: index + 1,
    };
  });

  const citedEntries = entries.filter((entry) => entry.cited);
  const uncitedEntries = entries.filter((entry) => !entry.cited);
  const ordered =
    view.order === CITATION_ORDER
      ? [...citedEntries].sort((a, b) => a.citationNumber - b.citationNumber).concat(uncitedEntries)
      : entries;

  const hideUncited = view.order === CITATION_ORDER && !view.showUncited;
  const visible = hideUncited ? ordered.filter((entry) => entry.cited) : ordered;

  return {
    order: view.order,
    entries: ordered,
    visible,
    showCitationNumbers,
    citedCount: citedEntries.length,
    uncitedCount: uncitedEntries.length,
    hiddenCount: hideUncited ? uncitedEntries.length : 0,
    hasCitations: cited.length > 0,
    // While the answer streams, tell the user the order is provisional.
    showNotice: Boolean(view.canFlip) && !view.complete,
    // After it settles, offer the way back to relevance order.
    showOrderToggle: Boolean(view.canFlip) && Boolean(view.complete) && cited.length > 0,
    // Only in citation order: relevance order is the raw ranking, and hiding
    // rows inside it would misrepresent what the retriever returned. Nothing to
    // collapse either when every source is cited.
    showUncitedToggle:
      Boolean(view.canFlip)
      && Boolean(view.complete)
      && view.order === CITATION_ORDER
      && cited.length > 0
      && uncitedEntries.length > 0,
    // A finished answer that cites nothing is worth saying out loud.
    showNoCitationsNotice: Boolean(view.canFlip) && Boolean(view.complete) && cited.length === 0 && list.length > 0,
  };
}

/** Card label: citation number plus retrieval rank for cited, rank alone otherwise. */
export function sourceCardLabel(entry, showCitationNumbers) {
  if (showCitationNumbers && entry.cited) {
    return `[${entry.citationNumber}] · ${entry.citationId}`;
  }
  return `[${entry.citationId}]`;
}

export const SEMANTIC_CHANNEL_LABEL = "sémanticky";
export const KEYWORD_CHANNEL_LABEL = "klíčová slova";

function scoreComponent(value) {
  return typeof value === "number" ? value : null;
}

/**
 * The diagnostics parts of one card: `["score 0.48", "emb 0.61", "BM25 0.22"]`.
 *
 * Local hybrid retrieval normalizes both channels and blends them, so all three
 * numbers differ and all three are worth showing. mSearch is different: it
 * returns one score per hit and copies it into whichever channel found the
 * document, leaving the other one absent — so `score 0.53 · BM25 0.53` printed
 * the same number twice. The only information there is *which* channel found
 * it, so name the channel instead of repeating the number.
 */
export function sourceScoreParts(source, chunk) {
  const score = scoreComponent(source?.score);
  const dense = scoreComponent(chunk?.dense_score);
  const bm25 = scoreComponent(chunk?.bm25_score);
  const parts = [score === null ? "score" : `score ${score.toFixed(2)}`];
  const onlyDense = dense !== null && bm25 === null;
  const onlyBm25 = bm25 !== null && dense === null;
  if (score !== null && onlyDense && dense === score) {
    parts.push(SEMANTIC_CHANNEL_LABEL);
    return parts;
  }
  if (score !== null && onlyBm25 && bm25 === score) {
    parts.push(KEYWORD_CHANNEL_LABEL);
    return parts;
  }
  if (dense !== null) {
    parts.push(`emb ${dense.toFixed(2)}`);
  }
  if (bm25 !== null) {
    parts.push(`BM25 ${bm25.toFixed(2)}`);
  }
  return parts;
}
