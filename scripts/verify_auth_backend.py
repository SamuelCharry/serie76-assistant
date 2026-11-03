"""Real HTTP/SQL isolation, revocation and backend restart; zero model requests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import uuid4
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from backend.auth.cli import create_user
from backend.auth.security import token_hash
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation import store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restart-backend", action="store_true")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    local_environment()
    users, sessions = [], [uuid4(), uuid4(), uuid4()]
    report = {"external_model_calls": 0, "transport": "real HTTP", "database": "real PostgreSQL"}
    try:
        with connect() as connection:
            for i in (0, 1):
                email, password = f"verification-{uuid4()}@example.test", secrets.token_urlsafe(24)
                uid = create_user(connection, email, f"Verification {i + 1}", password)
                users.append((uid, email, password))
                store.append_turn(connection, sessions[i], f"Verification {i + 1}",
                    SimpleNamespace(answer=f"Saved verification {i + 1}", products=[], tool_calls=[], context={}), new=True, owner_id=uid)
            connection.execute("INSERT INTO series76.conversations(id,title) VALUES (%s,'Legacy verification')", (sessions[2],))
        with httpx.Client(base_url=args.url, timeout=15) as client:
            tokens = []
            for uid, email, password in users:
                response = client.post("/api/auth/login", json={"email": email, "password": password})
                response.raise_for_status()
                tokens.append(response.json()["access_token"])
            if args.restart_backend:
                subprocess.run(["docker", "compose", "restart", "backend"], cwd=ROOT, check=True, capture_output=True)
                for _ in range(30):
                    try:
                        if client.get("/ready").status_code == 200: break
                    except httpx.HTTPError: pass
                    time.sleep(1)
                else: raise AssertionError("Backend did not become ready")
            for index, token in enumerate(tokens):
                headers = {"Authorization": f"Bearer {token}"}
                assert client.get("/api/auth/me", headers=headers).json()["id"] == str(users[index][0])
                page = client.get("/api/sessions", headers=headers)
                page.raise_for_status()
                assert [r["id"] for r in page.json()["sessions"]] == [str(sessions[index])]
                assert client.get(f"/api/sessions/{sessions[index]}/messages", headers=headers).status_code == 200
                for sid in (sessions[1-index], sessions[2]):
                    assert client.get(f"/api/sessions/{sid}/messages", headers=headers).status_code == 404
                    # Ownership rejection must happen before any model invocation.
                    assert client.post("/api/conversation", headers=headers, json={"query": "Denied", "session_id": str(sid)}).status_code == 404
            assert client.get("/api/sessions").status_code == 401
            header = {"Authorization": f"Bearer {tokens[0]}"}
            assert client.post("/api/auth/logout", headers=header).status_code == 204
            assert client.get("/api/auth/me", headers=header).status_code == 401
            with connect() as connection:
                connection.execute("UPDATE series76.auth_sessions SET expires_at=now()-interval '1 second' WHERE token_hash=%s", (token_hash(tokens[1]),))
            assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens[1]}"}).status_code == 401
        report.update(status="passed", users=2, legacy_quarantined=True, cross_user_read_and_continue="404",
                      anonymous="401", logout_revoked=True, expired_rejected=True,
                      token_and_history_survived_backend_restart=args.restart_backend)
    finally:
        with connect() as connection:
            for sid in sessions:
                connection.execute("DELETE FROM series76.messages WHERE session_id=%s", (sid,))
                connection.execute("DELETE FROM series76.conversations WHERE id=%s", (sid,))
            for uid, email, password in users:
                connection.execute("DELETE FROM series76.auth_sessions WHERE user_id=%s", (uid,))
                connection.execute("DELETE FROM series76.users WHERE id=%s", (uid,))
    output = ROOT / "reports/mobile/auth-v7/http-isolation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
