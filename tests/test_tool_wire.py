"""Compact provider decisions still execute the full canonical T6 policy and SQL."""
from collections import deque
from unittest.mock import patch

from test_agent_scenarios import Base, Scripted
from test_conversation_quality import QUERIES
from backend.conversation import agent, tool_wire


class CompactToolExecutionTests(Base):
    def setUp(self):
        super().setUp()
        # Scripted decisions must not spend another test's process-local quota;
        # keep the real guard function active with an isolated reservation deque.
        guard = patch("backend.conversation.agent._call_times", deque())
        guard.start()
        self.addCleanup(guard.stop)

    def test_flat_bound_decision_preserves_strictness_products_and_trace(self):
        result = self.turn(QUERIES[1], ("search_actuators", {
            "enclosure": "explosionproof", "supply_voltage_v": 24, "supply_current": "DC", "service": "modulating",
            "bounds": [{"field": "min_torque_in_lb", "op": "gt", "value": 1000}]}))
        self.assertEqual([p["base_part_number"] for p in result.products], ["762X30-11370000/A", "762Y30-11370000/A", "763X30-11370000/A"])
        trace = result.tool_calls[0]
        self.assertEqual(trace["parameters"]["min_torque_in_lb"], {"op": "gt", "value": "1000"})
        self.assertEqual(trace["raw_parameters"]["bounds"][0]["op"], "gt")
        self.assertIn("> 1000 in-lb", result.answer)
        self.assertEqual(len(result.suggested_replies), 3)

    def test_plain_focus_wire_matches_legacy_canonical_focus(self):
        call = ("get_actuator", {"part_numbers": ["761A00-11300000/A"],
            "focus": [{"field": "torque", "service": "on_off"}, {"field": "operating_time", "frequency_hz": 60}]})
        answer = self.turn(QUERIES[0], call)
        self.assertIn("On/Off torque: 700 in-lb / 80 Nm", answer.answer)
        self.assertIn("at 60 Hz: 17 s", answer.answer)
        self.assertNotIn("50 Hz", answer.answer)
        self.assertNotIn("Modulating torque", answer.answer)

    def test_duplicate_unknown_and_malformed_bounds_do_not_execute_catalogue_search(self):
        for args in [
            {"bounds": [{"field": "min_torque_nm", "op": "gte", "value": 70}]*2},
            {"bounds": [{"field": "untrusted_sql", "op": "gt", "value": 70}]},
            {"bounds": "not-a-list"},
            {"min_torque_nm": 70, "bounds": [{"field": "min_torque_nm", "op": "gt", "value": 80}]},
            {"bounds": [{"field": "min_torque_nm", "op": "unsafe", "value": 70}]},
            {"bounds": [{"field": "min_torque_nm", "op": "gte", "value": -1}]},
        ]:
            with self.subTest(args=args), patch("backend.conversation.agent.search_actuators", side_effect=AssertionError("invalid bounds executed")):
                result = self.turn("at least 70 Nm", ("search_actuators", args))
            self.assertEqual(result.clarification["field"], "requirements")
            self.assertTrue(all(v.startswith("schema:") for v in result.tool_calls[0]["validation"]))

    def test_wire_and_canonical_inputs_share_one_tool_decision_and_policy_path(self):
        compact = {"service": "on_off", "supply_voltage_v": 110,
                   "bounds": [{"field": "min_torque_nm", "value": 80, "op": "gt"}]}
        canonical = tool_wire.canonical_arguments("search_actuators", compact)
        self.assertNotIn("bounds", canonical)
        self.assertEqual(compact["bounds"][0]["value"], 80)  # caller-owned input remains intact
        calls = []
        class Once(Scripted):
            def invoke(self, *args, **kwargs):
                calls.append(1)
                return super().invoke(*args, **kwargs)
        first = agent.run_agent(self.connection, "On/Off 110 V over 80 Nm", [], {}, model=Once(("search_actuators", compact)))
        second = agent.run_agent(self.connection, "On/Off 110 V over 80 Nm", [], {}, model=Scripted(("search_actuators", canonical)))
        self.assertEqual(len(calls), 1)
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.context, second.context)
