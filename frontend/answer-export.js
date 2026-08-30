/**
 * Turning a rendered answer back into text someone can paste elsewhere.
 *
 * What the user sees is not what the model wrote: citation markers are `[^Z3]`
 * in the raw text but render as superscript ¹ ² ³ numbered by first appearance,
 * and model-emitted footnote definitions are dropped. Copying the raw text would
 * paste cryptic ids and resurrect the fabricated source list, so this rebuilds
 * the answer the way it is displayed.
 */

import { prepareCitationMarkdown } from "./citations.js";
import { extractOrderedCitationIds } from "./sources-panel.js";

const CITATION_MARKER_PATTERN = /\[\^([A-Z]{1,3}\d+)\]|\[([A-Z]{1,3}\d+)\]/g;

function citationNumbers(text, sources) {
  const known = new Set((sources || []).map((source) => source?.citation_id).filter(Boolean));
  const ordered = extractOrderedCitationIds(text).filter((citationId) => known.has(citationId));
  return new Map(ordered.map((citationId, index) => [citationId, index + 1]));
}

/** One source line: "1. Titul, str. 12 — https://…" */
function sourceLine(number, source) {
  const parts = [source.title || source.citation_id || "Neznámý dokument"];
  if (source.page_number) {
    parts.push(`str. ${source.page_number}`);
  }
  const url = source.document_url || source.source_url || source.url;
  const suffix = url ? ` — ${url}` : "";
  return `${number}. ${parts.join(", ")}${suffix}`;
}

/**
 * Build the clipboard text for an answer.
 *
 * Markers become the numbers the reader saw. A marker whose id was never
 * retrieved keeps its literal form, matching the answer body, where the markdown
 * plugin refuses to render an unknown id as a superscript.
 */
export function answerForCopy(answerText, sources = [], { includeSources = false } = {}) {
  const prepared = prepareCitationMarkdown(answerText);
  if (!prepared) {
    return "";
  }
  const numbers = citationNumbers(answerText, sources);
  const body = prepared.replace(CITATION_MARKER_PATTERN, (match, footnoteId, bareId) => {
    const number = numbers.get(footnoteId || bareId);
    return number ? `[${number}]` : match;
  });
  if (!includeSources || numbers.size === 0) {
    return body;
  }
  const byCitationId = new Map((sources || []).map((source) => [source.citation_id, source]));
  const lines = [...numbers.entries()]
    .sort((a, b) => a[1] - b[1])
    .map(([citationId, number]) => sourceLine(number, byCitationId.get(citationId) || { citation_id: citationId }));
  return `${body}\n\nZdroje:\n${lines.join("\n")}`;
}
