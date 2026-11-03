# User accounts

Optional login for instances whose URL might spread further than intended, so that strangers cannot run up AI Ufal or mSearch usage. Off by default; with `AUTH_ENABLED` unset the app behaves exactly as without accounts.

## What it does

- Every page and API call needs a login, except `/health`, `/settings` (the deploy health check polls it), static files, the login page and `/auth/*`. A logged-out visit to `/` is redirected to `login`.
- The email is the username. It is checked for shape (something before the `@`, a domain with a dot) and uniqueness, lower-cased, and never sent anything; there is no email verification.
- Each user has `USER_DAILY_REQUEST_LIMIT` requests per Prague calendar day (default 100). Counted are `/chat`, `/chat/stream`, `/retrieve`, `/retrieve/stream` and `/query-transform` (so an answer with a query transform uses two), including requests made with the user's own API key. Over the limit the endpoint answers 429 with a readable message. Counted responses carry `X-Daily-Requests-Remaining` (`-1` = unlimited). Admins are not limited, but their requests are counted for the statistics. A request is counted before it runs, so one that then fails (an invalid body, an upstream error) still uses quota; a client cannot get free attempts by sending bad requests.
- Registration has three modes that an admin switches in the app: `open` (the new account works at once), `approval` (the account waits until an admin activates it; the default) and `closed`. `AUTH_REGISTRATION_MODE` only sets the mode used until an admin picks one.
- Admins manage users in the `Účet` dialog: activate, block, make admin, set a new password (not on their own row, which would log them out; they use `Změnit heslo`), delete, with today's and total request counts. An admin cannot block, demote or delete their own account.
- A logged-in admin counts as having entered `ADMIN_PASSWORD`: all models are unlocked and shared prompts, placeholders and history can be edited without the shared password. The shared password keeps working as before.
- History, local prompt profiles and API keys stay in the browser; they are not tied to the account.

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

## API

- `GET /auth/me`: accounts on/off, registration mode, daily limit, the current user and today's count (also in `/settings` as `account`)
- `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`, `POST /auth/password`
- `GET /admin/users`, `PATCH /admin/users/{id}`, `POST /admin/users/{id}/password`, `DELETE /admin/users/{id}`, `PUT /admin/registration-mode`
