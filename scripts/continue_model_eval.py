"""Append-only continuation of two frozen Google model-evaluation cohorts.

No backend, prompt, corpus, historical attempt or measured score is rewritten.
Payload capture uses a patched transport and never counts as a model result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.catalog.cli import local_environment
from backend.catalog.db import connect, readiness
from backend.conversation.agent import AgentUnavailable
from model_eval.cases import CASES
from model_eval.google import API_ROOT, GeminiRouter, api_key, request_json
from model_eval.runner import (
    aggregate,
    code_signature,
    execute,
    google_spend,
    hash_json,
    live_lock,
    write_json,
)
from model_eval.scoring import score

COHORT_PATHS = (
    ROOT / "reports/model_eval/google-comparison-v2",
    ROOT / "reports/model_eval/google-additional",
)
REPORT_PATH = ROOT / "reports/model_eval/continuation.json"
GLOBAL_BUDGET_USD = 0.50
OUTPUT_TOKENS = 2048
OVERHEAD_TOKENS = 4096
MIN_INTERVAL_SECONDS = 5
METHOD = "exact_payload_bytes_plus_4096_input_tokens_and_2048_output_tokens"
DEFAULT_MODELS = ("gemini-3.6-flash", "gemini-3-flash-preview")


@dataclass
class Cohort:
    path: Path
    metadata: dict
    records: list[dict]
    prefix_bytes: int
    prefix_sha256: str
    expected_bytes: int
    expected_sha256: str


def payload_bytes(payload):
    """Exactly the serialization used by model_eval.google.request_json."""
    return json.dumps(payload).encode()


def load_cohorts(paths, cases, signature, catalog):
    cohorts, seen_models, seen_attempts = [], set(), set()
    expected_ids = [case.id for case in cases]
    corpus_hash = hash_json([asdict(case) for case in cases])
    for path in paths:
        meta = json.loads((path / "run.json").read_text(encoding="utf-8"))
        if (
            meta["code_signature"] != signature
            or meta["corpus_hash"] != corpus_hash
            or meta["catalog"] != catalog
            or meta["cases"] != expected_ids
            or meta["source"] != "real_google_api"
        ):
            raise ValueError(
                "Frozen code, corpus or active catalogue differs from the cohort"
            )
        config = meta["config"]
        if (
            config["max_output_tokens"] != OUTPUT_TOKENS
            or config["thinking_level"] != "low"
        ):
            raise ValueError(
                "Frozen generation settings are incompatible with this continuation"
            )
        raw = (path / "results.jsonl").read_bytes()
        if raw and not raw.endswith(b"\n"):
            raise ValueError(
                "Incomplete JSONL tail; historical evidence must not be truncated"
            )
        records = [
            json.loads(line)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]
        model_ids = {model["id"] for model in config["models"]}
        if seen_models & model_ids:
            raise ValueError(
                "A model belongs to multiple cohorts; budget attribution is ambiguous"
            )
        seen_models.update(model_ids)
        for model in config["models"]:
            for key in (
                "google_input_usd_per_million",
                "google_output_usd_per_million",
            ):
                if (
                    not isinstance(model[key], (int, float))
                    or not math.isfinite(model[key])
                    or model[key] < 0
                ):
                    raise ValueError("Invalid frozen Google tariff")
        own_attempts, outcomes = {}, set()
        for record in records:
            if (
                record["model"] not in model_ids
                or record["case_id"] not in expected_ids
            ):
                raise ValueError("Record does not belong to its frozen cohort")
            if record["kind"] == "attempt":
                if record["id"] in seen_attempts:
                    raise ValueError("Attempt ID is duplicated across cohorts")
                seen_attempts.add(record["id"])
                own_attempts[record["id"]] = record
            elif record["kind"] != "result":
                raise ValueError("Unknown record kind")
            else:
                attempt = own_attempts.get(record["id"])
                if (
                    attempt is None
                    or record["id"] in outcomes
                    or any(record[key] != attempt[key] for key in ("model", "case_id"))
                ):
                    raise ValueError("Result does not match one prior attempt")
                outcomes.add(record["id"])
        checksum = hashlib.sha256(raw).hexdigest()
        cohorts.append(
            Cohort(path, meta, records, len(raw), checksum, len(raw), checksum)
        )
    return cohorts


def capture_reservation(case, model):
    """Capture a frozen real request via normal execute(), with transport disabled."""
    captured = []

    def capture(endpoint, key, payload=None):
        if endpoint != API_ROOT + "models/" + model["id"] + ":generateContent":
            raise ValueError("Unexpected endpoint during payload capture")
        captured.append(payload_bytes(payload))
        return {
            "candidates": [
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
                    }
                }
            ]
        }

    adapter = GeminiRouter(
        model["id"], "NO_NETWORK_PAYLOAD_CAPTURE", max_output_tokens=OUTPUT_TOKENS
    )
    with patch("model_eval.google.request_json", side_effect=capture):
        execute(case, adapter)  # Deliberately discard this mock result; never score it.
    if len(captured) != 1:
        raise ValueError("Payload capture did not produce exactly one request")
    encoded = captured[0]
    reserve = (
        (len(encoded) + OVERHEAD_TOKENS) * model["google_input_usd_per_million"]
        + OUTPUT_TOKENS * model["google_output_usd_per_million"]
    ) / 1e6
    return dict(
        model=model["id"],
        case_id=case.id,
        payload_bytes=len(encoded),
        payload_sha256=hashlib.sha256(encoded).hexdigest(),
        input_overhead_token_reserve=OVERHEAD_TOKENS,
        max_output_tokens=OUTPUT_TOKENS,
        reserved_max_usd=reserve,
        reservation_method=METHOD,
        google_input_usd_per_million=model["google_input_usd_per_million"],
        google_output_usd_per_million=model["google_output_usd_per_million"],
    )


def project_records(cohort, refinements):
    """Change reserves only on in-memory copies; original JSONL remains untouched."""
    projected = []
    for record in cohort.records:
        copy = dict(record)
        if record["kind"] == "attempt":
            copy["reserved_max_usd"] = refinements[
                (record["model"], record["case_id"])
            ]["reserved_max_usd"]
        projected.append(copy)
    return projected


def terminal_case(cohort, model, case_id):
    # Never repeat a completed/protocol result, even if a later stray error exists.
    return any(
        record["kind"] == "result"
        and record["model"] == model
        and record["case_id"] == case_id
        and record["status"] in ("evaluated", "protocol_error")
        for record in cohort.records
    )


def attempts_for(cohorts, model):
    return sum(
        r["kind"] == "attempt" and r["model"] == model
        for c in cohorts
        for r in c.records
    )


def combined_spend(cohorts, refinements):
    models = [m for c in cohorts for m in c.metadata["config"]["models"]]
    records = [r for c in cohorts for r in project_records(c, refinements)]
    return google_spend(records, models)


def append_record(cohort, record, key):
    encoded = json.dumps(record, ensure_ascii=False).replace(key, "[REDACTED]")
    # An external writer that ignores the common lock must not silently mix runs.
    raw = (cohort.path / "results.jsonl").read_bytes()
    if (
        len(raw) != cohort.expected_bytes
        or hashlib.sha256(raw).hexdigest() != cohort.expected_sha256
    ):
        raise ValueError("Historical JSONL was modified externally")
    extra = (encoded + "\n").encode("utf-8")
    with (cohort.path / "results.jsonl").open(
        "a", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(encoded + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    cohort.expected_bytes += len(extra)
    cohort.expected_sha256 = hashlib.sha256(raw + extra).hexdigest()
    cohort.records.append(json.loads(encoded))


def save_evidence(cohorts, refinements, cases, signature, catalog, report):
    for cohort in cohorts:
        model_ids = {m["id"] for m in cohort.metadata["config"]["models"]}
        attempt_refinements = [
            dict(
                attempt_id=r["id"],
                original_reserved_max_usd=r["reserved_max_usd"],
                **refinements[(r["model"], r["case_id"])],
            )
            for r in cohort.records
            if r["kind"] == "attempt"
        ]
        sidecar = dict(
            schema_version=1,
            reservation_method=METHOD,
            code_signature=signature,
            corpus_hash=cohort.metadata["corpus_hash"],
            catalog=catalog,
            original_prefix_bytes=cohort.prefix_bytes,
            original_prefix_sha256=cohort.prefix_sha256,
            payloads=[
                value for (model, _), value in refinements.items() if model in model_ids
            ],
            attempt_refinements=attempt_refinements,
            mock_scores_saved=False,
            original_records_rewritten=False,
        )
        write_json(cohort.path / "reservation_refinements.json", sidecar)
        summary = aggregate(cohort.records, cohort.metadata["config"]["models"], cases)
        summary["google_spend"] = dict(
            google_spend(
                project_records(cohort, refinements),
                cohort.metadata["config"]["models"],
            ),
            client_budget_usd=GLOBAL_BUDGET_USD,
            budget_scope="shared_across_both_cohorts",
            reservation_method=METHOD,
        )
        write_json(cohort.path / "summary.json", summary)
    report["google_spend"] = dict(
        combined_spend(cohorts, refinements),
        client_budget_usd=GLOBAL_BUDGET_USD,
        scope="both_cohorts_all_models_and_all_historical_attempts",
    )
    return report


def continue_evaluation(
    *,
    models=DEFAULT_MODELS,
    max_new_requests=30,
    max_attempts_per_model=24,
    dry_run=False,
    cohort_paths=COHORT_PATHS,
    report_path=REPORT_PATH,
    cases=CASES,
):
    if not 0 <= max_new_requests <= 60 or not 1 <= max_attempts_per_model <= 60:
        raise ValueError("Use bounded request/attempt limits between 0..60 and 1..60")
    selected = list(dict.fromkeys(models))
    if not selected:
        raise ValueError("Select at least one frozen candidate model")
    local_environment(ROOT / ".env")
    with live_lock():
        with connect() as connection:
            catalog = readiness(connection)["catalog"]
        signature = code_signature()
        cohorts = load_cohorts(cohort_paths, cases, signature, catalog)
        by_model = {
            m["id"]: (c, m) for c in cohorts for m in c.metadata["config"]["models"]
        }
        if set(selected) - by_model.keys():
            raise ValueError("Selected model is not part of the frozen cohorts")
        by_case = {case.id: case for case in cases}
        needed = {
            (r["model"], r["case_id"])
            for c in cohorts
            for r in c.records
            if r["kind"] == "attempt"
        }
        needed.update((model, case.id) for model in selected for case in cases)
        refinements = {
            pair: capture_reservation(by_case[pair[1]], by_model[pair[0]][1])
            for pair in sorted(needed)
        }
        if code_signature() != signature:
            raise ValueError("Frozen source changed during payload capture")
        with connect() as connection:
            if readiness(connection)["catalog"] != catalog:
                raise ValueError("Active catalogue changed during payload capture")
        limits = dict(
            max_new_requests=max_new_requests,
            max_attempts_per_model=max_attempts_per_model,
            original_max_attempts_per_model=20,
            operational_extension=max_attempts_per_model > 20,
            min_interval_seconds=MIN_INTERVAL_SECONDS,
            consecutive_error_limit=2,
            consecutive_error_scope="this_explicit_continuation_invocation",
            global_google_budget_usd=GLOBAL_BUDGET_USD,
        )
        report = dict(
            status="dry_run" if dry_run else "continued",
            dry_run=dry_run,
            models=selected,
            code_signature=signature,
            corpus_hash=hash_json([asdict(c) for c in cases]),
            catalog=catalog,
            operational_limits=limits,
            new_inference_requests=0,
            appended_attempts=0,
            planned_requests=[],
            stopped_models={},
            global_stop=None,
            openrouter_requests=0,
            reservation_method=METHOD,
            mock_scores_saved=False,
        )
        # A previous fatal configuration/auth/payment error cannot be repaired by retrying identical inputs.
        fatal = [
            r
            for c in cohorts
            for r in c.records
            if r["kind"] == "result" and r.get("http_status") in (400, 401, 402)
        ]
        if fatal:
            report["global_stop"] = "historical_fatal_provider_error"
        key = None
        streak = {model: 0 for model in selected}
        last_request_start = 0.0
        planned_by_model = {model: 0 for model in selected}
        projected_future_reserve = 0.0
        for case in cases:
            for mid in selected:
                if report["global_stop"]:
                    break
                cohort, model = by_model[mid]
                if mid in report["stopped_models"] or terminal_case(
                    cohort, mid, case.id
                ):
                    continue
                attempt_count = attempts_for(cohorts, mid) + (
                    planned_by_model[mid] if dry_run else 0
                )
                if attempt_count >= max_attempts_per_model:
                    report["stopped_models"][mid] = "attempt_limit"
                    continue
                consumed = (
                    len(report["planned_requests"])
                    if dry_run
                    else report["new_inference_requests"]
                )
                if consumed >= max_new_requests:
                    report["global_stop"] = "new_request_limit"
                    break
                refinement = refinements[(mid, case.id)]
                spend = combined_spend(cohorts, refinements)
                if (
                    spend["conservative_used_usd"]
                    + projected_future_reserve
                    + refinement["reserved_max_usd"]
                    > GLOBAL_BUDGET_USD
                ):
                    report["global_stop"] = "global_budget_guard"
                    break
                if dry_run:
                    report["planned_requests"].append(
                        dict(
                            model=mid,
                            case_id=case.id,
                            reserved_max_usd=refinement["reserved_max_usd"],
                        )
                    )
                    planned_by_model[mid] += 1
                    projected_future_reserve += refinement["reserved_max_usd"]
                    continue
                if code_signature() != signature:
                    raise ValueError("Concurrent frozen-source change detected")
                with connect() as connection:
                    if readiness(connection)["catalog"] != catalog:
                        raise ValueError("Active catalogue changed before inference")
                if key is None:
                    key = api_key(ROOT / ".env")
                pause = MIN_INTERVAL_SECONDS - (time.monotonic() - last_request_start)
                if pause > 0:
                    time.sleep(pause)
                identifier = uuid.uuid4().hex
                append_record(
                    cohort,
                    dict(
                        kind="attempt",
                        id=identifier,
                        model=mid,
                        case_id=case.id,
                        reserved_max_usd=refinement["reserved_max_usd"],
                        reservation_method=METHOD,
                        payload_bytes=refinement["payload_bytes"],
                        payload_sha256=refinement["payload_sha256"],
                        operational_limits=limits,
                    ),
                    key,
                )
                report["appended_attempts"] += 1
                adapter = GeminiRouter(mid, key, max_output_tokens=OUTPUT_TOKENS)
                network = {"count": 0, "payload_mismatch": False}

                def frozen_transport(endpoint, actual_key, payload=None):
                    encoded = payload_bytes(payload)
                    if (
                        len(encoded) != refinement["payload_bytes"]
                        or hashlib.sha256(encoded).hexdigest()
                        != refinement["payload_sha256"]
                    ):
                        network["payload_mismatch"] = True
                        raise ValueError("Request differs from captured frozen payload")
                    if endpoint != API_ROOT + "models/" + mid + ":generateContent":
                        raise ValueError("Unexpected Google model endpoint")
                    network["count"] += 1
                    return request_json(endpoint, actual_key, payload)

                row = dict(
                    kind="result",
                    id=identifier,
                    model=mid,
                    case_id=case.id,
                    category=case.category,
                )
                last_request_start = time.monotonic()
                with patch(
                    "model_eval.google.request_json", side_effect=frozen_transport
                ):
                    try:
                        result = execute(case, adapter)
                        row.update(
                            status="evaluated",
                            score=score(case, result),
                            raw_calls=adapter.calls,
                            answer=result.answer,
                            trace=result.tool_calls,
                            context=result.context,
                        )
                    except AgentUnavailable:
                        if adapter.provider_failure:
                            failure = adapter.provider_failure
                            row.update(
                                status="provider_error",
                                http_status=failure.status,
                                error_category=failure.category,
                            )
                            if failure.status in (400, 401, 402):
                                report["global_stop"] = "fatal_provider_error"
                        else:
                            row.update(
                                status="protocol_error",
                                raw_calls=adapter.calls,
                                score=dict(
                                    passed=False,
                                    exact_tool=False,
                                    correct_arguments=False,
                                    valid_call=False,
                                    facts_ok=False,
                                    reasons=["invalid_model_tool_protocol"],
                                ),
                            )
                if network["payload_mismatch"]:
                    report["global_stop"] = "frozen_payload_mismatch"
                report["new_inference_requests"] += network["count"]
                adapter.metadata.setdefault(
                    "latency_s", round(time.monotonic() - last_request_start, 4)
                )
                row["metadata"] = adapter.metadata
                append_record(cohort, row, key)
                streak[mid] = (
                    streak[mid] + 1
                    if row["status"] in ("provider_error", "protocol_error")
                    else 0
                )
                if streak[mid] >= 2:
                    report["stopped_models"][mid] = "two_consecutive_errors"
                save_evidence(cohorts, refinements, cases, signature, catalog, report)
                report_path.parent.mkdir(parents=True, exist_ok=True)
                write_json(report_path, report)
                print(
                    json.dumps(
                        dict(
                            model=mid,
                            case=case.id,
                            status=row["status"],
                            new_requests=report["new_inference_requests"],
                        )
                    ),
                    flush=True,
                )
            if report["global_stop"]:
                break
        report["dry_run_future_reserve_usd"] = (
            round(projected_future_reserve, 8) if dry_run else None
        )
        save_evidence(cohorts, refinements, cases, signature, catalog, report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(report_path, report)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--max-new-requests", type=int, default=30)
    parser.add_argument(
        "--max-attempts-per-model",
        type=int,
        default=24,
        help="Explicit operational attempt cap; original cohort cap was20. Prompts remain unchanged.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    models = [model for item in args.models for model in item.split(",") if model]
    result = continue_evaluation(
        models=models,
        max_new_requests=args.max_new_requests,
        max_attempts_per_model=args.max_attempts_per_model,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f"Continuation stopped: {exc}", file=sys.stderr)
        raise SystemExit(2)
