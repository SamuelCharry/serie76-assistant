"""Offline scoring is representation-aware, operator-strict and evidence-preserving."""
from copy import deepcopy
from decimal import Decimal
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import agent_acceptance
from scripts.agent_acceptance import argument_matches, rescore_record, score


class AcceptanceScoringTests(unittest.TestCase):
    def test_legacy_minimum_only_accepts_equal_gte_bound_stated_in_case(self):
        for value in (70, "70", "70.00", Decimal("70.000")):
            self.assertTrue(argument_matches("min_torque_nm", {"value": value, "op": "gte"}, 70,
                                             ["at least 70 Nm", "On/off"]))
        for op in ("gt", "lt", "lte"):
            self.assertFalse(argument_matches("min_torque_nm", {"value": "70", "op": op}, 70, ["at least 70 Nm"]))
        for query in ("70 Nm", "at least 80 Nm", "more than 70 Nm"):
            self.assertFalse(argument_matches("min_torque_nm", {"value": "70", "op": "gte"}, 70, [query]))

    def test_explicit_operator_value_and_shape_are_all_required(self):
        want = {"value": 1.5, "op": "lt"}
        self.assertTrue(argument_matches("max_fla_a", {"value": "1.500", "op": "lt"}, want))
        for got in [1.5, {"value": "1.5", "op": "lte"}, {"value": "1.6", "op": "lt"},
                    {"value": True, "op": "lt"}, {"value": "NaN", "op": "lt"},
                    {"value": "Infinity", "op": "lt"}, {"value": "1.5"},
                    {"value": "1.5", "op": "lt", "extra": 1}]:
            self.assertFalse(argument_matches("max_fla_a", got, want), got)
        self.assertTrue(argument_matches("min_torque_nm", 70, {"value": "70", "op": "gte"}))
        self.assertFalse(argument_matches("min_torque_nm", 70, {"value": "70", "op": "gt"}))

    def test_unrelated_dimensions_do_not_gain_bound_unwrapping(self):
        for field in ("service", "supply_voltage_v", "frequency_hz"):
            self.assertFalse(argument_matches(field, {"value": "70", "op": "gte"}, 70, ["at least 70"]))
        self.assertFalse(argument_matches("max_fla_a", {"value": "70", "op": "gte"}, 70, ["at least 70"]))

    def fixture(self):
        case = {"turns": [{"query": "at least 70 Nm", "expect": {"tool": "search_actuators", "args": {"min_torque_nm": 70}}}]}
        turn = dict(query="at least 70 Nm", answer="SQL answer", products=[], terms=[], clarification=None,
                    trace={"name": "search_actuators", "parameters": {"min_torque_nm": {"value": "70", "op": "gte"}}},
                    passed=False, failures=["old scalar mismatch"])
        return case, {"status": "failed", "turns": [turn]}

    def test_rescore_uses_observations_without_mutating_original_verdicts_or_answers(self):
        case, record = self.fixture()
        original = deepcopy(record)
        result = rescore_record(record, case)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(record, original)
        self.assertEqual(result["turns"][0]["answer"], "SQL answer")
        case["turns"][0]["expect"]["contains"] = ["missing text"]
        result = rescore_record(record, case)
        self.assertEqual(result["status"], "failed")
        self.assertIn("missing text: missing text", result["turns"][0]["failures"])

    def test_rescore_preserves_provider_disposition_and_refuses_different_query(self):
        case, record = self.fixture()
        record["status"] = "provider_failure"
        self.assertEqual(rescore_record(record, case)["status"], "provider_failure")
        record["turns"][0]["query"] = "different query"
        with self.assertRaises(ValueError):
            rescore_record(record, case)

    def test_missing_candidate_evidence_retains_only_its_original_verdict(self):
        case, record = self.fixture()
        case["turns"][0]["expect"]["candidates_include"] = ["A"]
        self.assertEqual(rescore_record(record, case)["status"], "passed")
        record["turns"][0]["failures"].append("SQL candidate missing: A")
        self.assertEqual(rescore_record(record, case)["turns"][0]["failures"], ["SQL candidate missing: A"])
        record["turns"][0]["candidates"] = ["A"]
        self.assertEqual(rescore_record(record, case)["status"], "passed")

    def test_comparator_does_not_bypass_other_expectations(self):
        case, record = self.fixture()
        observed = record["turns"][0]
        expected = case["turns"][0]
        expected["expect"].update(tool="get_actuator", clarification=["service"], contains=["required"], product_count=1)
        passed, failures = score(expected, observed)
        self.assertFalse(passed)
        self.assertEqual(len(failures), 4)

    def test_report_recomputes_status_and_preserves_recorded_files_byte_for_byte(self):
        scenario, record = self.fixture()
        scenario.update(id="fixture", category="test")
        record["scenario"] = "fixture"
        with TemporaryDirectory() as directory:
            out = Path(directory)
            results = (json.dumps(record) + "\n").encode()
            (out / "results.jsonl").write_bytes(results)
            (out / "ledger.jsonl").write_bytes(b"")
            with patch.object(agent_acceptance, "OUT", out), redirect_stdout(io.StringIO()):
                agent_acceptance.command_report({"model": "offline", "provider": "fixture", "safety_cap_usd": 1},
                                                {"version": "fixture", "scenarios": [scenario]})
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["passed"], 1)
            self.assertEqual(summary["recorded_counts"]["failed"], 1)
            self.assertEqual((out / "results.jsonl").read_bytes(), results)
            self.assertEqual((out / "ledger.jsonl").read_bytes(), b"")
