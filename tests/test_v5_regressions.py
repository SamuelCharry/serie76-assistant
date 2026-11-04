"""Recorded v5 interpretations replayed against code/SQL, never a live provider."""
from collections import deque
from unittest.mock import patch

from test_agent_scenarios import Base


class V5RegressionTests(Base):
    def setUp(self):
        super().setUp()
        guard = patch("backend.conversation.agent._call_times", deque())
        guard.start()
        self.addCleanup(guard.stop)

    def test_dc_requested_ac_frequency_keeps_published_unqualified_current(self):
        for focus in ("fla", "lra", "operating_time"):
            result = self.turn("What is the full load current and operating time of 761X30-11370000/A at 60 Hz?",
                               ("get_actuator", {"part_numbers": ["761X30-11370000/A"], "focus": [focus], "focus_frequency_hz": 60}))
            self.assertIn("(DC: no mains frequency)", result.answer)
            self.assertNotIn("at 60 Hz:", result.answer)
            self.assertTrue(result.products[0]["measurements"])
            if focus == "fla":
                self.assertIn("FLA (DC: no mains frequency): 5 A", result.answer)

    def test_singular_after_comparison_clarifies_even_if_model_resends_both_codes(self):
        codes = ["761A00-11300000/A", "761B00-11300000/A"]
        self.turn("Compare " + " and ".join(codes), ("get_actuator", {"part_numbers": codes}))
        with patch("backend.conversation.agent.get_actuator", side_effect=AssertionError("ambiguous lookup queried")):
            result = self.turn("what is its LRA?", ("get_actuator", {"part_numbers": codes, "focus": ["lra"]}))
        self.assertEqual(result.clarification["field"], "which_product")
        self.assertFalse(result.products)
        self.assertIn("ambiguous_singular_reference", result.tool_calls[0]["overrides"])

    def test_new_ranked_request_does_not_inherit_pending_torque_when_refine_false(self):
        self.turn("I need at least 70 Nm", ("search_actuators", {"bounds": [{"field": "min_torque_nm", "value": 70, "op": "gte"}]}))
        result = self.turn("Busco un actuador para exteriores que sea muy rápido y no consuma mucha energía.",
                           ("search_actuators", {"enclosure": "weatherproof", "sort_by": ["fastest", "lowest_power"], "refine": False}))
        self.assertNotIn("min_torque_nm", result.context["filters"])
        self.assertEqual(result.clarification["field"], "supply_voltage_v")
        self.assertEqual(result.products, [])
        self.assertIn("Ranked by fastest operating time", result.answer)
        self.assertIn("Motor power", result.answer)

    def test_informal_service_with_explicit_torque_keeps_both_requirements(self):
        result = self.turn("I just need it to fully open or fully close a valve, 110 V, at least 50 Nm",
                           ("search_actuators", {"service": "on_off", "supply_voltage_v": 110,
                                                "bounds": [{"field": "min_torque_nm", "value": 50, "op": "gte"}]}))
        self.assertEqual(result.context["filters"]["min_torque_nm"], {"value": "50", "op": "gte"})
        self.assertIn("torque >= 50 Nm", result.answer)
