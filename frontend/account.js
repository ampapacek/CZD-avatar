// User accounts: text and checks shared by the login page and the account dialog.
// The server is the authority on every rule here; these only give early feedback.

// Same shape as EMAIL_RE in app/accounts.py.
const EMAIL_RE = /^[^@\s]+@[^@\s.]+(\.[^@\s.]+)*\.[a-z]{2,}$/;
export const PASSWORD_MIN_LENGTH = 8;

export const REGISTRATION_MODE_LABELS = {
  open: "Otevřená (nový účet funguje hned)",
  approval: "Se schválením (nový účet musí schválit admin)",
  closed: "Uzavřená (nové účty nejde zakládat)",
};

export const USER_STATUS_LABELS = {
  active: "Aktivní",
  pending: "Čeká na schválení",
  disabled: "Zablokovaný",
};

export function normalizeEmail(email) {
  return String(email || "").trim().toLowerCase();
}

export function isValidEmail(email) {
  const normalized = normalizeEmail(email);
  return normalized.length <= 254 && EMAIL_RE.test(normalized);
}

// First problem with a new password (and its confirmation), or "" when fine.
export function passwordProblem(password, confirmation = password) {
  if (String(password || "").length < PASSWORD_MIN_LENGTH) {
    return `Heslo musí mít alespoň ${PASSWORD_MIN_LENGTH} znaků.`;
  }
  if (password !== confirmation) {
    return "Hesla se neshodují.";
  }
  return "";
}

// One line about today's requests, or "" when accounts are off or nobody is logged in.
export function quotaText(account) {
  if (!account?.enabled || !account.user) {
    return "";
  }
  if (account.requests_remaining === null || account.requests_remaining === undefined) {
    return "Bez denního limitu dotazů.";
  }
  return `Dnes zbývá ${account.requests_remaining} z ${account.daily_limit} dotazů. Limit se obnoví o půlnoci.`;
}

// The account with the remaining count from a counted response's
// X-Daily-Requests-Remaining header; -1 there means unlimited.
export function accountWithRemaining(account, headerValue) {
  if (!account?.enabled || !account.user || headerValue === null || headerValue === undefined || headerValue === "") {
    return account;
  }
  const remaining = Number(headerValue);
  if (!Number.isInteger(remaining)) {
    return account;
  }
  if (remaining < 0) {
    return { ...account, requests_remaining: null };
  }
  return {
    ...account,
    requests_remaining: remaining,
    requests_today: Math.max(0, (account.daily_limit || 0) - remaining),
  };
}

export function registrationNote(mode) {
  if (mode === "closed") {
    return "Registrace je momentálně uzavřená. O účet požádej administrátora.";
  }
  if (mode === "approval") {
    return "Nový účet musí před prvním přihlášením schválit administrátor.";
  }
  return "";
}

// "12. 11. 2026 14:05" in Prague time, or "–" for a missing value.
export function formatAccountDate(iso) {
  if (!iso) {
    return "–";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "–";
  }
  return date.toLocaleString("cs-CZ", {
    timeZone: "Europe/Prague",
    day: "numeric",
    month: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
