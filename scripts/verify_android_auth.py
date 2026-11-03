"""Opt-in native login/isolation verification with real HTTP/SQL and exact-ID cleanup."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation import store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--credentials", type=Path, default=ROOT / ".cache/auth-demo-credentials.json")
    args = parser.parse_args()
    local_environment()
    accounts = json.loads(args.credentials.read_text(encoding="utf-8"))
    if len(accounts) != 2 or len({a["email"] for a in accounts}) != 2:
        raise ValueError("Exactly two distinct test accounts required")
    adb = Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe"
    base = [str(adb), "-s", args.serial]
    fixtures = []
    report_dir = ROOT / "reports/mobile/auth-v7"
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        with connect() as connection:
            for number, account in enumerate(accounts, 1):
                user = connection.execute("SELECT id FROM series76.users WHERE email=%s AND active", (account["email"],)).fetchone()
                if user is None:
                    raise ValueError("Active test account missing; run seed-demo first")
                sid = uuid4()
                store.append_turn(connection, sid, f"Verification account {number}",
                    SimpleNamespace(answer=f"Saved verification answer {number}", products=[], tool_calls=[], context={}), new=True, owner_id=user["id"])
                fixtures.append(sid)
        for path in ("mobile/android/app/build/outputs/apk/debug/app-debug.apk",
                     "mobile/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"):
            subprocess.run(base + ["install", "-r", "-t", str(ROOT / path)], check=True, capture_output=True)
        subprocess.run(base + ["shell", "am", "force-stop", "com.serie76.assistant.debug"], check=True, capture_output=True)
        subprocess.run(base + ["shell", "run-as com.serie76.assistant.debug sh -c 'mkdir -p files && cat > files/auth-verification.json'"],
                       input=json.dumps(accounts).encode(), check=True, capture_output=True)
        result = subprocess.run(base + ["shell", "am", "instrument", "-w", "-e", "class",
            "com.serie76.assistant.LiveAuthTest", "com.serie76.assistant.debug.test/androidx.test.runner.AndroidJUnitRunner"],
            capture_output=True, timeout=180)
        output = (result.stdout + result.stderr).decode(errors="replace")
        for account in accounts:
            output = output.replace(account["password"], "[REDACTED]")
        (report_dir / "android-live.txt").write_bytes(("\n".join(l.rstrip() for l in output.splitlines()).strip() + "\n").encode())
        if result.returncode or "OK (1 test)" not in output:
            raise AssertionError("Native verification failed; inspect the sanitized report")
        print("Native verification passed: two accounts, owned history, reopening and sign out; zero model calls.")
    finally:
        subprocess.run(base + ["shell", "run-as", "com.serie76.assistant.debug", "rm", "-f", "files/auth-verification.json"], capture_output=True)
        with connect() as connection:
            for sid in fixtures:
                connection.execute("DELETE FROM series76.messages WHERE session_id=%s", (sid,))
                connection.execute("DELETE FROM series76.conversations WHERE id=%s", (sid,))


if __name__ == "__main__":
    main()
