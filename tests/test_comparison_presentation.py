"""Visible comparison text is human-readable; SQL units stay grouped and unchanged."""
from collections import deque
import unittest
from unittest.mock import patch

from backend.conversation import agent, quality
from scripts.check_public_text import public_text_issues
from test_agent_scenarios import Base, Scripted


class PublicPresentationTests(unittest.TestCase):
    def product(self, code="A"):
        return dict(base_part_number=code, enclosure="weatherproof", supply_voltage_v=110,
                    supply_current="AC", phase_count=1, field_status={}, frequencies=[],
                    measurements={"on_off_torque_in_lb": 700, "on_off_torque_nm": 80})

    def test_identical_dual_units_count_as_one_hidden_field(self):
        a = self.product()
        b = self.product("B")
        comparison = quality.comparison([a, b])
        self.assertEqual(comparison["rows"], [])
        self.assertEqual(len(comparison["hidden_rows"]), 5)  # four dimensions + one torque

    def test_merged_units_and_unambiguous_better_value(self):
        a, b = self.product(), self.product("B")
        b["measurements"] = {"on_off_torque_in_lb": 880, "on_off_torque_nm": 100}
        row, = quality.comparison([a, b])["rows"]
        self.assertEqual(row, dict(field="on_off_torque", label="On/Off torque", values=["700 in-lb / 80 Nm", "880 in-lb / 100 Nm"], better=1))
        # Do not choose a winner if published dual-unit columns disagree in direction.
        b["measurements"]["on_off_torque_nm"] = 70
        self.assertIsNone(quality.comparison([a, b])["rows"][0]["better"])

    def test_na_and_missing_layout_stay_distinct_and_human_readable(self):
        a, b = self.product(), self.product("B")
        a["measurements"] = dict.fromkeys(a["measurements"])
        a["field_status"] = dict.fromkeys(a["measurements"], "source_NA")
        comparison = quality.comparison([a, b])
        self.assertIn("N/A in the source table", comparison["rows"][0]["values"][0])
        self.assertNotIn("source_NA", comparison["rows"][0]["values"][0])
        self.assertEqual(public_text_issues("", comparison), [])

    def test_guard_checks_all_three_visible_surfaces_but_allows_machine_row_ids(self):
        comparison = {"rows": [dict(field="on_off_torque", label="On/Off torque")]}
        self.assertEqual(public_text_issues("Published values", comparison, ["Show an actuator"]), [])
        self.assertEqual(len(public_text_issues("motor_power_w", {"rows": [{"label": "fla_60hz_a"}]}, ["Use on_off"])), 3)
        for old_label in ("on off torque in lb", "operating time 60 Hz s", "fla 60 Hz a"):
            self.assertTrue(public_text_issues("", {"rows": [{"label": old_label}]}), old_label)


class ComparisonSqlTests(Base):
    def setUp(self):
        super().setUp()
        guard = patch("backend.conversation.agent._call_times", deque())
        guard.start()
        self.addCleanup(guard.stop)

    def test_sql_comparison_uses_card_labels_and_merged_units(self):
        result = self.turn("Compare 761A00-11300000/A and 761B00-11300000/A", ("get_actuator", {
            "part_numbers": ["761A00-11300000/A", "761B00-11300000/A"]}))
        self.assertIn("On/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm", result.answer)
        self.assertIn("Operating time at 60 Hz: 17 s vs 19 s", result.answer)
        self.assertIn("FLA at 60 Hz: 1.2 A vs 1.3 A", result.answer)
        self.assertEqual(sum(r["label"] == "On/Off torque" for r in result.comparison["rows"]), 1)
        self.assertTrue(all(r["values"][0] != r["values"][1] for r in result.comparison["rows"]))

    def test_interpretation_rules_are_in_the_single_production_model_request(self):
        class Once(Scripted):
            count = 0
            def invoke(self, *args, **kwargs):
                self.count += 1
                return super().invoke(*args, **kwargs)
        model = Once(("search_actuators", {"service": "on_off", "supply_voltage_v": 110,
                     "bounds": [{"field": "min_torque_nm", "op": "gte", "value": 50}]}))
        result = agent.run_agent(self.connection,
            "I just need it to fully open or fully close a valve, 110 V, at least 50 Nm", [], {}, model=model)
        prompt = model.seen[0].content
        self.assertIn("Extract EVERY explicit numeric requirement", prompt)
        self.assertIn("starts fresh with refine=false", prompt)
        self.assertIn("even if a clarification", prompt)
        self.assertIn("including every numeric limit", agent.DESCRIPTIONS["search_actuators"])
        self.assertIn("New independent requests use refine=false", agent.DESCRIPTIONS["search_actuators"])
        self.assertEqual(model.count, 1)
        self.assertEqual(public_text_issues(result.answer, result.comparison, result.suggested_replies), [])
