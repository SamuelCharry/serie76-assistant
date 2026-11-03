"""Real SQL authentication/isolation. Only model interpretation is scripted; no paid calls."""

import os
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.auth.security import password_hash, verify_password, token_hash
from backend.auth.cli import create_user
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation import store
from backend.conversation.agent import AgentResult


class PasswordTests(unittest.TestCase):
    def test_hashes_are_salted_and_wrong_password_is_rejected(self):
        password = "Synthetic test password 76!"
        first, second = password_hash(password), password_hash(password)
        self.assertNotEqual(first, second)
        self.assertNotIn(password, first)
        self.assertTrue(verify_password(password, first))
        self.assertFalse(verify_password("incorrect", first))
        self.assertFalse(verify_password(password, "malformed"))

    def test_all_private_routes_reject_anonymous_requests(self):
        client = TestClient(app)
        for method, url, body in [("GET", "/api/sessions", None), ("GET", f"/api/sessions/{uuid4()}/messages", None),
            ("POST", "/api/conversation", {"query": "test"}), ("GET", f"/api/messages/{uuid4()}/debug", None),
            ("GET", "/api/auth/me", None), ("POST", "/api/auth/logout", None), ("GET", "/api/actuators/761A00", None),
            ("POST", "/api/actuators/search", {})]:
            response = client.request(method, url, json=body)
            self.assertEqual(response.status_code, 401, url)
            self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_validation_errors_do_not_echo_passwords(self):
        marker = "private synthetic value"
        response = TestClient(app).post("/api/auth/login", json={"password": marker})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(marker, response.text)


