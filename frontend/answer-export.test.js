import { describe, expect, it } from "vitest";

import { answerForCopy } from "./answer-export.js";

const sources = [
  { citation_id: "Z1", title: "Dějiny českých zemí", document_url: "https://example.test/dejiny" },
  { citation_id: "Z3", title: "Kronika", page_number: 42 },
];

describe("answerForCopy", () => {
  it("renumbers markers to the numbers the reader saw", () => {
    expect(answerForCopy("Prvni.[^Z3] Druhe.[^Z1] Znovu.[^Z3]", sources)).toBe(
      "Prvni.[1] Druhe.[2] Znovu.[1]",
    );
  });

  it("accepts the bare [Zn] spelling too", () => {
    expect(answerForCopy("Veta.[Z1]", sources)).toBe("Veta.[1]");
  });

  it("leaves an unretrieved id literal, as the answer body does", () => {
    expect(answerForCopy("Veta.[^Z9]", sources)).toBe("Veta.[^Z9]");
  });

  it("drops model-invented footnote definitions and closing source sections", () => {
    const answer = "Veta.[^Z1]\n\n[^Z1]: vymyslený popis\n\n## Použité zdroje\n- nemá zůstat";
    expect(answerForCopy(answer, sources)).toBe("Veta.[1]");
  });

  it("appends a numbered source key on request", () => {
    expect(answerForCopy("Prvni.[^Z3] Druhe.[^Z1]", sources, { includeSources: true })).toBe(
      [
        "Prvni.[1] Druhe.[2]",
        "",
        "Zdroje:",
        "1. Kronika, str. 42",
        "2. Dějiny českých zemí — https://example.test/dejiny",
      ].join("\n"),
    );
  });

  it("omits the source key when the answer cites nothing", () => {
    expect(answerForCopy("Odpověď bez citací.", sources, { includeSources: true })).toBe(
      "Odpověď bez citací.",
    );
  });

  it("is empty for an empty answer", () => {
    expect(answerForCopy("", sources, { includeSources: true })).toBe("");
    expect(answerForCopy(null, sources)).toBe("");
  });
});
