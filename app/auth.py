"""Login gate, daily request limit and the account/admin endpoints.

Everything here is inert unless AUTH_ENABLED is set: the middleware passes
requests straight through and the endpoints report that accounts are off.
"""

from __future__ import annotations

import math
import re
from contextvars import ContextVar
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse, RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.accounts import (
    AccountError,
    account_owner_id,
    AccountStore,
    HistoryLimitError,
    HistoryLimits,
    LoginThrottle,
    RateWindow,
    TooManyPendingError,
    User,
)
from app.config import get_settings
from app.models import (
    HistoryEntryRequest,
    HistoryImportRequest,
    PrefsRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    RegistrationModeRequest,
    UserUpdateRequest,
)

settings = get_settings()

# The logged-in user of the request being handled, set by AuthMiddleware.
# Starlette copies the context into the worker thread of a sync endpoint.
current_user: ContextVar[User | None] = ContextVar("current_user", default=None)

# Reachable without logging in. /settings stays public because the deploy
# health check polls it; it carries no secrets.
PUBLIC_PATHS = {
    "/health",
    "/settings",
    "/login",
    "/favicon.ico",
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
    "/logo_ufal_110u.png",
}
PUBLIC_PREFIXES = ("/static/", "/auth/")
# The endpoints that cost an LLM or mSearch call, one per user action.
# /chat/stream counts itself (count_request below), because an answer from the
# answer cache costs nothing and is not counted.
COUNTED_PATHS = {"/chat", "/retrieve", "/retrieve/stream", "/query-transform"}
QUOTA_HEADER = "X-Daily-Requests-Remaining"

# Generous enough for a room full of people signing up from one conference
# WiFi, low enough to stop scripted mass registration.
REGISTRATIONS_PER_WINDOW = 100
REGISTRATION_WINDOW_SECONDS = 600
MAX_PENDING_USERS = 200
# Failed logins for the whole server, so guessing with a new email each time
# (which the per-email lockout does not see) cannot keep the password check
# busy. Successful logins do not count, so a room logging in at once is fine.
FAILED_LOGINS_PER_WINDOW = 100
FAILED_LOGIN_WINDOW_SECONDS = 60

_store: AccountStore | None = None
login_throttle = LoginThrottle()
registration_rate = RateWindow(REGISTRATIONS_PER_WINDOW, REGISTRATION_WINDOW_SECONDS)
failed_login_rate = RateWindow(FAILED_LOGINS_PER_WINDOW, FAILED_LOGIN_WINDOW_SECONDS)


def get_store() -> AccountStore:
    global _store
    if _store is None:
        _store = AccountStore(
            settings.auth_db_path,
            default_registration_mode=settings.auth_registration_mode,
        )
    return _store


def set_store(store: AccountStore | None) -> None:
    """Point the app at another database (tests)."""

    global _store
    _store = store


def is_admin_user() -> bool:
    user = current_user.get()
    return user is not None and user.is_admin


def _app_path(scope: Scope) -> str:
    path = scope.get("path") or "/"
    root_path = scope.get("root_path") or ""
    if root_path and path.startswith(root_path):
        path = path[len(root_path):] or "/"
    return path


def _is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


def _quota_exceeded_detail(limit: int) -> str:
    return (
        f"Dnešní limit {limit} dotazů je vyčerpaný. Limit se obnoví o půlnoci; "
        "pokud potřebuješ víc, napiš administrátorovi."
    )


