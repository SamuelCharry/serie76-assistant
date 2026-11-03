"""Verify persisted Android contracts across a Docker restart, without a paid LLM.

Only routing is scripted. Tools run against real PostgreSQL. The script creates
one marked verification conversation and deletes only its own UUID afterwards.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from uuid import uuid4
import secrets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation.agent import run_agent
from backend.conversation import store
from backend.auth.cli import create_user


class RoutingFixture:
    def bind_tools(self, tools, **kwargs):
        return self

    def invoke(self, messages, **kwargs):
        return SimpleNamespace(tool_calls=[{
            "id": "verification", "name": "get_actuator", "args": {
                "part_numbers": ["761A00-11300000/A", "761B00-11300000/A"], "focus": "torque"
            }
        }])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restart", action="store_true", help="Restart existing db/backend without removing volumes")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/mobile/auth-v7/persistence.json")
    args = parser.parse_args()
    local_environment()
    session_id = uuid4()
    email, password = f"verification-{uuid4()}@example.test", secrets.token_urlsafe(24)
    user_id = None
    report = {"status": "running", "model": "scripted routing fixture; no external LLM", "postgres": "real"}
    try:
        with connect() as connection:
            user_id = create_user(connection, email, "Temporary verification", password)
            result = run_agent(connection, "Compare the torque of 761A00-11300000/A and 761B00-11300000/A", [], {}, model=RoutingFixture())
            assert len(result.products) == 2, "Verification must restore actual catalogue products"
            message_id = store.append_turn(connection, session_id, "[Verification] Compare two actuators", result, new=True, owner_id=user_id)
        with httpx.Client(base_url=args.url, timeout=10) as client:
            login = client.post("/api/auth/login", json={"email": email, "password": password})
            login.raise_for_status()
            token = login.json()["access_token"]
        if args.restart:
            subprocess.run(["docker", "compose", "restart", "db", "backend"], cwd=ROOT, check=True, capture_output=True)
        with httpx.Client(base_url=args.url, timeout=10, headers={"Authorization": f"Bearer {token}"}) as client:
            for attempt in range(30):
                try:
                    if client.get("/ready").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise AssertionError("Backend did not become ready")
            page = client.get(f"/api/sessions/{session_id}/messages"); page.raise_for_status()
            assert client.get("/api/auth/me").status_code == 200
            history = page.json()["messages"]
            assert len(history) == 2
            assert history[1]["id"] == str(message_id)
            assert history[1]["products"] == result.products
            assert "tool_calls" not in history[1] and "context" not in history[1]
            sessions = client.get("/api/sessions?limit=100"); sessions.raise_for_status()
            assert any(s["id"] == str(session_id) for s in sessions.json()["sessions"])
            debug = client.get(f"/api/messages/{message_id}/debug")
            # Default false and explicit opt-in both have defined behavior.
            assert debug.status_code in (200, 404)
            if debug.status_code == 200:
                assert debug.json()["tool_calls"] == result.tool_calls
        report.update(status="passed", restart_requested=args.restart, restored_messages=len(history),
                      restored_products=len(history[1]["products"]), debug_status=debug.status_code,
                      no_tool_details_in_public_history=True, external_model_calls=0, authenticated=True,
                      session_token_survived_restart=args.restart)
    finally:
        with connect() as connection:
            # Exact identifiers created by this run only; never delete existing user sessions.
            connection.execute("DELETE FROM series76.messages WHERE session_id=%s", (session_id,))
            connection.execute("DELETE FROM series76.conversations WHERE id=%s", (session_id,))
            if user_id:
                connection.execute("DELETE FROM series76.auth_sessions WHERE user_id=%s", (user_id,))
                connection.execute("DELETE FROM series76.users WHERE id=%s", (user_id,))
    destination = args.report
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
