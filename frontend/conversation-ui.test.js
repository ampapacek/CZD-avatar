import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

describe("conversation request UI", () => {
  it("shows request progress inside the scrollable conversation stream", () => {
    const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
    const document = dom.window.document;
    const messageStream = document.querySelector("#conversationMessages");
    const progress = document.querySelector("#conversationRequestStatus");

    expect(messageStream).not.toBeNull();
    expect(progress).not.toBeNull();
    expect(messageStream.contains(progress)).toBe(true);
    expect(document.querySelector(".conversation-composer")?.contains(progress)).toBe(false);
  });

  it("places query rewriting and its result before the sources heading", () => {
    const dom = new JSDOM(readFileSync("app/static/index.html", "utf8"));
    const document = dom.window.document;
    const controls = document.querySelector(".conversation-rewrite-controls");
    const result = document.querySelector("#conversationRetrievalInfo");
    const heading = [...document.querySelectorAll("h3")].find(
      (element) => element.textContent.trim() === "Zdroje poslední odpovědi",
    );

    expect(controls).not.toBeNull();
    expect(result).not.toBeNull();
    expect(heading).not.toBeUndefined();
    expect(controls.contains(result)).toBe(true);
    expect(controls.compareDocumentPosition(heading) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("wraps long conversation text while keeping structured blocks scrollable", () => {
    const css = readFileSync("app/static/styles.css", "utf8");
    const dom = new JSDOM(`
      <style>${css}</style>
      <article class="conversation-message user">
        <div class="conversation-message-body"><p>longtext</p><pre>code</pre></div>
      </article>
    `);
    const message = dom.window.document.querySelector(".conversation-message");
    const body = dom.window.document.querySelector(".conversation-message-body");
    const pre = dom.window.document.querySelector("pre");

    expect(dom.window.getComputedStyle(message).overflowWrap).toBe("anywhere");
    expect(dom.window.getComputedStyle(body).overflowWrap).toBe("anywhere");
    expect(dom.window.getComputedStyle(pre).overflowX).toBe("auto");
  });
});
