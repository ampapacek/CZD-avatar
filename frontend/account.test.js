import { describe, expect, it } from "vitest";

import {
  accountWithRemaining,
  defaultAuthorName,
  formatAccountDate,
  isValidEmail,
  passwordProblem,
  quotaText,
  registrationNote,
} from "./account.js";

const account = {
  enabled: true,
  daily_limit: 100,
  user: { email: "jan@seznam.cz", is_admin: false },
  requests_today: 10,
  requests_remaining: 90,
};

describe("isValidEmail", () => {
  it("accepts ordinary addresses regardless of case and spaces", () => {
    expect(isValidEmail(" Jan.Novak@Seznam.CZ ")).toBe(true);
    expect(isValidEmail("a+tag@mff.cuni.cz")).toBe(true);
  });

  it("rejects what the server rejects", () => {
    for (const email of ["", "jan", "jan@", "@seznam.cz", "jan@seznam", "jan@seznam.c", "jan@@seznam.cz", "jan novak@seznam.cz", "jan@seznam..cz"]) {
      expect(isValidEmail(email), email).toBe(false);
    }
  });
});

describe("passwordProblem", () => {
  it("requires length and a matching confirmation", () => {
    expect(passwordProblem("short")).toMatch("alespoň 8");
    expect(passwordProblem("long enough", "different")).toMatch("neshodují");
    expect(passwordProblem("long enough", "long enough")).toBe("");
  });
});

describe("quotaText", () => {
  it("is empty without accounts or a user", () => {
    expect(quotaText({ enabled: false })).toBe("");
    expect(quotaText({ ...account, user: null })).toBe("");
  });

  it("shows the remaining count, or no limit for admins", () => {
    expect(quotaText(account)).toMatch("Dnes zbývá 90 z 100 dotazů");
    expect(quotaText({ ...account, requests_remaining: null })).toBe("Bez denního limitu dotazů.");
  });
});

describe("accountWithRemaining", () => {
  it("takes the count from the response header", () => {
    expect(accountWithRemaining(account, "42")).toMatchObject({ requests_remaining: 42, requests_today: 58 });
  });

  it("treats -1 as unlimited and ignores a missing or broken header", () => {
    expect(accountWithRemaining(account, "-1").requests_remaining).toBeNull();
    expect(accountWithRemaining(account, null)).toBe(account);
    expect(accountWithRemaining(account, "abc")).toBe(account);
    expect(accountWithRemaining({ enabled: false }, "5")).toEqual({ enabled: false });
  });
});

describe("registrationNote", () => {
  it("explains approval and closed registration", () => {
    expect(registrationNote("approval")).toMatch("schválit");
    expect(registrationNote("closed")).toMatch("uzavřená");
    expect(registrationNote("open")).toBe("");
  });
});

describe("formatAccountDate", () => {
  it("formats in Prague time and tolerates missing values", () => {
    expect(formatAccountDate("2026-11-11T23:30:00+00:00")).toMatch(/12\. ?11\. ?2026/);
    expect(formatAccountDate(null)).toBe("–");
    expect(formatAccountDate("nonsense")).toBe("–");
  });
});

describe("defaultAuthorName", () => {
  it("takes the part before the @", () => {
    expect(defaultAuthorName("ales.papacek@seznam.cz")).toBe("ales.papacek");
    expect(defaultAuthorName("")).toBe("");
  });
});
