import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { renderMarkdown } from "./markdown-renderer.js";

const sources = [
  { citation_id: "Z1", title: "První zdroj", document_url: "https://example.test/one" },
  { citation_id: "Z5", title: "Pátý zdroj", page_number: 7 },
];

function render(markdown, suppliedSources = sources) {
  const container = document.createElement("div");
  container.innerHTML = renderMarkdown(markdown, suppliedSources);
  return container;
}

describe("Markdown blocks", () => {
  it("renders ATX headings, lists, blockquotes, and fenced code", () => {
    const dom = render("# Nadpis\n\n- **silně**\n- *kurzíva*\n\n> citace\n\n```js\n<x>\n```");
    expect(dom.querySelector("h1")?.textContent).toBe("Nadpis");
    expect(dom.querySelectorAll("ul li")).toHaveLength(2);
    expect(dom.querySelector("strong")?.textContent).toBe("silně");
    expect(dom.querySelector("em")?.textContent).toBe("kurzíva");
    expect(dom.querySelector("blockquote")?.textContent?.trim()).toBe("citace");
    expect(dom.querySelector("pre code")?.textContent).toBe("<x>\n");
  });

  it("renders Setext h1 and h2", () => {
    const dom = render("První\n=====\n\nDruhý\n-----");
    expect(dom.querySelector("h1")?.textContent).toBe("První");
    expect(dom.querySelector("h2")?.textContent).toBe("Druhý");
  });

  it("renders the reported Setext heading and GFM table regression", () => {
    const dom = render(`Normalizace
===========

| Rok | Nejdůležitější událost |
| --- | --- |
| 1969 | Nástup normalizace |
| 1970 | Personální čistky |`);
    expect(dom.querySelector("h1")?.textContent).toBe("Normalizace");
    expect(dom.querySelector("table")).not.toBeNull();
    expect(dom.querySelectorAll("tbody tr")).toHaveLength(2);
    expect(dom.querySelector("tbody tr td")?.textContent).toBe("1969");
  });

  it("supports inline formatting, citations, and escaped pipes in table cells", () => {
    const dom = render("| Pole | Hodnota |\n| --- | --- |\n| **rok** | 1969 \\| 1970 [^Z1] |");
    expect(dom.querySelector("tbody td:first-child strong")?.textContent).toBe("rok");
    expect(dom.querySelector("tbody td:nth-child(2)")?.textContent).toContain("1969 | 1970");
    expect(dom.querySelector("tbody .footnote-ref a")?.dataset.citationId).toBe("Z1");
    expect(dom.querySelector(".markdown-table-wrap")?.scrollWidth).toBeGreaterThanOrEqual(0);
  });
});

describe("application citations", () => {
  it("links valid citations and leaves unknown citations as visible text", () => {
    const dom = render("Platná [^Z1], starší zápis [Z5], neznámá [^Z9].");
    expect(dom.querySelector('.footnote-ref a[data-citation-id="Z1"]')).not.toBeNull();
    expect(dom.querySelector('.footnote-ref a[data-citation-id="Z5"]')).not.toBeNull();
    expect(dom.textContent).toContain("[^Z9]");
    expect(dom.querySelector('[data-citation-id="Z9"]')).toBeNull();
  });

  it("numbers by first appearance and sorts adjacent citations numerically", () => {
    const dom = render("První [^Z1]. Společně [^Z5][^Z1], znovu [^Z5].");
    const refs = [...dom.querySelectorAll(".footnote-ref a")];
    expect(refs.map((ref) => ref.textContent)).toEqual(["1", "1", "2", "2"]);
    expect(refs.map((ref) => ref.dataset.citationId)).toEqual(["Z1", "Z1", "Z5", "Z5"]);
    expect(dom.querySelector(".footnote-sep")?.textContent).toBe(",");
    expect([...dom.querySelectorAll(".footnotes li")].map((item) => item.id)).toEqual(["fn-Z1", "fn-Z5"]);
  });

  it("removes generated footnote definitions and final source sections", () => {
    const dom = render("Odpověď [^Z1].\n\n[^Z1]: modelový popis\n\nDalší odstavec.\n\n## Použité zdroje\n- nemá zůstat");
    expect(dom.textContent).toContain("Odpověď");
    expect(dom.textContent).toContain("Další odstavec");
    expect(dom.textContent).not.toContain("modelový popis");
    expect(dom.textContent).not.toContain("nemá zůstat");
    expect(dom.querySelectorAll(".footnotes li")).toHaveLength(1);
  });
});

describe("untrusted and streaming output", () => {
  it("removes executable HTML, event handlers, and unsafe URL schemes", () => {
    const dom = render('<script>alert(1)</script><img src=x onerror="alert(2)">\n\n[nebezpečný](javascript:alert(3)) [^Z1]', [
      { citation_id: "Z1", title: "Zdroj", document_url: "javascript:alert(4)" },
    ]);
    expect(dom.querySelector("script, img, [onerror]")).toBeNull();
    expect(dom.innerHTML).not.toMatch(/href=["']javascript:/i);
    expect(dom.textContent).toContain("<script>alert(1)</script>");
  });

  it.each(["**rozepsané", "```js\nconst x = 1", "| A | B\n| --", "Text [^Z"])(
    "never throws for an incomplete streaming fragment: %s",
    (fragment) => expect(() => renderMarkdown(fragment, sources)).not.toThrow(),
  );
});

describe("application integration", () => {
  it("uses the shared renderer for main, conversation, and history answers", () => {
    const appSource = readFileSync("app/static/app.js", "utf8");
    expect(appSource).toContain('answerEl.innerHTML = Avatar.renderMarkdown(text, currentAnswerSources, "main-source")');
    expect(appSource).toContain('Avatar.renderMarkdown(message.content || "", message.sources || [], "conversation-source")');
    expect(appSource).toContain('Avatar.renderMarkdown(entry.answer, sources, "history-source")');
  });
});
