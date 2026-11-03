"""One shared, resumable Google-only evaluation against real SQL tools."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch
import uuid

# Avoid telemetry independent of how the surrounding development shell is configured.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"

from backend.catalog.cli import local_environment
from backend.catalog.db import connect, readiness
from backend.conversation.agent import AgentUnavailable, run_agent
from .cases import CASES, SMOKE_CASE_IDS
from .google import GeminiRouter, api_key, available_models
from .scoring import score

ROOT = Path(__file__).resolve().parents[1]


def hash_json(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def code_signature():
    paths = [
        ROOT / "backend/conversation/agent.py",
        *sorted((ROOT / "backend/catalog").glob("*.py")),
        *sorted((ROOT / "model_eval").glob("*.py")),
    ]
    return hash_json(
        {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        }
    )


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary.replace(path)


@contextmanager
def live_lock():
    path = ROOT / ".cache/model-eval/live.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError(
            "Another live evaluator holds the shared quota lock. Verify its PID before removing a stale lock."
        ) from None
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


class Oracle:
    """Validates the harness without making an inference. Never ranked as a model."""

    def __init__(self, case):
        self.case = case

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, *args, **kwargs):
        return SimpleNamespace(
            tool_calls=[
                dict(name=self.case.expected_tool, args=self.case.expected_arguments)
            ]
        )


def execute(case, adapter):
    query = case.messages[-1]["content"]
    history = case.messages[:-1]
    with connect() as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        # This evaluation may never fall through to a default OpenRouter client.
        with patch(
            "backend.conversation.agent.create_model",
            side_effect=AssertionError("OpenRouter disabled in Google evaluation"),
        ):
            return run_agent(connection, query, history, case.context, model=adapter)


def preflight(cases):
    checked = []
    for case in cases:
        result = execute(case, Oracle(case))
        scored = score(case, result)
        if not scored["passed"]:
            raise ValueError(f"Invalid expected tool/facts in test case: {case.id}")
        checked.append(case.id)
    return checked


def aggregate(records, models, cases):
    expected_ids = {c.id for c in cases}
    results = {}
    for model in models:
        rows = {
            r["case_id"]: r
            for r in records
            if r["kind"] == "result" and r["model"] == model["id"]
        }
        good = [
            r for r in rows.values() if r["status"] in ("evaluated", "protocol_error")
        ]
        complete = set(rows) == expected_ids and len(good) == len(cases)
        all_results = [
            r for r in records if r["kind"] == "result" and r["model"] == model["id"]
        ]
        token_input = sum(
            r.get("metadata", {}).get("usage", {}).get("promptTokenCount", 0)
            for r in all_results
        )
        token_output = sum(
            r.get("metadata", {}).get("usage", {}).get("candidatesTokenCount", 0)
            + r.get("metadata", {}).get("usage", {}).get("thoughtsTokenCount", 0)
            for r in all_results
        )
        results[model["id"]] = {
            "completed": complete,
            "evaluated": len(good),
            "expected_cases": len(cases),
            "passed": sum(r["score"]["passed"] for r in good),
            "accuracy_observed": sum(r["score"]["passed"] for r in good) / len(good)
            if good
            else None,
            "exact_tool": sum(r["score"]["exact_tool"] for r in good),
            "invalid_calls": sum(not r["score"]["valid_call"] for r in good),
            "unresolved_provider_errors": len(rows) - len(good),
            "provider_error_attempts": sum(
                r["status"] == "provider_error" for r in all_results
            ),
            "protocol_error_attempts": sum(
                r["status"] == "protocol_error" for r in all_results
            ),
            "attempts": sum(
                r["kind"] == "attempt" and r["model"] == model["id"] for r in records
            ),
            "median_latency_s": statistics.median(
                [r["metadata"]["latency_s"] for r in good]
            )
            if good
            else None,
            "input_tokens": token_input,
            "output_and_thinking_tokens": token_output,
            "hypothetical_openrouter_usd": round(
                (
                    token_input * model["estimated_input_usd_per_million"]
                    + token_output * model["estimated_output_usd_per_million"]
                )
                / 1e6,
                8,
            ),
            "model_versions": sorted(
                {r["metadata"].get("model_version") or "not_reported" for r in good}
            ),
            "failures": [
                {
                    "case": r["case_id"],
                    "reasons": r.get("score", {}).get("reasons", [r["status"]]),
                }
                for r in rows.values()
                if r["status"] != "evaluated" or not r["score"]["passed"]
            ],
        }
    ranking = sorted(
        results,
        key=lambda m: (
            -results[m]["passed"],
            results[m]["invalid_calls"],
            results[m]["hypothetical_openrouter_usd"],
            results[m]["median_latency_s"] or float("inf"),
        ),
    )
    complete = all(
        r["completed"] and len(r["model_versions"]) == 1 for r in results.values()
    )
    recommendation = None
    if complete:
        top = results[ranking[0]]
        recommendation = dict(
            model=ranking[0],
            scope="Best observed among these Google candidates on a fixed development corpus; deployment provider not tested.",
            all_cases_passed=top["passed"] == len(cases),
            tie_break="Correctness, invalid calls, hypothetical deployment token cost, then latency.",
        )
    return dict(
        status="complete" if complete else "incomplete",
        models=results,
        ranking=ranking if complete else [],
        recommendation=recommendation,
        inference_requests=sum(r["kind"] == "attempt" for r in records),
        openrouter_requests=0,
        limitations=[
            "Single sample per case; no statistical guarantee.",
            "Public development cases, not an independent held-out set.",
            "Prose and numeric rendering are deterministic backend behavior, not model quality.",
            "Google free-tier latency does not predict OpenRouter latency.",
            "Estimated deployment prices are not charges incurred by this evaluation.",
        ],
    )


def reservation(model, config):
    # Conservative local guard: byte count upper-bounds normal text token count;
    # add substantial protocol/schema overhead and the complete output allowance.
    return (
        (config["max_prompt_bytes"] + config["prompt_overhead_token_reserve"])
        * model["google_input_usd_per_million"]
        + config["max_output_tokens"] * model["google_output_usd_per_million"]
    ) / 1e6


def google_spend(records, models):
    by_id = {m["id"]: m for m in models}
    outcomes = {r["id"]: r for r in records if r["kind"] == "result"}
    spent, reserved_unknown = 0.0, 0.0
    for attempt in (r for r in records if r["kind"] == "attempt"):
        model = by_id[attempt["model"]]
        outcome = outcomes.get(attempt["id"], {})
        usage = outcome.get("metadata", {}).get("usage", {})
        if usage.get("promptTokenCount") or usage.get("totalTokenCount"):
            spent += (
                usage.get("promptTokenCount", 0) * model["google_input_usd_per_million"]
                + (
                    usage.get("candidatesTokenCount", 0)
                    + usage.get("thoughtsTokenCount", 0)
                )
                * model["google_output_usd_per_million"]
            ) / 1e6
        else:
            reserved_unknown += attempt["reserved_max_usd"]
    return dict(
        measured_estimate_usd=round(spent, 8),
        unknown_outcome_reserve_usd=round(reserved_unknown, 8),
        conservative_used_usd=round(spent + reserved_unknown, 8),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=Path("reports/model_eval/google-comparison-v2")
    )
    parser.add_argument("--config", type=Path, default=Path("config/model_eval.json"))
    parser.add_argument("--suite", choices=["smoke", "full"], default="full")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-new-requests", type=int, default=54)
    parser.add_argument("--retry-provider-errors", action="store_true")
    args = parser.parse_args()
    if args.max_new_requests < 0 or args.max_new_requests > 60:
        raise ValueError("Use a bounded request budget between 0 and 60")
    local_environment(ROOT / ".env")
    cases = [c for c in CASES if args.suite == "full" or c.id in SMOKE_CASE_IDS]
    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    checked = preflight(cases)
    with connect() as connection:
        catalog = readiness(connection)["catalog"]
    signature = code_signature()
    meta = dict(
        code_signature=signature,
        corpus_hash=hash_json([asdict(c) for c in cases]),
        config=config,
        catalog=catalog,
        cases=[c.id for c in cases],
        source="real_google_api" if not args.dry_run else "no_model_inference",
    )
    if args.dry_run:
        write_json(
            args.out / "preflight.json",
            dict(
                status="preflight_passed",
                checked_cases=checked,
                metadata=meta,
                inference_requests=0,
                note="Oracle only validates expected tools and SQL facts; there are no measured model scores.",
            ),
        )
        print(
            json.dumps(
                dict(
                    status="preflight_passed",
                    checked_cases=len(checked),
                    inference_requests=0,
                )
            )
        )
        return
    key = api_key(ROOT / ".env")
    models = config["models"]
    with live_lock():
        meta_path = args.out / "run.json"
        if meta_path.exists():
            if json.loads(meta_path.read_text(encoding="utf-8")) != meta:
                raise ValueError(
                    "Code, corpus, configuration or active catalogue changed. Use a new output directory for a fair comparison."
                )
        else:
            write_json(meta_path, meta)
        available = available_models(key)
        missing = [m["id"] for m in models if m["id"] not in available]
        if missing:
            raise ValueError(
                "Candidate models not available to this API key: " + ", ".join(missing)
            )
        path = args.out / "results.jsonl"
        records = (
            [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if path.exists()
            else []
        )

        def append(record):
            encoded = json.dumps(record, ensure_ascii=False).replace(key, "[REDACTED]")
            with path.open("a", encoding="utf-8") as stream:
                stream.write(encoded + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            records.append(record)

        consumed, last, blocked = 0, 0.0, set()
        if not args.retry_provider_errors:
            failures = [
                r
                for r in records
                if r["kind"] == "result" and r["status"] == "provider_error"
            ]
            blocked.update(r["model"] for r in failures)
            if any(r.get("http_status") in (400, 401, 402) for r in failures):
                blocked.update(m["id"] for m in models)
        for case in cases:
            for model in models:
                mid = model["id"]
                previous = [
                    r
                    for r in records
                    if r["kind"] == "result"
                    and r["case_id"] == case.id
                    and r["model"] == mid
                ]
                if previous and (
                    previous[-1]["status"] != "provider_error"
                    or not args.retry_provider_errors
                ):
                    continue
                attempts = sum(
                    r["kind"] == "attempt" and r["model"] == mid for r in records
                )
                if (
                    mid in blocked
                    or attempts >= config["max_requests_per_model"]
                    or consumed >= args.max_new_requests
                ):
                    continue
                reserve = reservation(model, config)
                spend = google_spend(records, models)
                if (
                    spend["conservative_used_usd"] + reserve
                    > config["google_budget_usd"]
                ):
                    blocked.update(m["id"] for m in models)
                    print(
                        "Google budget guard reached; no further inference requests.",
                        flush=True,
                    )
                    continue
                if code_signature() != signature:
                    raise ValueError(
                        "Concurrent source change detected; do not mix code versions in a model comparison"
                    )
                with connect() as connection:
                    if readiness(connection)["catalog"] != catalog:
                        raise ValueError("Active catalogue changed during evaluation")
                remaining = config["min_interval_seconds"] - (time.monotonic() - last)
                if remaining > 0:
                    time.sleep(remaining)
                identifier = uuid.uuid4().hex
                append(
                    dict(
                        kind="attempt",
                        id=identifier,
                        model=mid,
                        case_id=case.id,
                        reserved_max_usd=reserve,
                    )
                )
                adapter = GeminiRouter(
                    mid, key, max_output_tokens=config["max_output_tokens"]
                )
                row = dict(
                    kind="result",
                    id=identifier,
                    model=mid,
                    case_id=case.id,
                    category=case.category,
                )
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
                        blocked.add(mid)
                        if failure.status in (400, 401, 402):
                            blocked.update(m["id"] for m in models)
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
                row["metadata"] = adapter.metadata
                append(row)
                consumed += adapter.request_count
                last = time.monotonic()
                summary = aggregate(records, models, cases)
                summary["google_spend"] = dict(
                    google_spend(records, models),
                    client_budget_usd=config["google_budget_usd"],
                )
                write_json(args.out / "summary.json", summary)
                print(
                    json.dumps(
                        {
                            "model": mid,
                            "case": case.id,
                            "status": row["status"],
                            "passed": row.get("score", {}).get("passed"),
                            "new_requests": consumed,
                        }
                    ),
                    flush=True,
                )
        summary = aggregate(records, models, cases)
        summary["google_spend"] = dict(
            google_spend(records, models), client_budget_usd=config["google_budget_usd"]
        )
        write_json(args.out / "summary.json", summary)
        print(
            json.dumps(
                {
                    "status": summary["status"],
                    "inference_requests": summary["inference_requests"],
                    "recommendation": summary["recommendation"],
                }
            )
        )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f"Evaluation stopped: {exc}", file=sys.stderr)
        raise SystemExit(2)
