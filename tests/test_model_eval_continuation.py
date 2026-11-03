"""Continuation safety tests. Transports, credentials, PostgreSQL and sleep are mocked."""

from contextlib import ExitStack, nullcontext
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.conversation.agent import AgentUnavailable
from model_eval.cases import Case
from model_eval.google import ProviderFailure
from model_eval.runner import hash_json
from scripts import continue_model_eval as continuation


def sample_model(name, input_price=1, output_price=2):
    return dict(
        id=name,
        google_input_usd_per_million=input_price,
        google_output_usd_per_million=output_price,
        estimated_input_usd_per_million=input_price,
        estimated_output_usd_per_million=output_price,
    )


def sample_case(name):
    return Case(
        name,
        [{"role": "user", "content": "Question " + name}],
        "ask_clarification",
        {"field": "unsupported"},
        {"status": "needs_clarification"},
        "fixture",
    )


def fake_execute(case, adapter):
    adapter.declarations = [
        {
            "name": "ask_clarification",
            "description": "Ask",
            "parametersJsonSchema": {"type": "object"},
        }
    ]
    try:
        response = adapter.invoke(
            [("system", "Frozen system"), ("human", case.messages[-1]["content"])]
        )
    except Exception:
        raise AgentUnavailable() from None
    calls = response.tool_calls
    if len(calls) != 1:
        raise AgentUnavailable()
    return SimpleNamespace(
        answer="No catalogue figures authored by a model.",
        products=[],
        context={},
        tool_calls=[
            {
                "name": call["name"],
                "parameters": call["args"],
                "data": {"status": "needs_clarification", "field": "unsupported"},
            }
            for call in calls
        ],
    )


