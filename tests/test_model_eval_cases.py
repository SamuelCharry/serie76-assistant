"""Sanity-check the evaluation corpus and its real catalogue-tool contracts."""

import json
from pathlib import Path
import unittest

from backend.catalog.models import SearchFilters, validate_part_number
from model_eval.cases import CASES, SMOKE_CASE_IDS


class ModelEvaluationCaseTests(unittest.TestCase):
    def test_alternate_clarifications_preserve_all_stated_constraints(self):
        alternatives = {
            case.id: case.alternative_search_arguments
            for case in CASES
            if case.alternative_search_arguments is not None
        }
        self.assertEqual(
            alternatives,
            {
                "missing_service": {"min_torque_nm": 100},
                "missing_frequency": {
                    "service": "on_off",
                    "supply_voltage_v": 110,
                    "supply_current": "AC",
                    "phase_count": 1,
                    "max_operating_time_s": 20,
                },
            },
        )
        for case in CASES:
            if case.alternative_search_arguments is None:
                continue
            with self.subTest(case=case.id):
                self.assertEqual(case.expected_tool, "ask_clarification")
                parsed = SearchFilters(**case.alternative_search_arguments)
                if case.id == "missing_service":
                    self.assertIsNone(parsed.service)
                else:
                    self.assertIsNone(parsed.frequency_hz)

    def test_smoke_selection_covers_high_risk_categories(self):
        self.assertEqual(len(set(SMOKE_CASE_IDS)), 12)
        selected = [case for case in CASES if case.id in SMOKE_CASE_IDS]
        self.assertEqual(len(selected), 12)
        self.assertTrue(
            {
                "exact_retrieval",
                "service_and_supply",
                "shared_measurements",
                "missing_data",
                "certification_exception",
                "ambiguity",
                "identity_validation",
                "no_matches",
                "multi_turn",
                "adversarial",
            }
            <= {case.category for case in selected}
        )

    def test_required_failure_modes_are_represented(self):
        required = {
            "exact_retrieval",
            "service_and_supply",
            "frequency_scope",
            "shared_measurements",
            "missing_data",
            "certification_exception",
            "ambiguity",
            "identity_validation",
            "no_matches",
            "multi_turn",
            "adversarial",
            "rate_and_duty",
        }
        self.assertTrue(required <= {c.category for c in CASES})
        self.assertEqual(len({c.id for c in CASES}), len(CASES))
        self.assertTrue(12 <= len(CASES) <= 18)

    def test_search_arguments_match_live_tool_contract(self):
        for case in CASES:
            with self.subTest(case=case.id):
                if case.expected_tool == "search_actuators":
                    parsed = SearchFilters(**case.expected_arguments)
                    self.assertIsNotNone(parsed.service)
                elif case.expected_tool == "get_actuator":
                    self.assertEqual(
                        set(case.expected_arguments), {"part_numbers", "focus"}
                    )
                    for code in case.expected_arguments["part_numbers"]:
                        validate_part_number(code)
                else:
                    self.assertIn(
                        case.expected_arguments["field"],
                        ("part_number", "service", "frequency"),
                    )

    def test_arguments_match_agent_schemas_when_available(self):
        try:
            from backend.conversation.agent import (
                LookupInput,
                SearchInput,
                ClarifyInput,
            )
        except ModuleNotFoundError:
            self.skipTest(
                "Conversation dependencies are not installed in this test environment"
            )
        schemas = {
            "get_actuator": LookupInput,
            "search_actuators": SearchInput,
            "ask_clarification": ClarifyInput,
        }
        for case in CASES:
            with self.subTest(case=case.id):
                schemas[case.expected_tool].model_validate(case.expected_arguments)

    def test_prompts_do_not_contain_tool_results_or_expected_fact_payloads(self):
        for case in CASES:
            with self.subTest(case=case.id):
                self.assertEqual(case.messages[-1]["role"], "user")
                self.assertTrue(
                    all(
                        m["role"] in ("user", "assistant") and m["content"].strip()
                        for m in case.messages
                    )
                )
                self.assertFalse(
                    any(
                        "expected_facts" in m["content"]
                        or "measurements." in m["content"]
                        for m in case.messages
                    )
                )

    def test_get_expected_measurements_match_processed_ocr_output(self):
        # Corpus maintenance check, not an evaluation of a model. No manual data.
        path = (
            Path(__file__).resolve().parents[1] / "data/extracted/series76/catalog.json"
        )
        catalogue = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = {r["base_part_number"]: r for r in catalogue["rows"]}
        for case in CASES:
            if case.expected_tool != "get_actuator":
                continue
            code = case.expected_arguments["part_numbers"][0]
            row = rows.get(code)
            with self.subTest(case=case.id):
                if case.expected_facts.get("products") == []:
                    self.assertIsNone(row)
                    self.assertEqual(case.expected_facts["missing"], [code])
                    continue
                self.assertIsNotNone(row)
                for key, expected in case.expected_facts.items():
                    self.assertTrue(key.startswith("products.0."))
                    key = key.removeprefix("products.0.")
                    if key.startswith("measurements."):
                        self.assertEqual(row[key.split(".", 1)[1]], expected)
                    elif key.startswith("field_status."):
                        self.assertEqual(
                            row["field_status"][key.split(".", 1)[1]], expected
                        )
                    elif key == "data_status":
                        self.assertEqual(row[key], expected)
                    elif key == "certification.csa_status":
                        self.assertEqual(row["csa_status"], expected)
                    elif key == "certification.footnote_marker":
                        self.assertEqual(row["source_footnote"], expected)


if __name__ == "__main__":
    unittest.main()
