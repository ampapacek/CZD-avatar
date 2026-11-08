# User accounts

Optional login for instances whose URL might spread further than intended, so that strangers cannot run up AI Ufal or mSearch usage. Off by default; with `AUTH_ENABLED` unset the app behaves exactly as without accounts.

## What it does

- Every page and API call needs a login, except `/health`, `/settings` (the deploy health check polls it), static files, the login page and `/auth/*`. A logged-out visit to `/` is redirected to `login`.
- The email is the username. It is checked for shape (something before the `@`, a domain with a dot) and uniqueness, lower-cased, and never sent anything; there is no email verification.
- Each user has `USER_DAILY_REQUEST_LIMIT` requests per Prague calendar day (default 100). Counted are `/chat`, `/chat/stream`, `/retrieve`, `/retrieve/stream` and `/query-transform` (so an answer with a query transform uses two), including requests made with the user's own API key. An answer from the [answer cache](architecture.md#answer-cache) is not counted: `/chat/stream` counts itself after the cache lookup, the others are counted by the middleware. Over the limit the endpoint answers 429 with a readable message. Counted responses carry `X-Daily-Requests-Remaining` (`-1` = unlimited). Admins are not limited, but their requests are counted for the statistics. A request is counted before it runs, so one that then fails (an invalid body, an upstream error) still uses quota; a client cannot get free attempts by sending bad requests.
- Registration has three modes that an admin switches in the app: `open` (the new account works at once), `approval` (the account waits until an admin activates it; the default) and `closed`. `AUTH_REGISTRATION_MODE` only sets the mode used until an admin picks one.
- Admins manage users in the `Účet` dialog: activate, block, make admin, set a new password (not on their own row, which would log them out; they use `Změnit heslo`), delete, with today's and total request counts. An admin cannot block, demote or delete their own account.
- A logged-in admin counts as having entered `ADMIN_PASSWORD`: all models are unlocked and shared prompts, placeholders and history can be edited without the shared password. The shared password keeps working as before.
- History and conversations are stored with the account on the server, unless the user keeps them in the browser or does not store them (see [History](#history)). Local prompt profiles and API keys stay in the browser; API keys never go to the server.
- Shared history, prompts and placeholders belong to the account, including those shared from a browser before accounts (see [Shared items](#shared-items)). The sharing name (`Sdílím jako`) is kept with the account.

## Setup

```bash
# .env
AUTH_ENABLED=true
USER_DAILY_REQUEST_LIMIT=100

# first admin, from the checkout the app runs from (prompts for the password)
uv run python scripts/users.py create-admin admin@example.cz
```

`scripts/users.py set-password <email>` resets a forgotten password from the shell (it also ends that user's sessions), `create-admin` on an existing account makes it an active admin and always sets a new password (someone could have registered the address first, since emails are not verified), ending its sessions, and `list` prints users with their request counts.

Settings:

- `AUTH_ENABLED` (default `false`)
- `AUTH_DB_PATH` (default `data/users.sqlite3`, gitignored)
- `AUTH_REGISTRATION_MODE` (`open`, `approval` or `closed`; default `approval`)
- `AUTH_SESSION_DAYS` (default `30`)
- `AUTH_COOKIE_SECURE` (default `true`; browsers keep Secure cookies off plain http except on `localhost`, so turn it off only for a test server reached over plain http)
- `AUTH_COOKIE_NAME` (default `czd_session`; give two instances on the same host different names)
- `USER_DAILY_REQUEST_LIMIT` (default `100`; `0` turns the limit off)
- `USER_HISTORY_MAX_ENTRIES` (default `2000`) and `USER_HISTORY_MAX_MB` (default `50`): the server history limit per user

## How it works

- `app/accounts.py`: the SQLite store (users, sessions, daily usage, the registration mode), password hashing and the login throttle. Python's `sqlite3`, one short connection per operation; fine for the expected tens of users. The database file (and its `-wal`/`-shm` files) is readable by the app's OS user only (`0600`), also when it existed before; run `scripts/users.py` as that user.
- Passwords are hashed with Argon2 through `pwdlib`, and re-hashed on login when its recommended parameters change. A login for an unknown email verifies against a dummy hash, so it takes as long as a wrong password.
- Sessions are random tokens (`secrets.token_urlsafe`) in an HttpOnly, Secure, SameSite=Lax cookie. Only their SHA-256 is stored, so a copy of the database holds no usable sessions. Logout, blocking and deleting a user end sessions immediately. A password change ends all other sessions of the user; the session that made the change stays logged in. A change only goes through if the current password checked is still the stored one, so a change started just before an admin reset cannot overwrite the reset (it answers 409).
- After 5 wrong passwords for one email, logins for it are refused for 5 minutes. Each attempt is counted before the password is checked (and forgotten on success), so parallel requests cannot all get through before the lock. Failures older than 5 minutes are forgotten and at most 10,000 emails are tracked. The counts are in memory and reset on restart.
- Across all emails, at most 100 failed logins per minute; above that every login answers 429 until the minute passes, without checking the password. Successful logins do not count. Someone guessing can keep new logins blocked this way, but existing sessions keep working.
- A login only gets a session if, after the password check, the account is still active and its password is still the one that was checked (one SQL statement). A password reset or block during the check therefore wins.
- At most 4 password hashes or checks run at once (Argon2 takes tens of MB each); further registrations and logins wait for a slot instead of exhausting memory.
- Registration: at most 100 new accounts per 10 minutes for the whole server (enough for a room signing up from one WiFi, no per-IP limit for that reason), and in approval mode at most 200 accounts waiting for approval. Both answer 429 and are checked before the password is hashed; the pending cap is checked once more in the INSERT, so parallel registrations cannot exceed it. The numbers are constants in `app/auth.py`.
- `app/auth.py`: `AuthMiddleware` resolves the cookie, guards non-public paths and counts the endpoints above before they run (check and increment are one SQL statement); the `/auth/*` and `/admin/*` endpoints. The middleware puts the user in a context variable that `_admin_authorized` in `app/main.py` reads.
- Cookie path is the ASGI `root_path` when the proxy sets one, otherwise `/`.
- Cross-site requests: SameSite=Lax keeps the cookie off cross-site POSTs, and every state-changing endpoint takes JSON or uses PUT/PATCH/DELETE, which need a CORS preflight the app never grants.
- Frontend: `app/static/login.html` + `login.js` (login and registration), the `Účet` button and dialog in `index.html`/`app.js`, shared helpers in `frontend/account.js`. A 401 from any API call sends the browser back to the login page.

## History

Each user picks where their history and conversations go, in the History dialog under `Úložiště` (the `Účet` dialog links there):

- `server` (`Na serveru`): rows in the accounts database, visible on every device the user logs in from.
- `browser` (`Jen v tomto prohlížeči`): localStorage, exactly as without accounts, including the storage meter and free-up dialog.
- `none` (`Neukládat`): kept only in the open page until it is closed or reloaded. The user's `/chat/stream` answers are also not written to the [answer cache](architecture.md#answer-cache) (a cached answer is still replayed; cache warming always stores).

The choice is stored per account (`user_prefs.history_mode`), not per browser. Until the user makes one it is `NULL`, and each browser decides: one that already holds history (entries, or a conversation with messages) keeps showing it from the browser, so nobody's history seems to vanish after the first login; one with nothing in it uses the server. In the first case a notice above `Moje historie` says how much is in the browser and offers `Ukládat na server` (saves the choice and uploads the browser's history) or `Nechat v prohlížeči` (saves the choice). On the server the server mode is the default, so `Neukládat` is the only choice that changes server behaviour.

Switching never moves or deletes anything: it only decides where new entries are saved and which list is shown, so switching back shows the old entries again. While the server copy is shown and the browser still holds entries the server lacks, the same notice offers `Nahrát na server` (or `Skrýt`, remembered in the browser), and `Úložiště` has `Nahrát historii z prohlížeče na server`. Uploading adds entries by id (an id already on the server keeps the server's version) and leaves the browser copy in place.

- Storage: `history_entries(user_id, kind, entry_id, created_at, updated_at, size, payload)`, one row per history entry or per conversation (rewritten after each turn), so two tabs or devices never overwrite each other's other entries. `payload` is the browser's entry as JSON after the same compaction as in localStorage. Deleting a user deletes their rows and preference (foreign keys with `ON DELETE CASCADE`).
- Limit: a save that would take a user over `USER_HISTORY_MAX_ENTRIES` or `USER_HISTORY_MAX_MB` answers 413 with a readable message; nothing old is dropped. The import adds what fits and reports the rest.
- Frontend: `frontend/history-store.js` (`PageHistoryStore`) keeps the working copy in memory, so `app.js` reads and writes whole lists synchronously as before. Each save is diffed against that copy and only changed entries are sent, one request per entry, after a short delay (a conversation rewritten on every streamed token becomes one request once the stream pauses). A failed save is reported and retried with the entry's next save. The browser mode keeps its own code path in `app.js`. Until `/settings` says which mode applies, entries wait in memory and are then added to the chosen store.
- The page loads the whole server history at start (`GET /me/history` returns full entries). Fine at the expected sizes; if users get near the limit, switch to a light list plus fetching one entry on demand.
- Privacy: anyone with access to the database file can read the stored conversations. Shared history items are a separate, explicit action and still go to the shared history.

## Shared items

Without accounts, a shared history item, prompt or placeholder belongs to the random owner id of the browser that made it (`czdemos4ai-browser-owner-id` in localStorage). With accounts:

- New items are stored with the account's owner id, `user:<id>`, so they are the user's from every browser.
- Each browser owner id a logged-in user sends is linked to their account (`owner_links`), the first time and to the first account only. Items shared from that browser before accounts, or before the user logged in there, become theirs on every device. On a computer several people used before accounts, the first to log in gets the old items; nobody else can claim them.
- An id starting with `user:` is never linked, so nobody can claim an account's items by sending its id.
- `requester_owner_ids` and `new_owner_id` in `app/auth.py` do this; `_owned_by` in `app/main.py` accepts any of the requester's ids. The browser still only learns `mine`, never an owner id.

The sharing name (`Sdílím jako`) is `user_prefs.author_name`. Until the user sets one, it is the name typed in that browser before accounts (saved to the account on the next load) or the part of the email before the `@`. The email itself is never shown to others.

## API

- `GET /auth/me`: accounts on/off, registration mode, daily limit, the current user and today's count (also in `/settings` as `account`)
- `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`, `POST /auth/password`
- `PUT /me/prefs` (`{"history_mode": "server" | "browser" | "none", "author_name": "..."}`, either field alone; returns both). `/auth/me` carries them as `user.history_mode` and `user.author_name`, `null` until set.
- `GET /me/history` (`history`, `conversations`, `usage` with the limits), `PUT /me/history/{history|conversations}/{id}` (`{"entry": {...}}`, its `id` must match), `DELETE /me/history/{history|conversations}/{id}`, `POST /me/history/import` (`{"history": [...], "conversations": [...]}`; returns `imported`, `existing`, `over_limit`)
- `GET /admin/users`, `PATCH /admin/users/{id}`, `POST /admin/users/{id}/password`, `DELETE /admin/users/{id}`, `PUT /admin/registration-mode`
