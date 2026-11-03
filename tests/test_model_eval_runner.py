"""The evaluator must distinguish genuine correctness from accidental agreement."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from model_eval.cases import Case
from model_eval.google import GeminiRouter, ProviderFailure, request_json
from model_eval.scoring import score


class EvaluationScoringTests(unittest.TestCase):
    def test_spend_accounts_for_thinking_and_reserves_unknown_outcomes(self):
        from model_eval.runner import google_spend

        models = [
            {
                "id": "example",
                "google_input_usd_per_million": 1,
                "google_output_usd_per_million": 2,
            }
        ]
        records = [
            {"kind": "attempt", "id": "1", "model": "example", "reserved_max_usd": 0.1},
            {
                "kind": "result",
                "id": "1",
                "model": "example",
                "metadata": {
                    "usage": {
                        "promptTokenCount": 1000,
                        "candidatesTokenCount": 100,
                        "thoughtsTokenCount": 200,
                        "totalTokenCount": 1300,
                    }
                },
            },
            {"kind": "attempt", "id": "2", "model": "example", "reserved_max_usd": 0.1},
        ]
        cost = google_spend(records, models)
        self.assertAlmostEqual(cost["measured_estimate_usd"], 0.0016)
        self.assertAlmostEqual(cost["unknown_outcome_reserve_usd"], 0.1)
        self.assertAlmostEqual(cost["conservative_used_usd"], 0.1016)

    def test_an_added_filter_fails_even_if_result_count_matches(self):
        case = Case(
            "example",
            [],
            "search_actuators",
            {"service": "on_off", "min_torque_nm": 70},
            {"total": 5},
            "test",
        )
        trace = {
            "name": "search_actuators",
            "parameters": {
                "service": "on_off",
                "min_torque_nm": "70",
                "supply_voltage_v": 24,
            },
            "data": {"status": "ok", "total": 5},
        }
        self.assertFalse(score(case, SimpleNamespace(tool_calls=[trace]))["passed"])

    def test_semantically_equivalent_frequency_clarification_is_accepted(self):
        case = Case(
            "example",
            [],
            "ask_clarification",
            {"field": "frequency"},
            {"field": "frequency"},
            "test",
            alternative_search_arguments={"max_operating_time_s": 20},
        )
        trace = {
            "name": "search_actuators",
            "parameters": {"max_operating_time_s": "20"},
            "data": {"status": "needs_clarification", "fields": ["frequency_hz"]},
        }
        result = score(case, SimpleNamespace(tool_calls=[trace]))
        self.assertTrue(result["passed"])
        self.assertFalse(result["exact_tool"])

    def test_clarification_cannot_drop_or_invent_constraints(self):
        from model_eval.cases import CASES

        case = next(c for c in CASES if c.id == "missing_frequency")
        trace = {
            "name": "search_actuators",
            "parameters": {"service": "on_off", "max_operating_time_s": 99999},
            "data": {"status": "needs_clarification", "fields": ["frequency_hz"]},
        }
        self.assertFalse(score(case, SimpleNamespace(tool_calls=[trace]))["passed"])
        trace["parameters"] = dict(case.alternative_search_arguments)
        self.assertTrue(score(case, SimpleNamespace(tool_calls=[trace]))["passed"])
        trace["parameters"]["csa_required"] = True
        self.assertFalse(score(case, SimpleNamespace(tool_calls=[trace]))["passed"])

    def test_provider_attempts_do_not_disappear_after_successful_retry(self):
        from model_eval.runner import aggregate

        case = Case(
            "example",
            [],
            "get_actuator",
            {"part_numbers": ["761A00-11300000/A"]},
            {},
            "test",
        )
        model = {
            "id": "test",
            "estimated_input_usd_per_million": 1,
            "estimated_output_usd_per_million": 1,
        }
        records = [
            {"kind": "attempt", "model": "test", "case_id": "example"},
            {
                "kind": "result",
                "model": "test",
                "case_id": "example",
                "status": "provider_error",
                "metadata": {"latency_s": 1},
            },
            {"kind": "attempt", "model": "test", "case_id": "example"},
            {
                "kind": "result",
                "model": "test",
                "case_id": "example",
                "status": "evaluated",
                "score": {"passed": True, "exact_tool": True, "valid_call": True},
                "metadata": {
                    "latency_s": 2,
                    "model_version": "test-v1",
                    "usage": {"promptTokenCount": 10},
                },
            },
        ]
        result = aggregate(records, [model], [case])["models"]["test"]
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["provider_error_attempts"], 1)
        self.assertTrue(result["completed"])

    def test_payment_error_is_not_misclassified_as_rate_limit(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://generativelanguage.googleapis.com/",
            402,
            "Payment Required",
            {},
            None,
        )
        with (
            patch("urllib.request.urlopen", side_effect=error),
            self.assertRaises(ProviderFailure) as caught,
        ):
            request_json(
                "https://generativelanguage.googleapis.com/v1beta/models", "unused"
            )
        self.assertEqual(caught.exception.category, "payment_required")

    def test_wrong_value_is_not_saved_by_correct_tool_name(self):
        case = Case(
            "example",
            [],
            "get_actuator",
            {"part_numbers": ["761A00-11300000/A"]},
            {"products.0.measurements.motor_power_w": 15},
            "test",
        )
        trace = {
            "name": "get_actuator",
            "parameters": case.expected_arguments,
            "data": {"products": [{"measurements": {"motor_power_w": 40}}]},
        }
        self.assertFalse(score(case, SimpleNamespace(tool_calls=[trace]))["passed"])

    def test_google_adapter_uses_one_request_and_keeps_credentials_out_of_payload(self):
        tool = SimpleNamespace(
            name="ask_clarification",
            description="Ask",
            args_schema=SimpleNamespace(
                model_json_schema=lambda: {
                    "type": "object",
                    "properties": {"field": {"type": "string"}},
                }
            ),
        )
        adapter = GeminiRouter("gemini-3.8-flash", "secret-do-not-print").bind_tools(
            [tool], tool_choice="required", parallel_tool_calls=False
        )
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "ask_clarification",
                                    "args": {"field": "service"},
                                }
                            }
                        ]
                    }
                }
            ],
            "usageMetadata": {"promptTokenCount": 10},
        }
        with patch("model_eval.google.request_json", return_value=response) as request:
            result = adapter.invoke([("system", "Route"), ("human", "What actuator?")])
        self.assertEqual(adapter.request_count, 1)
        self.assertEqual(result.tool_calls[0]["name"], "ask_clarification")
        self.assertNotIn("secret-do-not-print", str(request.call_args.args[2]))
        self.assertNotIn("temperature", request.call_args.args[2]["generationConfig"])

    def test_other_hosts_are_never_called(self):
        with self.assertRaises(ValueError):
            request_json("https://openrouter.ai/api/v1/chat/completions", "unused", {})

    def test_quota_failure_is_preserved_without_automatic_retry(self):
        adapter = GeminiRouter("gemini-3.8-flash", "unused")
        with patch(
            "model_eval.google.request_json",
            side_effect=ProviderFailure(429, "quota_exhausted"),
        ):
            with self.assertRaises(ProviderFailure):
                adapter.invoke([("human", "Hi")])
        self.assertEqual(adapter.request_count, 1)
        self.assertEqual(adapter.provider_failure.status, 429)


if __name__ == "__main__":
    unittest.main()
