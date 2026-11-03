"""No paid calls: local HTTP transport, process guard and rollback-only demo provisioning."""
import json
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from backend.auth.cli import ensure_demo_users
from backend.auth.security import verify_password
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation import agent


class ReadinessUnitTests(unittest.TestCase):
    def test_provider_flag_serialized_on_wire_with_local_http_only(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                body = json.dumps({"id": "fixture", "object": "chat.completion", "created": 1, "model": "fixture",
                    "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "fixture"}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for host, flag, expected in [("openrouter.ai", "true", True), ("openrouter.ai", "false", False),
                                         ("generativelanguage.googleapis.com", "true", None)]:
                with self.subTest(host=host, flag=flag), patch.dict(os.environ, {
                    "OPENROUTER_API_KEY": "synthetic-local-only", "OPENROUTER_CHAT_MODEL": "fixture",
                    "OPENROUTER_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
                    "OPENROUTER_REQUIRE_PARAMETERS": flag}), patch.object(agent, "urlsplit", return_value=SimpleNamespace(hostname=host)):
                    agent.create_model_client().invoke("local test")
                if expected is None:
                    self.assertNotIn("provider", received[-1])
                else:
                    self.assertEqual(received[-1]["provider"], {"require_parameters": expected})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_guard_boundary_expiry_and_concurrent_reservations(self):
        from collections import deque
        with patch.object(agent, "_call_times", deque()), patch.dict(os.environ, {"AGENT_MAX_CALLS_PER_HOUR": "2"}):
            with patch.object(agent.time, "monotonic", return_value=100):
                agent.reserve_agent_call()
                agent.reserve_agent_call()
                with self.assertRaises(agent.AgentUnavailable) as error:
                    agent.reserve_agent_call()
                self.assertEqual(error.exception.code, "rate_limited_local")
            with patch.object(agent.time, "monotonic", return_value=3700):
                agent.reserve_agent_call()
                self.assertEqual(len(agent._call_times), 1)
        with patch.object(agent, "_call_times", deque()), patch.dict(os.environ, {"AGENT_MAX_CALLS_PER_HOUR": "2"}):
            def attempt(_):
                try:
                    agent.reserve_agent_call()
                    return True
                except agent.AgentUnavailable:
                    return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(attempt, range(8))), 2)

    def test_invalid_demo_override_is_sanitized(self):
        with patch.dict(os.environ, {"DEMO_USERS_JSON": "private-marker"}):
            with self.assertRaises(ValueError) as error:
                ensure_demo_users(None)
            self.assertNotIn("private-marker", str(error.exception))


@unittest.skipUnless(os.environ.get("SERIES76_TEST_DB") == "1", "Real database checks disabled")
class DemoIntegrationTests(unittest.TestCase):
    def test_demo_users_are_hashed_idempotent_and_passwords_preserved(self):
        local_environment()
        with connect() as connection, connection.transaction(force_rollback=True):
            accounts = [{"email": f"{uuid4()}@series76.test", "name": "Test only", "password": "Series76-Demo-1"},
                        {"email": f"{uuid4()}@series76.test", "name": "Test reviewer", "password": "Series76-Demo-2"}]
            with patch.dict(os.environ, {"DEMO_USERS_JSON": json.dumps(accounts)}):
                self.assertEqual(ensure_demo_users(connection), 2)
                self.assertEqual(ensure_demo_users(connection), 0)
            for account in accounts:
                row = connection.execute("SELECT password_hash FROM series76.users WHERE email=%s", (account["email"],)).fetchone()
                self.assertTrue(verify_password(account["password"], row["password_hash"]))
            original = row["password_hash"]
            accounts[-1]["password"] = "A different password 76!"
            with patch.dict(os.environ, {"DEMO_USERS_JSON": json.dumps(accounts)}):
                self.assertEqual(ensure_demo_users(connection), 0)
            self.assertEqual(connection.execute("SELECT password_hash FROM series76.users WHERE email=%s", (accounts[-1]["email"],)).fetchone()["password_hash"], original)
            with patch.dict(os.environ, {"DEMO_USERS_JSON": "[]"}):
                self.assertEqual(ensure_demo_users(connection), 0)
