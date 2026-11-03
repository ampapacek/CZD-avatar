// Login and registration page, shown by the server to logged-out visitors when
// AUTH_ENABLED is on. On success it sends the browser on to the app, keeping
// the app's query string (e.g. ?shared=<id>) that the server passed along.

const loginTab = document.querySelector("#loginTab");
const registerTab = document.querySelector("#registerTab");
const loginForm = document.querySelector("#loginForm");
const loginEmail = document.querySelector("#loginEmail");
const loginPassword = document.querySelector("#loginPassword");
const loginConfirmField = document.querySelector("#loginConfirmField");
const loginConfirm = document.querySelector("#loginConfirm");
const registrationNoteEl = document.querySelector("#registrationNote");
const loginStatus = document.querySelector("#loginStatus");
const loginSubmit = document.querySelector("#loginSubmit");

let registering = false;
let registrationMode = "approval";

function setStatus(message, variant = "") {
  loginStatus.textContent = message;
  loginStatus.className = variant ? `status ${variant}` : "status";
}

function setRegistering(value) {
  registering = value && registrationMode !== "closed";
  loginTab.setAttribute("aria-selected", String(!registering));
  registerTab.setAttribute("aria-selected", String(registering));
  loginConfirmField.hidden = !registering;
  loginPassword.autocomplete = registering ? "new-password" : "current-password";
  loginSubmit.textContent = registering ? "Registrovat" : "Přihlásit se";
  const note = registering || registrationMode === "closed" ? Avatar.registrationNote(registrationMode) : "";
  registrationNoteEl.textContent = note;
  registrationNoteEl.hidden = !note;
  setStatus("");
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    /* An empty or non-JSON error body still gets the generic message below. */
  }
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "Něco se nepovedlo, zkus to znovu.");
  }
  return data;
}

async function submit(event) {
  event.preventDefault();
  const email = loginEmail.value;
  const password = loginPassword.value;
  if (!Avatar.isValidEmail(email)) {
    setStatus("Zadej platnou e-mailovou adresu.", "error");
    loginEmail.focus();
    return;
  }
  if (registering) {
    const problem = Avatar.passwordProblem(password, loginConfirm.value);
    if (problem) {
      setStatus(problem, "error");
      return;
    }
  } else if (!password) {
    setStatus("Zadej heslo.", "error");
    return;
  }
  loginSubmit.disabled = true;
  setStatus(registering ? "Zakládám účet…" : "Přihlašuji…");
  try {
    const data = await postJson(registering ? "auth/register" : "auth/login", { email, password });
    if (data.pending) {
      setRegistering(false);
      loginPassword.value = "";
      loginConfirm.value = "";
      setStatus("Registrace přijata. Přihlásit se půjde, až účet schválí administrátor.");
      return;
    }
    window.location.replace(`./${window.location.search}`);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    loginSubmit.disabled = false;
  }
}

async function init() {
  try {
    const response = await fetch("auth/me");
    const account = await response.json();
    if (!account.enabled || account.user) {
      window.location.replace(`./${window.location.search}`);
      return;
    }
    registrationMode = account.registration_mode || "approval";
  } catch {
    /* Keep the defaults; the server still enforces the real mode. */
  }
  registerTab.hidden = registrationMode === "closed";
  setRegistering(false);
  loginEmail.focus();
}

loginTab.addEventListener("click", () => setRegistering(false));
registerTab.addEventListener("click", () => setRegistering(true));
loginForm.addEventListener("submit", submit);
init();
