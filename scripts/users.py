#!/usr/bin/env python3
"""Manage user accounts from the server's shell.

Creates the first admin and resets passwords without going through the app.
Everything else (approving, blocking, deleting users) is in the app's admin
dialog. Run from the checkout so `.env` and AUTH_DB_PATH resolve as for the app:

    uv run python scripts/users.py create-admin admin@example.cz
    uv run python scripts/users.py set-password user@example.cz
    uv run python scripts/users.py list
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.accounts import AccountError, AccountStore, normalize_email  # noqa: E402
from app.config import get_settings  # noqa: E402


def read_password(password: str | None) -> str:
    if password is not None:
        return password
    first = getpass.getpass("Nové heslo: ")
    if getpass.getpass("Heslo znovu: ") != first:
        raise AccountError("Hesla se neshodují.")
    return first


def create_admin(store: AccountStore, email: str, password: str | None) -> str:
    """Create an active admin, or promote and activate an existing account.

    Promoting always sets a new password and ends the account's sessions:
    without email verification, anyone could have registered the address
    first, with a password of their choosing.
    """

    email = normalize_email(email)
    existing = store.find_user(email)
    if existing is None:
        store.create_user(email, read_password(password), status="active", is_admin=True)
        return f"Admin {email} vytvořen."
    print(f"Účet {email} už existuje (stav: {existing.status}); nastav mu nové heslo.")
    store.set_password(existing.id, read_password(password))
    store.update_user(existing.id, status="active", is_admin=True)
    return f"Účet {email} je teď aktivní admin s novým heslem; jeho dřívější přihlášení byla ukončena."


def set_password(store: AccountStore, email: str, password: str | None) -> str:
    user = store.find_user(normalize_email(email))
    if user is None:
        raise AccountError(f"Účet {email} neexistuje.")
    store.set_password(user.id, read_password(password))
    return f"Heslo pro {user.email} změněno; jeho přihlášení byla ukončena."


def list_users(store: AccountStore) -> str:
    rows = store.list_users()
    if not rows:
        return "Žádní uživatelé."
    lines = [f"{'e-mail':40} {'stav':9} {'admin':5} {'dnes':>5} {'celkem':>7}"]
    for row in rows:
        lines.append(
            f"{row['email']:40} {row['status']:9} {'ano' if row['is_admin'] else '':5} "
            f"{row['requests_today']:>5} {row['requests_total']:>7}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage CZD-avatar user accounts.")
    parser.add_argument("--db", type=Path, help="user database (default: AUTH_DB_PATH from .env)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("create-admin", "create an admin, or make an existing account an active admin"),
        ("set-password", "set a user's password and end their sessions"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("email")
        # For scripting only; the prompt keeps the password out of shell history.
        command.add_argument("--password", help=argparse.SUPPRESS)
    commands.add_parser("list", help="list users with today's and total request counts")
    args = parser.parse_args(argv)

    settings = get_settings()
    store = AccountStore(args.db or settings.auth_db_path, default_registration_mode=settings.auth_registration_mode)
    try:
        if args.command == "create-admin":
            print(create_admin(store, args.email, args.password))
        elif args.command == "set-password":
            print(set_password(store, args.email, args.password))
        else:
            print(list_users(store))
    except AccountError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
