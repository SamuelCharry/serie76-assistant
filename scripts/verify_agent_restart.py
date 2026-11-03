"""End-to-end check on the REAL Docker backend with a real LLM (experimental Google endpoint).

HTTP -> container -> LangChain -> tool -> SQL -> answer, then `docker compose restart db backend`,
then resume the same session and ask a follow-up that depends on the persisted context.

- A dedicated acceptance user is created once; its random password is kept only in the
  ignored .cache/agent-acceptance-user.json and never printed.
- The Google key is passed to Compose through the process environment only; afterwards the
  backend is recreated with the normal .env so the key does not remain in the container.
- Calls happen inside the container, so the ledger reserves their worst case BEFORE running.
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.agent_acceptance import Ledger, google_key, append  # noqa: E402
import scripts.agent_acceptance as acceptance  # noqa: E402

API = "http://127.0.0.1:8000"
CREDENTIALS = ROOT / ".cache/agent-acceptance-user.json"
OUT = ROOT / "reports/agent_acceptance/e2e"
TURNS_BEFORE = ["Show me 761A00-11300000/A", "and how much power does it draw?"]
TURN_AFTER = "and its locked rotor current?"


def request(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} | ({"Authorization": f"Bearer {token}"} if token else {})
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def converse(body, token, ledger, report):
    """POST a turn; retry ONLY provider 503s (infrastructure check, not a quality score). Each try is reserved."""
    for attempt in range(1, 4):
        ledger.reserve(32_000, dict(stage="e2e_container_call", query=body["query"], attempt=attempt))
        status, answer = request("POST", "/api/conversation", body, token)
        report["attempts"].append(dict(query=body["query"], attempt=attempt, status=status, error_code=answer.get("error_code")))
        if not (status == 503 and answer.get("error_code") in ("provider_error", "rate_limited", "timeout", "provider_unreachable")):
            return status, answer
        time.sleep(5)
    return status, answer


def wait_ready(timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if request("GET", "/ready")[0] == 200:
                return True
        except OSError:
            pass
        time.sleep(2)
    return False


def compose(*args, env=None):
    subprocess.run(["docker", "compose", *args], cwd=ROOT, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_user():
    from backend.auth.cli import create_user
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    if CREDENTIALS.exists():
        return json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    local_environment()
    account = dict(email="agent.acceptance@example.test", password=secrets.token_urlsafe(24))
    with connect() as connection:
        create_user(connection, account["email"], "Agent acceptance", account["password"])
    CREDENTIALS.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS.write_text(json.dumps(account), encoding="utf-8")
    return account


def main():
    config = json.loads((ROOT / "config/agent_acceptance.json").read_text(encoding="utf-8"))
    acceptance.OUT = OUT
    ledger = Ledger(config)
    account = ensure_user()  # calls run inside the container: converse() reserves each attempt's worst case first
    env = dict(os.environ, OPENROUTER_API_KEY=google_key(), OPENROUTER_BASE_URL=config["base_url"],
               OPENROUTER_CHAT_MODEL=config["model"], AGENT_REASONING_EFFORT=config["reasoning_effort"],
               AGENT_MAX_TOKENS=str(config["max_tokens"]), DEV_DEBUG="true")
    report = dict(steps=[], attempts=[])
    try:
        compose("up", "-d", "--build", "--force-recreate", "backend", env=env)
        assert wait_ready(), "backend not ready"
        status, login = request("POST", "/api/auth/login", dict(email=account["email"], password=account["password"]))
        assert status == 200, f"login {status}"
        token = login["access_token"]
        session = None
        for query in TURNS_BEFORE:
            status, body = converse(dict(query=query) | ({"session_id": session} if session else {}), token, ledger, report)
            report["steps"].append(dict(query=query, status=status, answer=body.get("answer"), error_code=body.get("error_code")))
            assert status == 200, f"{query}: {status} {body.get('error_code')}"
            session = body["session_id"]
        compose("restart", "db", "backend", env=env)
        assert wait_ready(), "not ready after restart"
        status, login = request("POST", "/api/auth/login", dict(email=account["email"], password=account["password"]))
        token = login["access_token"]
        status, history = request("GET", f"/api/sessions/{session}/messages", token=token)
        report["history_after_restart"] = dict(status=status, messages=len(history.get("messages", [])))
        status, body = converse(dict(session_id=session, query=TURN_AFTER), token, ledger, report)
        report["steps"].append(dict(query=TURN_AFTER, status=status, answer=body.get("answer"), error_code=body.get("error_code"), after_restart=True))
        status, debug = request("GET", f"/api/messages/{body.get('message_id')}/debug", token=token)
        trace = (debug.get("tool_calls") or [{}])[0]
        report["after_restart_trace"] = {k: trace.get(k) for k in ("name", "parameters", "validation", "context_before", "model")}
        checks = dict(
            power_answer="Motor power: 15 W" in (report["steps"][1]["answer"] or ""),
            history_restored=report["history_after_restart"]["messages"] == 4,
            follow_up_after_restart="LRA at 60 Hz: 1.4 A" in (body.get("answer") or ""),
            context_reached_model_after_restart="761A00-11300000/A" in json.dumps(trace.get("context_before")),
        )
        report["checks"] = checks
        report["status"] = "passed" if all(checks.values()) else "failed"
    finally:
        # Recreate the backend with the normal .env so the experimental key is not left in it.
        compose("up", "-d", "--force-recreate", "backend")
    report["session_id"] = session
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "restart_check.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(dict(status=report["status"], checks=report["checks"])))


if __name__ == "__main__":
    main()
