"""Scoped SQL extrema and executable contextual replies; no provider inference."""
import re
from copy import deepcopy

from test_agent_scenarios import Base
from test_conversation_quality import QUERIES
from backend.catalog.models import SearchFilters
from backend.catalog.repository import closest_numeric
from backend.conversation.agent import AgentResult
from backend.conversation.quality import replies, render_impossible


class QualityFollowupTests(Base):
    def manual(self, number):
        if number in (5, 6, 7, 8):
            self.turn("I need at least 70 Nm", ("search_actuators", {"min_torque_nm": 70}))
        call = {
            4: ("search_actuators", {"supply_voltage_v": 110, "min_torque_in_lb": {"value": 100000, "op": "gte"}}),
            5: ("ask_clarification", {"field": "decline"}),
            6: ("ask_clarification", {"field": "cancel"}),
            7: ("ask_clarification", {"field": "unsupported", "cancel_previous": True}),
            8: ("search_actuators", {"supply_voltage_v": 110, "min_torque_in_lb": {"value": 100000, "op": "gt"}, "cancel_previous": True}),
        }[number]
        return self.turn(QUERIES[number - 1], call)

    def test_unknown_service_reports_both_labelled_sql_maxima(self):
        result = self.manual(4)
        self.assertIn("On/Off torque: 26500 in-lb, held by 765B00-11300000/A", result.answer)
        self.assertIn("Modulating torque: 22550 in-lb, held by 765B00-11300000/A", result.answer)
        self.assertNotIn("Closest published torque:", result.answer)

    def test_known_service_reports_only_its_own_maximum(self):
        for service, value in [("on_off", 26500), ("modulating", 22550)]:
            rows = closest_numeric(self.connection, SearchFilters(service=service, supply_voltage_v=110,
                min_torque_in_lb={"value": 100000, "op": "gte"}))
            self.assertEqual([row["service"] for row in rows], [service])
            self.assertEqual(rows[0]["value"], value)

    def test_frequency_variants_have_separate_extrema_and_known_frequency_is_scoped(self):
        for name in ("max_operating_time_s", "max_fla_a", "max_lra_a"):
            rows = closest_numeric(self.connection, SearchFilters(supply_voltage_v=110, **{name: {"value": 0, "op": "lt"}}))
            self.assertEqual({row["frequency_hz"] for row in rows}, {50, 60})
            text = render_impossible({"supply_voltage_v": 110, name: {"value": 0, "op": "lt"}}, rows)
            self.assertIn("at 50 Hz", text)
            self.assertIn("at 60 Hz", text)
            scoped = closest_numeric(self.connection, SearchFilters(supply_voltage_v=110, frequency_hz=60, **{name: {"value": 0, "op": "lt"}}))
            self.assertEqual({row["frequency_hz"] for row in scoped}, {60})
            self.assertTrue(all(row["models"] for row in scoped))
            text = render_impossible({"supply_voltage_v": 110, "frequency_hz": 60, name: {"value": 0, "op": "lt"}}, scoped)
            self.assertIn("at 60 Hz", text)
            self.assertNotIn("at 50 Hz", text)

    @staticmethod
    def scripted_reply(reply):
        code = re.fullmatch(r"Show ([A-Z0-9]{6}-[A-Z0-9]{8}/A)", reply)
        if code:
            return "get_actuator", {"part_numbers": [code[1]], "focus": "overview"}
        if reply.startswith("Find actuators with "):
            voltage = re.search(r"(\d+) V", reply)
            torque = re.search(r"torque >= (\d+) in-lb", reply)
            if not voltage or not torque:
                raise AssertionError("Unexpected numeric suggestion: " + reply)
            return "search_actuators", {"supply_voltage_v": int(voltage[1]),
                "service": "on_off" if "On/Off service" in reply else "modulating",
                "min_torque_in_lb": {"value": int(torque[1]), "op": "gte"}}
        return {
            "Find an actuator for my requirements": ("ask_clarification", {"field": "requirements"}),
            "Explain Base Part Number": ("explain_terms", {"term_keys": ["base_part_number"]}),
            "Explain FLA": ("explain_terms", {"term_keys": ["fla"]}),
        }[reply]

    def test_all_suggestions_for_manual_turns_4_to_8_are_contextual_and_executable(self):
        for number in range(4, 9):
            with self.subTest(turn=number):
                self.history, self.context = [], {}
                result = self.manual(number)
                self.assertEqual(len(result.suggested_replies), 3 if number in (4, 8) else 0)
                self.assertEqual(len(set(result.suggested_replies)), 3 if number in (4, 8) else 0)
                for forbidden in ("Show more", "Cancel", "Explain On/Off service"):
                    self.assertNotIn(forbidden, result.suggested_replies)
                context, history = deepcopy(self.context), deepcopy(self.history)
                for reply in result.suggested_replies:
                    self.context, self.history = deepcopy(context), deepcopy(history)
                    follow = self.turn(reply, self.scripted_reply(reply))
                    self.assertTrue(follow.answer.strip())
                    self.assertFalse(any(str(v).startswith("schema:") for v in follow.tool_calls[0]["validation"]))
                    self.assertNotIn("I could not apply", follow.answer)
                    if reply.startswith(("Show ", "Find actuators with ")):
                        self.assertTrue(follow.products, reply)

    def test_decline_names_only_the_actually_pending_field(self):
        service = self.manual(5)
        self.assertIn("narrow them by service", service.answer)
        self.assertEqual(len(service.products), 3)
        self.context = {"pending_clarification": "frequency"}
        frequency = self.turn("no", ("ask_clarification", {"field": "decline"}))
        self.assertNotIn("service", frequency.answer)
        self.assertIn("frequency", frequency.answer)

    def test_pagination_and_pending_state_gate_control_suggestions(self):
        result = AgentResult("Answer", context={"filters": {"service": "on_off"}, "pagination": {"has_more": False}})
        self.assertNotIn("Show more", replies(result))
        self.assertNotIn("Cancel", replies(result))
        result.context["pagination"]["has_more"] = True
        self.assertEqual(replies(result), [])
        pending = AgentResult("Service?", context={"pending_clarification": "service"}, clarification={"field": "service"})
        self.assertEqual(replies(pending), [])
        cancelled = AgentResult("Cancelled the previous request. Frequency?", context={"pending_clarification": "frequency"}, clarification={"field": "frequency"})
        self.assertNotIn("Cancel", replies(cancelled))
