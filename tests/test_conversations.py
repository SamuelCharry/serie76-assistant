"""Conversation tests: real PostgreSQL and LangChain tools, scripted routing only.

No paid model calls. Test rows live inside a rollback-only transaction.
"""

import os
import unittest
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch
from contextlib import contextmanager

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.contracts import ConversationRequest
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation.agent import AgentUnavailable, run_agent
from backend.conversation import store


class RouterFixture:
    """Only the language interpretation is scripted. Tools still query real SQL."""
    def __init__(self, name, args):
        self.name, self.args, self.seen = name, args, None

    def bind_tools(self, tools, **kwargs):
        self.tools = tools
        return self

    def invoke(self, messages, **kwargs):
        self.seen = messages
        return SimpleNamespace(tool_calls=[{"name": self.name, "args": self.args, "id": "test-call"}])


class RequestTests(unittest.TestCase):
    def test_blank_oversized_and_invalid_session(self):
        for request in ({"query": " "}, {"query": "x" * 4001}, {"query": "a", "session_id": "bad"}):
            with self.assertRaises(ValueError):
                ConversationRequest.model_validate(request)

    def test_debug_disabled_without_database(self):
        with patch.dict(os.environ, {"DEV_DEBUG": "false"}):
            self.assertEqual(TestClient(app).get(f"/api/messages/{uuid4()}/debug").status_code, 404)

    def test_openrouter_compatible_transport_without_external_calls(self):
        from backend.conversation.agent import create_model
        received = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                payload = {"id": "local-test", "object": "chat.completion", "created": 1, "model": "fixture",
                    "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                        "role": "assistant", "content": None, "tool_calls": [{"id": "call-test", "type": "function",
                        "function": {"name": "ask_clarification", "arguments": '{"field":"service"}'}}]}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
                body = json.dumps(payload).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "synthetic-local-test-key", "OPENROUTER_CHAT_MODEL": "fixture",
                  "OPENROUTER_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1"}):
                result = run_agent(None, "Need torque", [], {})
            self.assertIn("On/Off", result.answer)
            self.assertEqual(received[0]["tool_choice"], "required")
            self.assertEqual(len(received), 1)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


@unittest.skipUnless(os.environ.get("SERIES76_TEST_DB") == "1", "Real database checks disabled")
class ConversationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local_environment()

    def setUp(self):
        self.connection = connect()
        self.transaction = self.connection.transaction(force_rollback=True)
        self.transaction.__enter__()

    def tearDown(self):
        self.transaction.__exit__(None, None, None)
        self.connection.close()

    def run_tool(self, name, args, context=None):
        return run_agent(self.connection, "technical query", [], context or {}, model=RouterFixture(name, args))

    def test_exact_lookup_and_focus_use_published_numbers(self):
        result = self.run_tool("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "motor_power"})
        self.assertIn("15 W", result.answer)
        self.assertIn("not a specification of total", result.answer)
        self.assertEqual(result.products[0]["measurements"]["on_off_torque_nm"], 80)
        self.assertEqual(result.tool_calls[0]["name"], "get_actuator")
        self.assertNotIn("evidence", result.products[0])
        self.assertNotIn("provenance", result.products[0])

    def test_unknown_na_and_invalid_codes_are_distinct(self):
        missing = self.run_tool("get_actuator", {"part_numbers": ["999Z99-99999999/A"]})
        self.assertFalse(missing.products)
        na = self.run_tool("get_actuator", {"part_numbers": ["761A00-11330C00/A"]})
        self.assertIn("N/A", na.answer)
        self.assertEqual(na.products[0]["field_status"]["motor_power_w"], "source_NA")
        invalid = self.run_tool("get_actuator", {"part_numbers": ["761A00"]})
        self.assertIn("could not be applied", invalid.answer)
        self.assertFalse(invalid.products)

    def test_search_clarification_no_match_and_valid_constraints(self):
        clarification = self.run_tool("search_actuators", {"min_torque_nm": 100})
        self.assertIn("service", clarification.answer)
        empty = self.run_tool("search_actuators", {"service": "on_off", "min_torque_nm": 1e10}, {"part_numbers": ["old"]})
        self.assertFalse(empty.products)
        self.assertEqual(empty.context["part_numbers"], [])
        found = self.run_tool("search_actuators", {"service": "on_off", "min_torque_nm": 70, "supply_voltage_v": 24})
        self.assertTrue(found.products)
        self.assertEqual(found.tool_calls[0]["parameters"]["min_torque_nm"], "70")

    def test_saved_context_and_snapshots_round_trip(self):
        result = self.run_tool("get_actuator", {"part_numbers": ["761A00-11300000/A"]})
        sid = uuid4()
        response_id = store.append_turn(self.connection, sid, "Look up this actuator", result, new=True)
        restored = store.history(self.connection, sid)
        self.assertEqual(len(restored), 2)
        self.assertEqual(restored[-1]["products"], result.products)
        self.assertEqual(store.recent_context(self.connection, sid), result.context)
        self.assertEqual(store.debug_for_message(self.connection, response_id)["tool_calls"], result.tool_calls)
        fixture = RouterFixture("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "fla"})
        followup = run_agent(self.connection, "and the current?", restored, result.context, model=fixture)
        self.assertIn("1.2 A", followup.answer)
        self.assertIn("761A00-11300000/A", fixture.seen[1].content)

    def test_http_history_debug_and_failed_turn_atomicity(self):
        @contextmanager
        def connection_fixture():
            yield self.connection

        fixture = RouterFixture("get_actuator", {"part_numbers": ["761A00-11300000/A"]})
        def agent(connection, query, history, context):
            return run_agent(connection, query, history, context, model=fixture)

        with patch("backend.conversation.api.connect", connection_fixture), patch("backend.conversation.api.run_agent", side_effect=agent):
            client = TestClient(app)
            response = client.post("/api/conversation", json={"query": "Look up 761A00-11300000/A"})
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertNotIn("tool_calls", payload)
            sid = payload["session_id"]
            history = client.get(f"/api/sessions/{sid}/messages?limit=1").json()
            self.assertTrue(history["has_more"])
            self.assertEqual(len(history["messages"]), 1)
            self.assertNotIn("context", history["messages"][0])
            self.assertNotIn("tool_calls", history["messages"][0])
            earlier = client.get(f"/api/sessions/{sid}/messages?before={history['next_before']}").json()
            self.assertEqual(earlier["messages"][0]["role"], "user")
            with patch.dict(os.environ, {"DEV_DEBUG": "true"}):
                debug = client.get(f"/api/messages/{payload['message_id']}/debug").json()
                self.assertEqual(debug["tool_calls"][0]["name"], "get_actuator")
            with patch("backend.conversation.api.run_agent", side_effect=AgentUnavailable):
                failed = client.post("/api/conversation", json={"query": "failure", "session_id": sid})
                self.assertEqual(failed.status_code, 503)
            self.assertEqual(len(store.history(self.connection, sid)), 2)
            self.assertEqual(client.post("/api/conversation", json={"query": "missing", "session_id": str(uuid4())}).status_code, 404)

    def test_session_lock_serializes_across_connections(self):
        sid = uuid4()
        store.lock_session(self.connection, sid)
        with connect() as other:
            with self.assertRaises(store.BusySession):
                store.lock_session(other, sid)


if __name__ == "__main__":
    unittest.main()
