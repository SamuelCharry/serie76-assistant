"""Explicit local provisioning and legacy-history assignment. Never print credentials."""

import argparse
import getpass
import json
import os
import re
import secrets
from pathlib import Path
from uuid import uuid4, UUID

from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from .security import password_hash


def create_user(connection, email, name, password):
    email = email.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("Invalid email or name")
    identifier = uuid4()
    connection.execute("INSERT INTO series76.users(id,email,name,password_hash) VALUES (%s,%s,%s,%s)",
                       (identifier, email, name.strip(), password_hash(password)))
    return identifier


# Public assessment credentials: TEST ONLY, never use these accounts in production.
DEMO_USERS = [
    {"email": "demo@series76.test", "name": "Test-only demo", "password": "Series76-Demo-1"},
    {"email": "reviewer@series76.test", "name": "Test-only reviewer", "password": "Series76-Demo-2"},
]


def ensure_demo_users(connection):
    """Test-only provisioning; existing identities and passwords are never changed."""
    try:
        accounts = json.loads(os.environ["DEMO_USERS_JSON"]) if os.environ.get("DEMO_USERS_JSON", "").strip() else DEMO_USERS
        if not isinstance(accounts, list) or any(
            not isinstance(a, dict) or set(a) != {"email", "name", "password"}
            or any(not isinstance(a[k], str) for k in a) for a in accounts
        ):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("DEMO_USERS_JSON must be a JSON array of email/name/password objects (test only)") from None
    # Serialise concurrent startup provisioning without resetting existing accounts.
    connection.execute("SELECT pg_advisory_xact_lock(760003)")
    created = 0
    for account in accounts:
        email = account["email"].strip().lower()
        if not connection.execute("SELECT id FROM series76.users WHERE email=%s", (email,)).fetchone():
            create_user(connection, email, account["name"], account["password"])
            created += 1
    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ensure-demo-users", help="Provision public TEST-ONLY assessment accounts")
    user = sub.add_parser("create-user")
    user.add_argument("--email", required=True)
    user.add_argument("--name", required=True)
    demo = sub.add_parser("seed-demo")
    demo.add_argument("--output", type=Path, default=Path(".cache/auth-demo-credentials.json"))
    assign = sub.add_parser("assign-legacy")
    assign.add_argument("--session", type=UUID, required=True)
    assign.add_argument("--email", required=True)
    assign.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args()
    local_environment()
    if args.command == "ensure-demo-users":
        with connect() as connection:
            created = ensure_demo_users(connection)
        print(f"Test-only demo users: {created} created; existing accounts unchanged")
    elif args.command == "seed-demo":
        # Refuse to overwrite credentials or silently reset existing accounts.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            accounts = []
            try:
                with connect() as connection:
                    for number in (1, 2):
                        email = f"demo.{number}@example.test"
                        password = secrets.token_urlsafe(20)
                        create_user(connection, email, f"Demo {number}", password)
                        accounts.append({"email": email, "password": password})
                    json.dump(accounts, output, indent=2)
            except Exception:
                # The transaction rolls back; remove only the file just created by this command.
                output.close()
                args.output.unlink()
                raise
        print("Two demo accounts created. Credentials saved to the requested private local file.")
    elif args.command == "create-user":
        password = getpass.getpass("Password (12+ characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords differ")
        with connect() as connection:
            create_user(connection, args.email, args.name, password)
        print("Account created")
    else:
        with connect() as connection:
            row = connection.execute("""UPDATE series76.conversations SET owner_id=(
                SELECT id FROM series76.users WHERE email=%s AND active)
                WHERE id=%s AND owner_id IS NULL AND EXISTS(SELECT 1 FROM series76.users WHERE email=%s AND active)
                RETURNING id""", (args.email.strip().lower(), args.session, args.email.strip().lower())).fetchone()
            if row is None:
                raise ValueError("Unowned conversation or active destination account not found")
        print("One legacy conversation assigned explicitly")


if __name__ == "__main__":
    main()