def response(usage=None):
    return dict(
        candidates=[
            {
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "ask_clarification",
                                "args": {"field": "unsupported"},
                            }
                        }
                    ]
                },
                "finishReason": "STOP",
            }
        ],
        modelVersion="fixture-v1",
        usageMetadata=usage
        or {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 5,
            "totalTokenCount": 115,
        },
    )


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cases = (sample_case("first"), sample_case("second"), sample_case("third"))
        self.catalog = {
            "id": 2,
            "document_sha256": "source",
            "pipeline_signature": "pipeline",
            "rows": 68,
        }
        self.models = [sample_model("model-a"), sample_model("model-b")]
        self.paths = (self.root / "cohort-a", self.root / "cohort-b")
        for index, path in enumerate(self.paths):
            path.mkdir()
            meta = dict(
                code_signature="frozen",
                corpus_hash=hash_json([asdict(c) for c in self.cases]),
                catalog=self.catalog,
                cases=[c.id for c in self.cases],
                source="real_google_api",
                config={
                    "max_output_tokens": 2048,
                    "thinking_level": "low",
                    "models": [self.models[index]],
                    "google_budget_usd": 0.5 if index == 0 else 0.1,
                    "parent_conservative_used_usd": 0.4 if index else None,
                },
            )
            (path / "run.json").write_text(json.dumps(meta), encoding="utf-8")
            (path / "results.jsonl").write_bytes(b"")
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.addCleanup(self.temp.cleanup)
        self.stack.enter_context(patch.object(continuation, "local_environment"))
        self.stack.enter_context(
            patch.object(
                continuation, "connect", side_effect=lambda: nullcontext(object())
            )
        )
        self.stack.enter_context(
            patch.object(
                continuation, "readiness", return_value={"catalog": self.catalog}
            )
        )
        self.stack.enter_context(
            patch.object(continuation, "code_signature", return_value="frozen")
        )
        self.stack.enter_context(
            patch.object(continuation, "live_lock", side_effect=nullcontext)
        )
        self.stack.enter_context(
            patch.object(continuation, "execute", side_effect=fake_execute)
        )
        self.sleep = self.stack.enter_context(patch.object(continuation.time, "sleep"))
        self.key = self.stack.enter_context(
            patch.object(continuation, "api_key", return_value="DUMMY_TEST_KEY")
        )
        self.network = self.stack.enter_context(
            patch.object(continuation, "request_json", return_value=response())
        )

    def append_fixture(
        self,
        cohort_index,
        case_id,
        *,
        status="provider_error",
        usage=None,
        reserved=0.5,
        http_status=503,
    ):
        model = self.models[cohort_index]["id"]
        identifier = f"{cohort_index}-{case_id}-{len((self.paths[cohort_index] / 'results.jsonl').read_bytes())}"
        attempt = {
            "kind": "attempt",
            "id": identifier,
            "model": model,
            "case_id": case_id,
            "reserved_max_usd": reserved,
        }
        result = {
            "kind": "result",
            "id": identifier,
            "model": model,
            "case_id": case_id,
            "category": "fixture",
            "status": status,
            "metadata": {"latency_s": 1},
        }
        if usage:
            result["metadata"].update(usage=usage, model_version="fixture-v1")
        if status == "provider_error":
            result.update(http_status=http_status, error_category="upstream_error")
        else:
            result["score"] = {
                "passed": status == "evaluated",
                "exact_tool": True,
                "valid_call": True,
                "reasons": [],
            }
        path = self.paths[cohort_index] / "results.jsonl"
        with path.open("ab") as stream:
            for record in (attempt, result):
                stream.write((json.dumps(record) + "\n").encode())
        return attempt

    def run_continuation(self, **kwargs):
        return continuation.continue_evaluation(
            models=[m["id"] for m in self.models],
            cohort_paths=self.paths,
            report_path=self.root / "continuation.json",
            cases=self.cases,
            **kwargs,
        )

    def test_capture_uses_exact_serialization_and_no_real_transport_or_key(self):
        detail = continuation.capture_reservation(self.cases[0], self.models[0])
        self.network.assert_not_called()
        self.key.assert_not_called()
        self.assertEqual(
            detail["reserved_max_usd"],
            ((detail["payload_bytes"] + 4096) * 1 + 2048 * 2) / 1e6,
        )
        self.assertEqual(len(detail["payload_sha256"]), 64)

    def test_dry_run_preserves_jsonl_and_only_writes_payload_evidence(self):
        self.append_fixture(0, "first")
        before = {p: (p / "results.jsonl").read_bytes() for p in self.paths}
        result = self.run_continuation(dry_run=True, max_new_requests=2)
        self.assertEqual(result["new_inference_requests"], 0)
        self.assertEqual(len(result["planned_requests"]), 2)
        self.network.assert_not_called()
        self.key.assert_not_called()
        for path in self.paths:
            self.assertEqual((path / "results.jsonl").read_bytes(), before[path])
            side = json.loads((path / "reservation_refinements.json").read_text())
            self.assertFalse(side["mock_scores_saved"])
            self.assertFalse(side["original_records_rewritten"])
            self.assertFalse(any("score" in p for p in side["payloads"]))

    def test_frozen_metadata_mismatch_rejects_before_capture(self):
        path = self.paths[1] / "run.json"
        data = json.loads(path.read_text())
        data["corpus_hash"] = "changed"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Frozen"):
            self.run_continuation(dry_run=True)
        self.network.assert_not_called()
        self.key.assert_not_called()

    def test_global_budget_sums_cohorts_without_parent_double_counting(self):
        self.append_fixture(0, "first")
        self.append_fixture(1, "first")
        result = self.run_continuation(dry_run=True, max_new_requests=0)
        captures = []
        for path in self.paths:
            captures += json.loads((path / "reservation_refinements.json").read_text())[
                "attempt_refinements"
            ]
        expected = sum(r["reserved_max_usd"] for r in captures)
        self.assertAlmostEqual(
            result["google_spend"]["conservative_used_usd"], expected, places=7
        )
        self.assertLess(expected, 0.1)

    def test_unknown_outcome_retains_full_refined_reservation_and_usage_counts_thinking_once(
        self,
    ):
        self.append_fixture(0, "first")
        usage = {
            "promptTokenCount": 1000,
            "candidatesTokenCount": 100,
            "thoughtsTokenCount": 200,
            "totalTokenCount": 1300,
        }
        self.append_fixture(1, "first", status="evaluated", usage=usage)
        result = self.run_continuation(dry_run=True, max_new_requests=0)
        detail = json.loads(
            (self.paths[0] / "reservation_refinements.json").read_text()
        )["attempt_refinements"][0]
        spend = result["google_spend"]
        self.assertAlmostEqual(
            spend["unknown_outcome_reserve_usd"], detail["reserved_max_usd"], places=7
        )
        self.assertAlmostEqual(spend["measured_estimate_usd"], 0.0016)

    def test_live_mock_never_repeats_evaluated_or_protocol_rows_and_appends(self):
        self.append_fixture(
            0, "first", status="evaluated", usage={"promptTokenCount": 100}
        )
        self.append_fixture(
            1, "first", status="protocol_error", usage={"promptTokenCount": 100}
        )
        before = {p: (p / "results.jsonl").read_bytes() for p in self.paths}
        result = self.run_continuation(max_new_requests=2)
        self.assertEqual(result["new_inference_requests"], 2)
        self.assertEqual(self.network.call_count, 2)
        for path in self.paths:
            raw = (path / "results.jsonl").read_bytes()
            self.assertTrue(raw.startswith(before[path]))
            additions = [json.loads(l) for l in raw[len(before[path]) :].splitlines()]
            self.assertEqual(len(additions), 2)
            self.assertEqual(additions[0]["case_id"], "second")
            self.assertEqual(additions[0]["reservation_method"], continuation.METHOD)
            self.assertEqual(additions[1]["status"], "evaluated")

    def test_two_provider_errors_stop_only_that_model_and_keep_unknown_reserves(self):
        self.network.side_effect = ProviderFailure(503, "upstream_error")
        result = self.run_continuation(max_new_requests=30)
        self.assertEqual(result["new_inference_requests"], 4)
        self.assertEqual(
            set(result["stopped_models"].values()), {"two_consecutive_errors"}
        )
        self.assertGreater(result["google_spend"]["unknown_outcome_reserve_usd"], 0)

    def test_auth_payment_or_invalid_request_stops_all_models(self):
        for status in (400, 401, 402):
            with self.subTest(status=status):
                # Reset only temporary fixture logs so each fatal status is live-tested.
                for path in self.paths:
                    (path / "results.jsonl").write_bytes(b"")
                self.network.side_effect = ProviderFailure(status, "fatal")
                result = self.run_continuation(max_new_requests=30)
                self.assertEqual(result["global_stop"], "fatal_provider_error")
                self.assertEqual(result["new_inference_requests"], 1)

    def test_attempt_cap_includes_historical_failures(self):
        self.append_fixture(0, "first")
        self.append_fixture(0, "first")
        result = self.run_continuation(dry_run=True, max_attempts_per_model=2)
        self.assertEqual(result["stopped_models"]["model-a"], "attempt_limit")
        self.assertTrue(
            all(p["model"] != "model-a" for p in result["planned_requests"])
        )

    def test_actual_transport_payload_mismatch_stops_without_network(self):
        original = continuation.capture_reservation

        def wrong_hash(case, model):
            result = original(case, model)
            result["payload_sha256"] = "0" * 64
            return result

        with patch.object(continuation, "capture_reservation", side_effect=wrong_hash):
            result = self.run_continuation(max_new_requests=2)
        self.assertEqual(result["global_stop"], "frozen_payload_mismatch")
        self.assertEqual(result["new_inference_requests"], 0)
        self.network.assert_not_called()

    def test_global_budget_prevents_any_new_call(self):
        self.append_fixture(0, "first")
        self.append_fixture(1, "first")
        original = continuation.capture_reservation

        def costly(case, model):
            result = original(case, model)
            result["reserved_max_usd"] = 0.3
            return result

        with patch.object(continuation, "capture_reservation", side_effect=costly):
            result = self.run_continuation(max_new_requests=30)
        self.assertEqual(result["global_stop"], "global_budget_guard")
        self.assertEqual(result["new_inference_requests"], 0)
        self.key.assert_not_called()


if __name__ == "__main__":
    unittest.main()