@unittest.skipUnless(os.environ.get("SERIES76_TEST_DB") == "1", "Real database checks disabled")
class AuthIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local_environment()

    def setUp(self):
        self.connection = connect()
        self.transaction = self.connection.transaction(force_rollback=True)
        self.transaction.__enter__()
        self.password = "Synthetic test password 76!"
        self.email_a, self.email_b = f"{uuid4()}@example.test", f"{uuid4()}@example.test"
        self.a = create_user(self.connection, self.email_a, "Test A", self.password)
        self.b = create_user(self.connection, self.email_b, "Test B", self.password)

        @contextmanager
        def fixture():
            yield self.connection
        self.patches = [patch("backend.auth.api.connect", fixture), patch("backend.conversation.api.connect", fixture),
                        patch.dict(os.environ, {"DEV_DEBUG": "true"})]
        for p in self.patches: p.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        for p in reversed(self.patches): p.stop()
        self.transaction.__exit__(None, None, None)
        self.connection.close()

    def login(self, email):
        response = self.client.post("/api/auth/login", json={"email": email, "password": self.password})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        return response.json()["access_token"]

    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_login_me_expiry_logout_and_stored_token_digest(self):
        token = self.login(self.email_a.upper())
        headers = self.headers(token)
        me = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me.json()["id"], str(self.a))
        self.assertNotIn("password_hash", me.text)
        row = self.connection.execute("SELECT token_hash FROM series76.auth_sessions WHERE user_id=%s", (self.a,)).fetchone()
        self.assertEqual(row["token_hash"], token_hash(token))
        self.assertNotEqual(row["token_hash"], token)
        self.assertEqual(self.client.post("/api/auth/logout", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)
        token = self.login(self.email_a)
        self.connection.execute("UPDATE series76.auth_sessions SET expires_at=now()-interval '1 second' WHERE token_hash=%s", (token_hash(token),))
        self.assertEqual(self.client.get("/api/auth/me", headers=self.headers(token)).status_code, 401)

    def test_wrong_unknown_and_inactive_accounts_have_same_failure(self):
        failures = []
        for email in [self.email_a, f"{uuid4()}@example.test"]:
            r = self.client.post("/api/auth/login", json={"email": email, "password": "incorrect"})
            failures.append((r.status_code, r.json()))
        self.connection.execute("UPDATE series76.users SET active=false WHERE id=%s", (self.a,))
        r = self.client.post("/api/auth/login", json={"email": self.email_a, "password": self.password})
        self.assertEqual(failures[0], failures[1])
        self.assertEqual(failures[0], (r.status_code, r.json()))

    def test_throttle_is_persistent_and_bounds_password_work(self):
        for _ in range(10):
            self.assertEqual(self.client.post("/api/auth/login", json={"email": self.email_a, "password": "bad"}).status_code, 401)
        with patch("backend.auth.api.verify_password") as verify:
            r = self.client.post("/api/auth/login", json={"email": self.email_a, "password": self.password})
            self.assertEqual(r.status_code, 429)
            verify.assert_not_called()

    def test_blocked_ip_cannot_create_unbounded_email_limit_rows(self):
        self.connection.execute("INSERT INTO series76.auth_login_limits(scope_hash,attempts) VALUES (%s,30) ON CONFLICT(scope_hash) DO UPDATE SET attempts=30,window_start=clock_timestamp()", (token_hash("ip:testclient"),))
        for _ in range(3):
            email = f"{uuid4()}@example.test"
            response = self.client.post("/api/auth/login", json={"email": email, "password": "bad"})
            self.assertEqual(response.status_code, 429)
            self.assertIsNone(self.connection.execute("SELECT 1 FROM series76.auth_login_limits WHERE scope_hash=%s", (token_hash("email:" + email),)).fetchone())

    def test_two_users_cannot_list_read_continue_or_debug_each_other(self):
        a, b = self.headers(self.login(self.email_a)), self.headers(self.login(self.email_b))
        result = AgentResult(answer="Controlled interpretation", products=[], tool_calls=[{"name": "fixture"}], context={"part_numbers": ["private-context"]})
        with patch("backend.conversation.api.run_agent", return_value=result) as agent:
            created = self.client.post("/api/conversation", json={"query": "A private question"}, headers=a).json()
            sid, mid = created["session_id"], created["message_id"]
            self.assertEqual(agent.call_count, 1)
            self.assertEqual(self.client.get("/api/sessions", headers=b).json()["sessions"], [])
            self.assertEqual(self.client.get(f"/api/sessions/{sid}/messages", headers=b).status_code, 404)
            self.assertEqual(self.client.get(f"/api/messages/{mid}/debug", headers=b).status_code, 404)
            self.assertEqual(self.client.post("/api/conversation", json={"query": "Steal context", "session_id": sid}, headers=b).status_code, 404)
            self.assertEqual(agent.call_count, 1)
            self.assertEqual(self.client.get(f"/api/sessions/{sid}/messages", headers=a).status_code, 200)
            self.assertEqual(self.client.get(f"/api/messages/{mid}/debug", headers=a).status_code, 200)
            self.assertEqual(self.client.post("/api/conversation", json={"query": "Continue", "session_id": sid}, headers=a).status_code, 200)
            self.assertEqual(len(agent.call_args.args[2]), 2)
            self.assertEqual(agent.call_args.args[3], result.context)
            self.assertEqual(store.history(self.connection, sid, owner_id=self.b), [])
            self.assertEqual(store.recent_context(self.connection, sid, owner_id=self.b), {})

    def test_legacy_history_is_preserved_and_not_auto_claimed(self):
        sid = uuid4()
        self.connection.execute("INSERT INTO series76.conversations(id,title) VALUES (%s,'Legacy')", (sid,))
        token = self.headers(self.login(self.email_a))
        self.assertEqual(self.client.get("/api/sessions", headers=token).json()["sessions"], [])
        self.assertEqual(self.client.get(f"/api/sessions/{sid}/messages", headers=token).status_code, 404)
        self.assertIsNone(self.connection.execute("SELECT owner_id FROM series76.conversations WHERE id=%s", (sid,)).fetchone()["owner_id"])


if __name__ == "__main__":
    unittest.main()
