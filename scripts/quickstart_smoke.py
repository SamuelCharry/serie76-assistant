"""Exercise the README keyless HTTP flow; stdlib only, never loads .env.

Run against the disposable serie76-ci project. Restart is intentional; cleanup
belongs to the caller so a failing check cannot hide its exit status.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CODE = "761A00-11300000/A"
QUERY = f"What is the motor power of {CODE}?"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def request(base, path, token=None, payload=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(base + path, headers=headers,
                  data=None if payload is None else json.dumps(payload).encode())
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as exc:
        response = exc
    with response:
        status = response.code
        body = json.load(response)
    require(status == expected, f"{path}: expected HTTP {expected}, got {status}: {body}")
    return body


def wait_ready(base, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request(base, "/ready")
            print("PASS readiness HTTP 200", flush=True)
            return
        except (URLError, TimeoutError, OSError, AssertionError):
            time.sleep(2)
    raise RuntimeError("/ready did not return HTTP 200 before deadline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--compose-env-file", default=".env.example")
    parser.add_argument("--wait-only", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    wait_ready(base)
    if args.wait_only:
        return
    require(os.environ.get("COMPOSE_PROJECT_NAME") == "serie76-ci",
            "Set COMPOSE_PROJECT_NAME=serie76-ci; restart is restricted to this disposable project")
    tokens = []
    for email, password in [("demo@series76.test", "Series76-Demo-1"),
                            ("reviewer@series76.test", "Series76-Demo-2")]:
        login = request(base, "/api/auth/login", payload={"email": email, "password": password})
        require(login["user"]["email"] == email, "Login returned the wrong user")
        tokens.append(login["access_token"])
    print("PASS both README demo logins", flush=True)
    with (ROOT / "data/extracted/series76/catalog.csv").open(encoding="utf-8-sig", newline="") as stream:
        row = next(row for row in csv.DictReader(stream) if row["base_part_number"] == CODE)
    expected = float(row["motor_power_w"])

    def check_power(reply):
        require(any(p["base_part_number"] == CODE for p in reply["products"]), "Missing canonical product")
        values = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*W\b", reply["answer"])
        require(values and all(float(value) == expected for value in values),
                "Answer motor power differs from catalogue CSV")

    first = request(base, "/api/conversation", tokens[0], {"query": QUERY})
    check_power(first)
    session = first["session_id"]
    print("PASS README keyless motor power matches catalogue CSV", flush=True)
    foreign = request(base, "/api/sessions", tokens[1])
    require(session not in [s["id"] for s in foreign["sessions"]], "Foreign session leaked in list")
    request(base, f"/api/sessions/{session}/messages", tokens[1], expected=404)
    request(base, "/api/conversation", tokens[1], {"query": QUERY, "session_id": session}, expected=404)
    print("PASS user 2 cannot list, read or resume user 1 session", flush=True)
    unknown = request(base, "/api/conversation", tokens[0], {"query": "What is the motor power of 999Z99-99999999/A?"})
    require("not found" in unknown["answer"].lower() and not unknown["products"], "Unknown code was not rejected")
    print("PASS unknown code not found without substitute products", flush=True)
    for written in ("761a00-11300000/a", "761a00-11300000"):
        resolved = request(base, "/api/conversation", tokens[0], {"query": f"What is the motor power of {written}?"})
        check_power(resolved)
        require("Interpreted" in resolved["answer"] and written in resolved["answer"]
                and CODE in resolved["answer"], "Code resolution assumption not shown")
    print("PASS lowercase and partial code resolution with visible assumptions", flush=True)
    error = request(base, "/api/conversation", tokens[0],
                    {"query": "I need an actuator for an outdoor valve"}, expected=503)
    require(error == {"detail": "The assistant is not configured yet. Please contact the service administrator.",
                      "error_code": "not_configured"}, "Documented keyless error JSON changed")
    print("PASS free-language HTTP 503 documented error JSON", flush=True)
    sessions = request(base, "/api/sessions", tokens[0])["sessions"]
    require(session in [s["id"] for s in sessions], "Owner session missing")
    for item in sessions:
        history = request(base, f"/api/sessions/{item['id']}/messages", tokens[0])
        require(history["messages"], "Listed session has no messages")
    before = request(base, f"/api/sessions/{session}/messages", tokens[0])["messages"]
    require([m["role"] for m in before] == ["user", "assistant"], "Initial turn not persisted")
    require(before[1]["content"] == first["answer"], "Persisted answer changed")
    print("PASS session lists and persisted messages", flush=True)
    subprocess.run(["docker", "compose", "--env-file", args.compose_env_file,
                    "-p", "serie76-ci", "restart", "backend"], cwd=ROOT, check=True, timeout=90)
    wait_ready(base)
    after_restart = request(base, f"/api/sessions/{session}/messages", tokens[0])["messages"]
    require(after_restart == before, "History changed across backend restart")
    resumed = request(base, "/api/conversation", tokens[0], {"query": QUERY, "session_id": session})
    require(resumed["session_id"] == session, "Resume created another session")
    check_power(resumed)
    after = request(base, f"/api/sessions/{session}/messages", tokens[0])["messages"]
    require(len(after) == 4 and after[:2] == before, "Resumed history lost or duplicated messages")
    request(base, f"/api/sessions/{session}/messages", tokens[1], expected=404)
    print("PASS backend restart, token persistence, session resume and isolation", flush=True)


if __name__ == "__main__":
    main()