class AuthMiddleware:
    """Resolve the session cookie, guard non-public paths and count requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.auth_enabled:
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        store = get_store()
        user = await run_in_threadpool(store.session_user, request.cookies.get(settings.auth_cookie_name))
        path = _app_path(scope)
        if user is None and not _is_public(path):
            if path == "/" and request.method in ("GET", "HEAD"):
                # Relative, so it also works when the app is served under a prefix.
                # The query (e.g. ?shared=<id>) rides along for after the login.
                query = scope.get("query_string", b"").decode("latin-1")
                response = RedirectResponse(f"login?{query}" if query else "login", status_code=303)
            else:
                response = JSONResponse({"detail": "Přihlas se prosím."}, status_code=401)
            await response(scope, receive, send)
            return

        if user is not None and path in COUNTED_PATHS and request.method == "POST":
            limit = settings.user_daily_request_limit
            remaining = await run_in_threadpool(store.consume_request, user, limit)
            if remaining is None:
                response = JSONResponse(
                    {"detail": _quota_exceeded_detail(limit)},
                    status_code=429,
                    headers={QUOTA_HEADER: "0"},
                )
                await response(scope, receive, send)
                return
            send = _with_header(send, QUOTA_HEADER, str(remaining))

        token = current_user.set(user)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user.reset(token)


def count_request() -> dict[str, str]:
    """Count one request of the logged-in user, for an endpoint that counts
    itself. Returns the quota header to send; raises 429 over the limit."""

    user = current_user.get()
    if not settings.auth_enabled or user is None:
        return {}
    limit = settings.user_daily_request_limit
    remaining = get_store().consume_request(user, limit)
    if remaining is None:
        raise HTTPException(status_code=429, detail=_quota_exceeded_detail(limit), headers={QUOTA_HEADER: "0"})
    return {QUOTA_HEADER: str(remaining)}


def _with_header(send: Send, name: str, value: str) -> Send:
    async def wrapped(message: Message) -> None:
        if message["type"] == "http.response.start":
            MutableHeaders(scope=message).append(name, value)
        await send(message)

    return wrapped


# Endpoints ------------------------------------------------------------------

router = APIRouter()


def account_payload(user: User | None) -> dict[str, object]:
    """What the browser needs to know about accounts and the current user."""

    if not settings.auth_enabled:
        return {"enabled": False}
    store = get_store()
    limit = settings.user_daily_request_limit
    payload: dict[str, object] = {
        "enabled": True,
        "registration_mode": store.registration_mode(),
        "daily_limit": limit,
        "user": None,
    }
    if user is not None:
        used = store.requests_today(user.id)
        # history_mode / author_name are None until the user chooses.
        payload["user"] = {"email": user.email, "is_admin": user.is_admin, **store.prefs(user.id)}
        payload["requests_today"] = used
        # None means unlimited.
        payload["requests_remaining"] = None if user.is_admin or limit <= 0 else max(limit - used, 0)
    return payload


def _require_enabled() -> AccountStore:
    if not settings.auth_enabled:
        raise HTTPException(status_code=404, detail="Uživatelské účty nejsou zapnuté.")
    return get_store()


def _require_user() -> User:
    _require_enabled()
    user = current_user.get()
    if user is None:
        raise HTTPException(status_code=401, detail="Přihlas se prosím.")
    return user


def _require_admin() -> User:
    user = _require_user()
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Tato akce vyžaduje administrátora.")
    return user


def _cookie_path(request: Request) -> str:
    return (request.scope.get("root_path") or "").rstrip("/") or "/"


def _start_session(store: AccountStore, user: User, request: Request, response: Response) -> None:
    lifetime = timedelta(days=settings.auth_session_days)
    token = store.create_session(user.id, lifetime, password_hash=user.password_hash)
    if token is None:
        # The password was changed or the account blocked while it was checked.
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo.")
    response.set_cookie(
        settings.auth_cookie_name,
        token,
        max_age=int(lifetime.total_seconds()),
        path=_cookie_path(request),
        httponly=True,
        secure=settings.auth_cookie_secure,
        # Lax keeps the cookie off cross-site POSTs; the JSON endpoints also
        # need a CORS preflight that this app never grants.
        samesite="lax",
    )


def _account_error(exc: AccountError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/auth/me")
def auth_me() -> dict[str, object]:
    return account_payload(current_user.get())


@router.post("/auth/login")
def auth_login(body: LoginRequest, request: Request, response: Response) -> dict[str, object]:
    store = _require_enabled()
    key = body.email.strip().lower()
    # Both checked before the password, the expensive part.
    if failed_login_rate.full():
        raise HTTPException(status_code=429, detail="Právě je příliš mnoho neúspěšných přihlášení. Zkus to za minutu.")
    wait = login_throttle.begin(key)
    if wait:
        raise HTTPException(
            status_code=429,
            detail=f"Příliš mnoho neúspěšných pokusů. Zkus to znovu za {math.ceil(wait / 60)} min.",
        )
    user = store.authenticate(body.email, body.password)
    if user is None:
        failed_login_rate.record()
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo.")
    login_throttle.succeeded(key)
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Účet čeká na schválení administrátorem.")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Účet je zablokovaný.")
    _start_session(store, user, request, response)
    return account_payload(user)


@router.post("/auth/register")
def auth_register(body: LoginRequest, request: Request, response: Response) -> dict[str, object]:
    store = _require_enabled()
    mode = store.registration_mode()
    if mode == "closed":
        raise HTTPException(status_code=403, detail="Registrace je momentálně uzavřená.")
    # Both checks run before the password is hashed, the expensive part.
    # create_user checks the pending cap again in the INSERT, for parallel requests.
    too_many_pending = HTTPException(
        status_code=429,
        detail="Na schválení už čeká příliš mnoho registrací. Zkus to později nebo napiš administrátorovi.",
    )
    if mode == "approval" and store.count_users("pending") >= MAX_PENDING_USERS:
        raise too_many_pending
    if not registration_rate.allow():
        raise HTTPException(status_code=429, detail="Právě se registruje příliš mnoho lidí. Zkus to za pár minut.")
    try:
        user = store.create_user(
            body.email,
            body.password,
            status="active" if mode == "open" else "pending",
            max_pending=MAX_PENDING_USERS,
        )
    except TooManyPendingError as exc:
        raise too_many_pending from exc
    except AccountError as exc:
        raise _account_error(exc) from exc
    if user.status != "active":
        return {**account_payload(None), "pending": True}
    _start_session(store, user, request, response)
    return {**account_payload(user), "pending": False}


@router.post("/auth/logout")
def auth_logout(request: Request, response: Response) -> dict[str, object]:
    store = _require_enabled()
    store.delete_session(request.cookies.get(settings.auth_cookie_name))
    response.delete_cookie(
        settings.auth_cookie_name,
        path=_cookie_path(request),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
    )
    return account_payload(None)


@router.post("/auth/password")
def auth_change_password(body: PasswordChangeRequest, request: Request) -> dict[str, object]:
    user = _require_user()
    store = get_store()
    # 400, not 401: the session is fine, only the typed password is wrong.
    if login_throttle.begin(user.email):
        raise HTTPException(status_code=429, detail="Příliš mnoho neúspěšných pokusů. Zkus to později.")
    checked = store.authenticate(user.email, body.current_password)
    if checked is None:
        raise HTTPException(status_code=400, detail="Současné heslo není správné.")
    login_throttle.succeeded(user.email)
    try:
        changed = store.set_password(
            user.id,
            body.new_password,
            keep_session=request.cookies.get(settings.auth_cookie_name),
            replaces=checked.password_hash,
        )
    except AccountError as exc:
        raise _account_error(exc) from exc
    if not changed:
        # An admin set a new password while the current one was being checked.
        raise HTTPException(status_code=409, detail="Heslo se mezitím změnilo. Přihlas se znovu.")
    return account_payload(user)


@router.get("/admin/users")
def admin_list_users() -> dict[str, object]:
    _require_admin()
    store = get_store()
    return {
        "users": store.list_users(),
        "registration_mode": store.registration_mode(),
        "daily_limit": settings.user_daily_request_limit,
    }


def _existing_user(store: AccountStore, user_id: int) -> User:
    user = store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Uživatel neexistuje.")
    return user


@router.patch("/admin/users/{user_id}")
def admin_update_user(user_id: int, body: UserUpdateRequest) -> dict[str, object]:
    admin = _require_admin()
    store = get_store()
    _existing_user(store, user_id)
    if user_id == admin.id and (
        (body.status is not None and body.status != "active") or body.is_admin is False
    ):
        # Otherwise the last admin could lock everyone out of user management.
        raise HTTPException(status_code=400, detail="Svůj vlastní účet nemůžeš zablokovat ani mu odebrat práva admina.")
    store.update_user(user_id, status=body.status, is_admin=body.is_admin)
    return {"ok": True}


@router.post("/admin/users/{user_id}/password")
def admin_reset_password(user_id: int, body: PasswordResetRequest) -> dict[str, object]:
    _require_admin()
    store = get_store()
    _existing_user(store, user_id)
    try:
        store.set_password(user_id, body.password)
    except AccountError as exc:
        raise _account_error(exc) from exc
    return {"ok": True}


@router.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(user_id: int) -> Response:
    admin = _require_admin()
    store = get_store()
    _existing_user(store, user_id)
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Svůj vlastní účet nemůžeš smazat.")
    store.delete_user(user_id)
    return Response(status_code=204)


@router.put("/admin/registration-mode")
def admin_set_registration_mode(body: RegistrationModeRequest) -> dict[str, object]:
    _require_admin()
    get_store().set_registration_mode(body.mode)
    return {"registration_mode": body.mode}


# History ------------------------------------------------------------------
# The logged-in user's own history and conversations (see docs/accounts.md).
# The browser keeps the working copy in memory and saves each changed entry
# here, so these are per-entry calls rather than one big list.

HISTORY_KIND_BY_PATH = {"history": "history", "conversations": "conversation"}
# The browser's ids are Date.now() numbers; anything id-like is accepted.
HISTORY_ENTRY_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def history_limits() -> HistoryLimits:
    return HistoryLimits(
        max_entries=settings.user_history_max_entries,
        max_bytes=int(settings.user_history_max_mb * 1024 * 1024),
    )


def history_storage_off() -> bool:
    """True when the logged-in user chose not to store history ("neukládat"):
    their answers then do not go into the shared answer cache either."""

    user = current_user.get()
    return settings.auth_enabled and user is not None and get_store().history_mode(user.id) == "none"


def _history_kind(kind: str) -> str:
    if kind not in HISTORY_KIND_BY_PATH:
        raise HTTPException(status_code=404, detail="Neznámý druh historie.")
    return HISTORY_KIND_BY_PATH[kind]


def _history_entry_id(value: object) -> str:
    entry_id = str(value if value is not None else "")
    if not HISTORY_ENTRY_ID_RE.match(entry_id):
        raise HTTPException(status_code=400, detail="Neplatné id položky historie.")
    return entry_id


def _usage_payload(usage: dict[str, int]) -> dict[str, object]:
    limits = history_limits()
    return {**usage, "max_entries": limits.max_entries, "max_bytes": limits.max_bytes}


@router.put("/me/prefs")
def set_my_prefs(body: PrefsRequest) -> dict[str, object]:
    user = _require_user()
    store = get_store()
    if body.history_mode is not None:
        store.set_history_mode(user.id, body.history_mode)
    if body.author_name is not None:
        store.set_author_name(user.id, body.author_name)
    return store.prefs(user.id)


# Shared-item ownership ------------------------------------------------------
# Without accounts a shared item belongs to the random id of the browser that
# made it. With accounts, new items belong to the account ("user:<id>"), and
# the browser ids a user sends are linked to their account on first use, so
# what they shared before logging in (or from another browser) stays theirs.


def requester_owner_ids(owner_id: str | None) -> frozenset[str]:
    """The owner ids the requester may act as."""

    requester = (owner_id or "").strip()
    user = current_user.get()
    if not settings.auth_enabled or user is None:
        return frozenset({requester}) if requester else frozenset()
    store = get_store()
    if requester:
        store.link_owner_id(user.id, requester)
    return frozenset(store.owner_ids(user.id))


def new_owner_id(owner_id: str | None) -> str:
    """The owner id a newly shared item is stored with."""

    user = current_user.get()
    if settings.auth_enabled and user is not None:
        # Links the browser id too, as a read would.
        requester_owner_ids(owner_id)
        return account_owner_id(user.id)
    return (owner_id or "").strip()


@router.get("/me/history")
def list_my_history() -> dict[str, object]:
    user = _require_user()
    store = get_store()
    entries = store.list_history(user.id)
    return {
        "history": entries["history"],
        "conversations": entries["conversation"],
        "usage": _usage_payload(store.history_usage(user.id)),
    }


@router.put("/me/history/{kind}/{entry_id}")
def put_my_history_entry(kind: str, entry_id: str, body: HistoryEntryRequest) -> dict[str, object]:
    user = _require_user()
    kind = _history_kind(kind)
    entry_id = _history_entry_id(entry_id)
    if _history_entry_id(body.entry.get("id")) != entry_id:
        raise HTTPException(status_code=400, detail="Id v adrese a v položce se liší.")
    try:
        usage = get_store().put_history(user.id, kind, entry_id, body.entry, history_limits())
    except HistoryLimitError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return {"usage": _usage_payload(usage)}


@router.delete("/me/history/{kind}/{entry_id}", status_code=204)
def delete_my_history_entry(kind: str, entry_id: str) -> Response:
    user = _require_user()
    get_store().delete_history(user.id, _history_kind(kind), _history_entry_id(entry_id))
    return Response(status_code=204)


@router.post("/me/history/import")
def import_my_history(body: HistoryImportRequest) -> dict[str, object]:
    """Copy entries from the browser; ids already on the server are kept as they are."""

    user = _require_user()
    items = [
        (kind, _history_entry_id(entry.get("id")), entry)
        for kind, entries in (("history", body.history), ("conversation", body.conversations))
        for entry in entries
    ]
    store = get_store()
    result = store.import_history(user.id, items, history_limits())
    return {**result, "usage": _usage_payload(store.history_usage(user.id))}
