const CITATION_PATTERN = /^\[\^([A-Z]{1,3}\d+)\]|^\[([A-Z]{1,3}\d+)\]/;
const FOOTNOTE_DEFINITION_PATTERN = /^\[\^[A-Z]{1,3}\d+\]:/;
const SOURCES_HEADING_PATTERN = /^(?:#{1,6}\s*)?Použité zdroje:?\s*$/i;

export function prepareCitationMarkdown(markdown) {
  const lines = String(markdown || "").replace(/\r\n?/g, "\n").split("\n");
  const retained = [];
  let skippingDefinition = false;

  for (const line of lines) {
    if (SOURCES_HEADING_PATTERN.test(line.trim())) break;
    if (FOOTNOTE_DEFINITION_PATTERN.test(line)) {
      skippingDefinition = true;
      continue;
    }
    if (skippingDefinition && (/^(?: {2,}|\t)/.test(line) || !line.trim())) continue;
    skippingDefinition = false;
    retained.push(line);
  }

  return retained.join("\n").trim();
}

export function createCitationPlugin() {
  return (markdownIt) => {
    markdownIt.inline.ruler.before("link", "avatar_citation", (state, silent) => {
      const match = state.src.slice(state.pos).match(CITATION_PATTERN);
      if (!match) return false;

      const citationId = match[1] || match[2];
      const citationMap = state.env.citationMap;
      if (!(citationMap instanceof Map) || !citationMap.has(citationId)) return false;

      if (!silent) {
        const order = state.env.orderedCitationIds;
        if (!order.includes(citationId)) order.push(citationId);
        const token = state.push("avatar_citation", "", 0);
        token.meta = { citationId };
      }
      state.pos += match[0].length;
      return true;
    });

    markdownIt.renderer.rules.avatar_citation = (tokens, index, _options, env) => {
      const citationId = tokens[index].meta.citationId;
      const number = env.orderedCitationIds.indexOf(citationId) + 1;
      const separator = tokens[index - 1]?.type === "avatar_citation"
        ? '<sup class="footnote-ref"><span class="footnote-sep">,</span></sup>'
        : "";
      return `${separator}<sup class="footnote-ref"><a href="#fn-${citationId}" id="fnref-${citationId}" data-citation-id="${citationId}">${number}</a></sup>`;
    };
  };
}

export function buildCitationMap(sources) {
  return new Map((sources || []).filter((source) => source?.citation_id).map((source) => [source.citation_id, source]));
}

export function renderCitationOverview(orderedCitationIds, citationMap, escapeHtml) {
  const items = orderedCitationIds.map((citationId) => {
    const source = citationMap.get(citationId);
    if (!source) return "";
    const title = escapeHtml(source.title || citationId);
    const page = source.page_number ? `, str. ${escapeHtml(source.page_number)}` : "";
    const targetUrl = source.document_url || source.source_url || source.url;
    const titleHtml = targetUrl
      ? `<a href="${escapeHtml(targetUrl)}" target="_blank" rel="noreferrer">${title}</a>`
      : title;
    return `<li id="fn-${citationId}"><span class="footnote-label">[${citationId}]</span> ${titleHtml}${page}</li>`;
  }).filter(Boolean).join("");

  if (!items) return "";
  return `<section class="footnotes"><h4>Poznámky a zdroje</h4><ol>${items}</ol></section>`;
}
