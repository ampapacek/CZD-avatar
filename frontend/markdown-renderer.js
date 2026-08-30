import createDOMPurify from "dompurify";
import MarkdownIt from "markdown-it";

import { extractOrderedCitationIds } from "./sources-panel.js";
import {
  buildCitationMap,
  createCitationPlugin,
  prepareCitationMarkdown,
  renderCitationOverview,
} from "./citations.js";

const markdownIt = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: false,
});

markdownIt.use(createCitationPlugin());

const defaultLinkOpen = markdownIt.renderer.rules.link_open
  || ((tokens, index, options, _env, self) => self.renderToken(tokens, index, options));
markdownIt.renderer.rules.link_open = (tokens, index, options, env, self) => {
  tokens[index].attrSet("target", "_blank");
  tokens[index].attrSet("rel", "noreferrer");
  return defaultLinkOpen(tokens, index, options, env, self);
};
markdownIt.renderer.rules.table_open = () => '<div class="markdown-table-wrap"><table>\n';
markdownIt.renderer.rules.table_close = () => "</table></div>\n";

const purifier = createDOMPurify(globalThis.window);
const SANITIZE_OPTIONS = {
  ALLOWED_TAGS: [
    "a", "blockquote", "br", "code", "details", "div", "em", "h1", "h2", "h3", "h4", "h5", "h6",
    "hr", "li", "ol", "p", "pre", "s", "section", "span", "strong", "sup", "table", "tbody",
    "summary", "td", "th", "thead", "tr", "ul",
  ],
  ALLOWED_ATTR: ["class", "data-citation-id", "href", "id", "rel", "start", "target", "title"],
  ALLOW_DATA_ATTR: false,
};

export function renderMarkdown(markdown, sources = []) {
  const input = String(markdown || "");
  try {
    const citationMap = buildCitationMap(sources);
    const env = { citationMap, orderedCitationIds: [] };
    const answerHtml = markdownIt.render(prepareCitationMarkdown(input), env);
    const overviewHtml = renderCitationOverview(env.orderedCitationIds, citationMap, markdownIt.utils.escapeHtml);
    return purifier.sanitize(`<div class="markdown-content">${answerHtml}${overviewHtml}</div>`, SANITIZE_OPTIONS);
  } catch {
    return `<div class="markdown-content"><p>${markdownIt.utils.escapeHtml(input).replace(/\n/g, "<br>")}</p></div>`;
  }
}

export function extractCitationIds(text) {
  return new Set(extractOrderedCitationIds(text));
}
