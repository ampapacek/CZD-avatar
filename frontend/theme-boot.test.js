import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";

const html = readFileSync("app/static/index.html", "utf8");

// `resources` stays at its default so JSDOM never fetches static/app.js or the
// bundle: whatever the theme ends up as here was set by the inline boot script.
function boot(storedTheme) {
  return new JSDOM(html, {
    runScripts: "dangerously",
    url: "https://avatar.test/",
    beforeParse(window) {
      if (storedTheme !== undefined) {
        window.localStorage.setItem("theme", storedTheme);
      }
    },
  });
}

describe("theme boot script", () => {
  it("applies a saved dark theme", () => {
    expect(boot("dark").window.document.body.dataset.theme).toBe("dark");
  });

  it("falls back to light when nothing is saved", () => {
    expect(boot().window.document.body.dataset.theme).toBe("light");
  });

  it("falls back to light for an unknown stored value", () => {
    expect(boot("neon").window.document.body.dataset.theme).toBe("light");
  });

  it("survives localStorage being unavailable", () => {
    const dom = new JSDOM(html, {
      runScripts: "dangerously",
      url: "https://avatar.test/",
      beforeParse(window) {
        Object.defineProperty(window, "localStorage", {
          get() {
            throw new Error("site data blocked");
          },
        });
      },
    });
    expect(dom.window.document.body.dataset.theme).toBe("light");
  });

  it("runs at parse time, before the page's other scripts", () => {
    const dom = boot("dark");
    const document = dom.window.document;
    const bootScript = document.querySelector("#themeBoot");
    expect(bootScript).not.toBeNull();
    expect(bootScript.parentElement).toBe(document.body);
    expect(document.body.firstElementChild).toBe(bootScript);
    const others = [...document.querySelectorAll("script")].filter((script) => script !== bootScript);
    expect(others.length).toBeGreaterThan(0);
    for (const script of others) {
      expect(bootScript.compareDocumentPosition(script) & dom.window.Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      // app.js and the bundle were never fetched, so they cannot be what set the theme.
      expect(script.src).not.toBe("");
    }
  });
});
