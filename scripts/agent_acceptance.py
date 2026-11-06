"""Real-LLM acceptance of the A+ agent (experimental Google endpoint, production client).

The production code path is used unchanged: FastAPI /api/conversation -> run_agent ->
LangChain ChatOpenAI -> tool decision -> code validation -> SQL -> rendered answer.
Only the OpenAI-compatible base URL/model differ from OpenRouter. Each scenario runs in a
rollback-only transaction, so the operational database keeps no acceptance data.

Commands:
  selfcheck  scripted ideal decisions: proves expectations are reachable (no network)
  probe      one paid call: does the endpoint accept tool_choice=required?
  run        paid cohort; resumable, append-only results and ledger, frozen inputs
  report     offline summary from results.jsonl and ledger.jsonl

The provider key is read from the process environment only; it is never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from copy import deepcopy
import sys
import time
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "reports/agent_acceptance/v2"  # overridden by --cohort
CONFIG = ROOT / "config/agent_acceptance.json"
CASES = ROOT / "config/agent_acceptance_cases.json"
FROZEN_FILES = [ "config/agent_acceptance_cases.json", "scripts/agent_acceptance.py",
                "scripts/acceptance_contract.py", "backend/conversation/interactions.py",
                "backend/catalog/migrations/005_message_interactions.sql",
                "scripts/check_public_text.py",
                "backend/conversation/quality.py", "backend/conversation/store.py",
                "backend/conversation/tool_wire.py",
                "backend/catalog/migrations/004_message_presentation.sql",
                "backend/conversation/agent.py", "backend/conversation/policy.py", "backend/conversation/rendering.py",
                "backend/conversation/api.py", "backend/app/contracts.py", "backend/catalog/models.py",
                "backend/catalog/repository.py", "backend/catalog/context.py", "data/extracted/series76_summary/terms.json",
                "data/extracted/series76/catalog.csv"]


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def append(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def provider_key(config):
    variable = "OPENROUTER_API_KEY" if config["provider"] == "openrouter" else "GOOGLE_API_KEY"
    key = os.environ.get(variable, "").strip()
    if not key:
        raise SystemExit(f"{variable} not configured in process environment")
    return key


# --- budget -------------------------------------------------------------------------------
class BudgetStop(Exception):
    pass


class Ledger:
    def __init__(self, config):
        self.path, self.config, self.last = OUT / "ledger.jsonl", config, 0.0

    def spent(self):
        charges = {}
        for event in read_jsonl(self.path):
            charges[event["id"]] = event["charged_usd"]
        return sum(charges.values())

    def reserve(self, payload_bytes, label):
        c = self.config
        amount = ((payload_bytes + 4096) * c["input_usd_per_million"] + c["max_tokens"] * c["output_usd_per_million"]) / 1e6
        if self.spent() + amount > c["safety_cap_usd"]:
            raise BudgetStop("Safety cap reached")
        event = dict(id=len({e["id"] for e in read_jsonl(self.path)}) + 1, state="reserved", charged_usd=amount,
                     reserved_usd=amount, label=label, time=time.time())
        append(self.path, event)
        return event

    def settle(self, event, usage, latency):
        c = self.config
        prompt = usage.get("prompt_tokens") or 0
        completion = usage.get("completion_tokens") or 0
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        # Conservative: reasoning is added even if the provider already counted it in completion.
        charged = (prompt * c["input_usd_per_million"] + (completion + reasoning) * c["output_usd_per_million"]) / 1e6
        append(self.path, dict(event, state="settled", charged_usd=charged, usage=usage, latency_s=latency))

    def fail(self, event, error, status, latency):
        append(self.path, dict(event, state="failed", error=error, status=status, latency_s=latency))


class Budgeted:
    """Wraps the production ChatOpenAI: reserve before the network, settle after."""

    def __init__(self, client, ledger, label):
        self.client, self.ledger, self.label, self.bound = client, ledger, label, None

    def bind_tools(self, tools, **kwargs):
        self.tools = tools
        self.bound = self.client.bind_tools(tools, **kwargs)
        return self

    def invoke(self, messages, **kwargs):
        from langchain_core.utils.function_calling import convert_to_openai_tool
        payload = canonical([[getattr(m, "content", m) for m in messages], [convert_to_openai_tool(t) for t in self.tools]])
        event = self.ledger.reserve(len(payload.encode("utf-8")), self.label)
        wait = self.ledger.config["min_interval_seconds"] - (time.monotonic() - self.ledger.last)
        if wait > 0:
            time.sleep(wait)
        start = time.perf_counter()
        try:
            response = self.bound.invoke(messages, **kwargs)
        except Exception as exc:
            self.ledger.last = time.monotonic()
            self.ledger.fail(event, type(exc).__name__, getattr(exc, "status_code", None), time.perf_counter() - start)
            raise
        self.ledger.last = time.monotonic()
        usage = (getattr(response, "response_metadata", {}) or {}).get("token_usage") or {}
        self.ledger.settle(event, usage, time.perf_counter() - start)
        return response


def configure_env(config, key):
    os.environ.update(OPENROUTER_API_KEY=key, OPENROUTER_BASE_URL=config["base_url"], OPENROUTER_CHAT_MODEL=config["model"],
                      AGENT_MAX_TOKENS=str(config["max_tokens"]), AGENT_REASONING_EFFORT=config["reasoning_effort"],
                      AGENT_TOOL_CHOICE=config["tool_choice"])


# --- scoring ------------------------------------------------------------------------------
def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        a = {k: v for k, v in a.items() if v is not None}
        b = {k: v for k, v in b.items() if v is not None}
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return a == b


def numeric_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    try:
        a, b = Decimal(str(a)), Decimal(str(b))
        return a.is_finite() and b.is_finite() and a == b
    except Exception:
        return False


def argument_matches(field, got, expected, queries=()):
    """Only numeric bound fields bridge scalar/bound representations; never drop op.

    Old scalar expectations may accept a gte bound only when the case's current or
    preceding query explicitly says at least/minimum for that same value.
    Other operators require explicit {value, op} expectations.
    """
    from backend.catalog.repository import COMPARISONS
    if field not in COMPARISONS:
        return same(got, expected)
    if isinstance(expected, list):
        return isinstance(got, list) and len(got) == len(expected) and all(
            argument_matches(field, a, b, queries) for a, b in zip(got, expected))
    if isinstance(expected, dict):
        if set(expected) != {"value", "op"}:
            return False
        if not isinstance(got, dict):
            # Legacy scalar inputs have the repository's inclusive default only.
            got = {"value": got, "op": "gte" if field.startswith("min_") else "lte"}
        return (set(got) == {"value", "op"} and expected["op"] in {"gt", "gte", "lt", "lte"}
                and got["op"] == expected["op"] and numeric_equal(got["value"], expected["value"]))
    if isinstance(got, dict):
        stated_minimum = any(numeric_equal(m, expected) for q in queries for m in re.findall(
            r"(?:at least|minimum(?: of)?)\s+(\d+(?:\.\d+)?)", q.lower()))
        return (field.startswith("min_") and stated_minimum and set(got) == {"value", "op"}
                and got["op"] == "gte" and numeric_equal(got["value"], expected))
    return same(got, expected)


def check(expect, observed, queries=()):
    from scripts.check_public_text import response_text_issues
    from backend.catalog.repository import COMPARISONS
    failures = response_text_issues(observed)
    trace = observed["trace"]
    params = trace.get("parameters") or {}
    if "tool" in expect and trace.get("name") != expect["tool"]:
        failures.append(f"tool {trace.get('name')} != {expect['tool']}")
    for field, value in (expect.get("args") or {}).items():
        got = trace.get("raw_parameters", {}).get(field) if field == "cancel_previous" else params.get(field)
        if isinstance(value, list) and field not in COMPARISONS:
            if not same(got or [], value):
                failures.append(f"{field} {got} != {value}")
        elif not argument_matches(field, got, value, queries):
            failures.append(f"{field} {got} != {value}")
    if expect.get("only_filters"):
        from backend.conversation.policy import FILTER_FIELDS
        present = {k for k in FILTER_FIELDS if params.get(k) not in (None, False)}
        extra = present - set(expect.get("args", {})) - set(expect.get("allow_extra", []))
        if extra:
            failures.append(f"added filters {sorted(extra)}")
    clarification = observed["clarification"]
    if "clarification" in expect and (not clarification or clarification.get("field") not in expect["clarification"]):
        failures.append(f"clarification {clarification and clarification.get('field')} not in {expect['clarification']}")
    if "conflict" in expect and ((clarification or {}).get("conflict") or {}).get("kind") != expect["conflict"]:
        failures.append(f"conflict {(clarification or {}).get('conflict')} != {expect['conflict']}")
    for text in expect.get("contains", []):
        if text not in observed["answer"]:
            failures.append(f"missing text: {text}")
    for text in expect.get("not_contains", []):
        if text in observed["answer"]:
            failures.append(f"forbidden text: {text}")
    for text in expect.get('lead_contains', []):
        if text not in (observed.get('lead') or ''):
            failures.append(f'missing lead text: {text}')
    if 'interaction_option_labels' in expect:
        labels = [option['label'] for question in (observed.get('interaction') or {}).get('questions', [])
                  for option in question.get('options', [])]
        if labels != expect['interaction_option_labels']:
            failures.append(f'option labels {labels} differ')
    codes = [p["base_part_number"] for p in observed["products"]]
    for code in expect.get("products_include", []):
        if code not in codes:
            failures.append(f"product {code} missing")
    if "comparison_models" in expect and (observed.get("comparison") or {}).get("models") != expect["comparison_models"]:
        failures.append("comparison models differ")
    if expect.get("no_products") and codes:
        failures.append(f"unexpected products {codes[:3]}")
    recommendation = observed.get('recommendation') or {}
    if expect.get('recommendation_codes_once'):
        for item in recommendation.get('items', []):
            code = item['part_number']
            if observed['answer'].count(code) != 1:
                failures.append('ranked code repeated or absent in answer: ' + code)
    if 'recommendation_total' in expect and recommendation.get('total') != expect['recommendation_total']:
        failures.append('recommendation total differs')
    recommendation_codes = [item['part_number'] for item in recommendation.get('items', [])]
    if 'recommendation_first' in expect and (recommendation_codes or [None])[0] != expect['recommendation_first']:
        failures.append('recommended winner differs')
    if 'recommendation_scope' in expect and not set(recommendation_codes) <= set(expect['recommendation_scope']):
        failures.append('recommendation escaped the shown set')
    if expect.get('recommendation_safe'):
        from scripts.acceptance_contract import eligible_codes
        filters = (trace.get('context_after') or {}).get('filters') or {}
        if not set(recommendation_codes) <= set(eligible_codes(filters)):
            failures.append('recommendation violates the independent CSV requirements oracle')
    if expect.get('recommendation_ranked_by') and not recommendation.get('ranked_by'):
        failures.append('ranking explanation missing')
    if 'debug_llm_called' in expect and observed.get('debug', {}).get('llm_called') != expect['debug_llm_called']:
        failures.append('debug model-call flag differs')
    if 'interaction_count_at_least' in expect and len((observed.get('interaction') or {}).get('questions', [])) < expect['interaction_count_at_least']:
        failures.append('too few simultaneous questions')
    if "candidates_include" in expect:
        if "recorded_candidate_failures" in observed:
            # Older recordings omitted SQL candidates. Preserve the original
            # candidate-only verdict; do not invent evidence or query today's DB.
            failures.extend(observed["recorded_candidate_failures"])
        else:
            for code in expect["candidates_include"]:
                if code not in observed.get("candidates", []):
                    failures.append("SQL candidate missing: " + code)
    if "product_count" in expect and len(codes) != expect["product_count"]:
        failures.append("product count differs")
    if expect.get("no_clarification") and clarification is not None:
        failures.append("unexpected clarification")
    if "suggested_replies_count" in expect and len(observed.get("suggested_replies", [])) != expect["suggested_replies_count"]:
        failures.append("suggested reply count differs")
    for suggestion in expect.get("suggestions_exclude", []):
        if suggestion in observed.get("suggested_replies", []):
            failures.append("inappropriate suggested reply: " + suggestion)
    context = trace.get("context_after") or {}
    if expect.get("cancel_cleared") and (context.get("filters") or context.get("pending_clarification")):
        failures.append("cancel retained filters or pending clarification")
    for name in expect.get("context_filter_absent", []):
        if name in context.get("filters", {}):
            failures.append("unexpected retained filter: " + name)
    terms = [t["term_key"] for t in observed["terms"]]
    for term in expect.get("terms", []):
        if term not in terms:
            failures.append(f"term {term} missing")
    if expect.get('contract_v6'):
        from scripts.acceptance_contract import verify
        failures.extend(verify(expect, observed))
    if 't10_oracle' in expect:
        failures.extend(t10_oracle().verify(expect['t10_oracle'], observed))
    if 't12_oracle' in expect:
        from scripts.t12_oracle import verify
        failures.extend(verify(expect['t12_oracle'], observed))
    if 't14_oracle' in expect:
        from scripts.t14_oracle import verify
        failures.extend(verify(expect['t14_oracle'], observed))
    return failures


def t10_oracle():
    """Load the optional offline oracle without making tests a runtime dependency."""
    import importlib.util
    name = '_acceptance_t10_oracle'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'tests/test_t10_oracle.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def score(turn, observed, queries=None):
    options = turn.get("expect_any") or [turn["expect"]]
    results = [check(o, observed, queries or [turn["query"]]) for o in options]
    best = min(results, key=len)
    return not best, best


# --- execution ----------------------------------------------------------------------------
@contextmanager
def scenario_environment():
    from backend.auth.api import require_user
    from backend.app.main import app
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    local_environment()
    connection = connect()
    transaction = connection.transaction(force_rollback=True)
    transaction.__enter__()
    user = uuid4()
    connection.execute("INSERT INTO series76.users(id,email,name,password_hash) VALUES (%s,%s,'Acceptance','unused')",
                       (user, f"acceptance-{user}@example.test"))
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[require_user] = lambda: {"id": user}

    @contextmanager
    def same_connection():
        yield connection

    try:
        from collections import deque
        with patch("backend.conversation.api.connect", same_connection), patch('backend.conversation.agent._call_times', deque()):
            yield app, connection, user
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        transaction.__exit__(None, None, None)
        connection.close()


def run_scenario(scenario, model_factory):
    if scenario.get('t10_defect'):
        scenario = t10_oracle().resolve(scenario)
    from fastapi.testclient import TestClient
    from backend.conversation import store
    turns, session = [], None
    with scenario_environment() as (app, connection, user):
        client = TestClient(app)
        for index, turn in enumerate(scenario["turns"]):
            with patch("backend.conversation.agent.create_model_client", lambda: model_factory(scenario, index)):
                started = time.perf_counter()
                body = {"query": turn["query"]} | ({"session_id": session} if session else {})
                body.update({k: turn[k] for k in ('answers', 'remove_filters', 'action') if k in turn})
                response = client.post("/api/conversation", json=body)
            elapsed = time.perf_counter() - started
            if response.status_code == 503:
                return dict(status="provider_failure", error_code=response.json().get("error_code"), turns=turns)
            if response.status_code != 200:
                return dict(status="http_error", http_status=response.status_code, turns=turns)
            payload = response.json()
            session = payload["session_id"]
            debug = store.debug_for_message(connection, payload["message_id"], user)["tool_calls"][0]
            trace = {k: debug.get(k) for k in ("name", "parameters", "raw_parameters", "validation", "renderer",
                                                 "overrides", "context_before", "context_after", "model", "model_calls")}
            observed = dict(answer=payload["answer"], products=payload["products"], terms=payload["terms"],
                            clarification=payload["clarification"], assumptions=payload["assumptions"], trace=trace,
                            suggested_replies=payload["suggested_replies"], comparison=payload["comparison"],
                            candidates=[p["base_part_number"] for p in debug.get("data", {}).get("products", [])] or debug.get("data", {}).get("candidates", []))
            observed.update({k: payload[k] for k in ('lead', 'interaction', 'suggestions', 'active_filters', 'recommendation', 'debug')})
            observed['candidate_total'] = debug.get('data', {}).get('total')
            if debug.get('name') == 'search_actuators' and observed['candidate_total'] is not None:
                from backend.catalog.models import SearchFilters
                from backend.catalog.repository import search_actuators
                filters = (debug.get('context_after') or {}).get('filters') or {}
                full = search_actuators(connection, SearchFilters.model_validate(dict(filters, limit=100, offset=0)), allow_ambiguous=True)
                observed['eligible_codes'] = [p['base_part_number'] for p in full['products']]
            passed, failures = score(turn, observed, [t["query"] for t in scenario["turns"][:index + 1]])
            turns.append(dict(query=turn["query"], passed=passed, failures=failures, elapsed_s=round(elapsed, 3),
                              answer=payload["answer"], clarification=payload["clarification"],
                              products=[p["base_part_number"] for p in payload["products"]],
                              terms=[t["term_key"] for t in payload["terms"]], assumptions=payload["assumptions"], trace=trace,
                              suggested_replies=payload["suggested_replies"], comparison=payload["comparison"],
                              candidates=observed["candidates"]))
            turns[-1].update({k: observed.get(k) for k in ('lead', 'interaction', 'suggestions', 'active_filters', 'recommendation', 'debug', 'candidate_total', 'eligible_codes')})
            turns[-1]['product_snapshots'] = payload['products']
            turns[-1]['response'] = payload
    return dict(status="passed" if all(t["passed"] for t in turns) else "failed", turns=turns)


class IdealModel:
    """Scripted 'perfect interpreter' used only by selfcheck."""

    def __init__(self, call):
        self.call = call

    def bind_tools(self, tools, **kwargs):
        return self

    def invoke(self, messages, **kwargs):
        return SimpleNamespace(tool_calls=[dict(name=self.call[0], args=self.call[1], id="ideal")],
                               usage_metadata={}, response_metadata={"model_name": "ideal"})


IDEAL = {
    "exact_operating_time": [("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "operating_time"})],
    "exact_noncanonical": [("get_actuator", {"part_numbers": ["761a0011300000/a"]})],
    "exact_unknown": [("get_actuator", {"part_numbers": ["769Z99-11300000/A"]})],
    "exact_partial": [("get_actuator", {"part_numbers": ["761A00-113"], "focus": "torque"})],
    "missing_data_na": [("get_actuator", {"part_numbers": ["761A00-11330C00/A"], "focus": "motor_power"})],
    "dc_no_frequency": [("get_actuator", {"part_numbers": ["761X30-11370000/A"], "focus": "fla"})],
    "followup_power": [("get_actuator", {"part_numbers": ["761A00-11300000/A"]}),
                       ("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "motor_power"})],
    "followup_ambiguous_it": [("get_actuator", {"part_numbers": ["761A00-11300000/A", "761B00-11300000/A"]}),
                              ("ask_clarification", {"field": "which_product"})],
    "search_basic": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "min_torque_nm": 70})],
    "search_inlb": [("search_actuators", {"service": "on_off", "supply_voltage_v": 220, "phase_count": 1, "min_torque_in_lb": 2000})],
    "search_no_match": [("search_actuators", {"service": "modulating", "supply_voltage_v": 24, "supply_current": "DC", "min_torque_nm": 500})],
    "missing_service_then_answer": [("search_actuators", {"supply_voltage_v": 110, "min_torque_nm": 100}),
                                    ("search_actuators", {"refine": True, "service": "on_off"})],
    "conflict_dc_60hz": [("search_actuators", {"supply_voltage_v": 24, "supply_current": "DC", "frequency_hz": 60}),
                         ("search_actuators", {"refine": True, "supply_current": "DC", "service": "modulating"})],
    "conflict_rate_service": [("search_actuators", {"service": "modulating", "min_cycles_per_hour": 40})],
    "informal_modulating": [("search_actuators", {"service": "modulating", "supply_voltage_v": 220, "phase_count": 1})],
    "vague_application": [("ask_clarification", {"field": "requirements"})],
    "definition_s4": [("explain_terms", {"term_keys": ["duty_cycle"]})],
    "definition_fla_lra": [("explain_terms", {"term_keys": ["fla", "lra"]})],
    "definition_absent": [("ask_clarification", {"field": "term_not_in_summary"})],
    "combined_definition_lookup": [("get_actuator", {"part_numbers": ["761B00-11300000/A"], "focus": "duty", "explain_terms": ["duty_cycle"]})],
    "frequency_needed": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "max_fla_a": 1.5})],
    "unrelated": [("ask_clarification", {"field": "unsupported"})],
    "injection_number": [("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "torque"})],
    "no_added_filters": [("search_actuators", {"enclosure": "explosionproof"})],
    "more_results": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110}), ("search_actuators", {"more": True})],
    "changed_requirement": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "min_torque_nm": 70}),
                            ("search_actuators", {"refine": True, "supply_voltage_v": 220})],
    "csa_header": [("search_actuators", {"enclosure": "weatherproof", "supply_voltage_v": 110, "csa_required": True})],
    "h_compare_three": [("get_actuator", {"part_numbers": ["761A00-11300000/A", "761B00-11300000/A", "762A00-11300000/A"], "focus": "torque"})],
    "h_lra_50": [("get_actuator", {"part_numbers": ["763A00-11330C00/A"], "focus": "lra"})],
    "h_wrong_suffix": [("get_actuator", {"part_numbers": ["761A00-11300000/B"]})],
    "h_explosion_24v": [("search_actuators", {"enclosure": "explosionproof", "supply_voltage_v": 24, "service": "modulating"})],
    "h_informal_onoff": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "min_torque_nm": 50})],
    "h_three_phase": [("search_actuators", {"supply_voltage_v": 220, "phase_count": 3, "service": "on_off", "min_torque_nm": 250})],
    "h_no_match_power": [("search_actuators", {"service": "on_off", "max_motor_power_w": 5})],
    "h_duty_threshold": [("search_actuators", {"service": "modulating", "min_duty_s4_percent": 50})],
    "h_definition_speed": [("explain_terms", {"term_keys": ["operating_speed"]})],
    "h_definition_nema": [("ask_clarification", {"field": "term_not_in_summary"})],
    "h_followup_frequency": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "max_fla_a": {"value": 1.5, "op": "lt"}}),
                             ("search_actuators", {"refine": True, "frequency_hz": 60})],
    "h_followup_second": [("get_actuator", {"part_numbers": ["761A00-11300000/A", "761B00-11300000/A"]}),
                          ("get_actuator", {"part_numbers": ["761B00-11300000/A"], "focus": "motor_power"})],
    "h_remove_constraint": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110, "min_torque_nm": 70}),
                            ("search_actuators", {"refine": True, "remove": ["min_torque_nm"]})],
    "h_spanish_lookup": [("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": "torque"})],
    "h_prompt_leak": [("ask_clarification", {"field": "unsupported"})],
    "h_24v_ac": [("search_actuators", {"supply_voltage_v": 24, "supply_current": "AC", "service": "on_off"})],
    "hd_locked_rotor": [("explain_terms", {"term_keys": ["lra"]})],
    "hd_onoff_vs_mod": [("explain_terms", {"term_keys": ["on_off", "modulating"]})],
    "hd_weatherproof": [("explain_terms", {"term_keys": ["weatherproof"]})],
    "hd_24v_acdc": [("explain_terms", {"term_keys": ["supply_24v_ac_dc"]})],
    "hd_base_part": [("explain_terms", {"term_keys": ["base_part_number"]})],
    "hd_inrush": [("explain_terms", {"term_keys": ["lra"]})],
    "hd_joke": [("ask_clarification", {"field": "unsupported"})],
    "hd_ip65": [("explain_terms", {"term_keys": ["weatherproof"]})],
    "h4_forget_voltage": [("search_actuators", {"service": "modulating", "supply_voltage_v": 220, "min_torque_nm": 100}),
                          ("search_actuators", {"remove": ["supply_voltage_v"]})],
    "h4_remove_service": [("search_actuators", {"service": "on_off", "supply_voltage_v": 110}),
                          ("search_actuators", {"remove": ["service"]})],
    "h4_hello": [("ask_clarification", {"field": "unsupported"})],
    "h4_any_recommendation": [("ask_clarification", {"field": "requirements"})],
}


IDEAL.update({'t6_manual_01': [('search_actuators', {'min_torque_nm': 70}),
                  ('get_actuator',
                   {'part_numbers': ['761A00-11300000/A'],
                    'focus': [{'field': 'torque', 'service': 'on_off'},
                              {'field': 'operating_time', 'frequency_hz': 60}]})],
 't6_manual_02': [('search_actuators', {'min_torque_nm': 70}),
                  ('search_actuators',
                   {'enclosure': 'explosionproof',
                    'supply_voltage_v': 24,
                    'supply_current': 'DC',
                    'service': 'modulating',
                    'min_torque_in_lb': {'value': 1000, 'op': 'gt'}})],
 't6_manual_03': [('search_actuators', {'min_torque_nm': 70}),
                  ('search_actuators',
                   {'enclosure': 'weatherproof', 'sort_by': ['fastest', 'lowest_power']})],
 't6_manual_04': [('search_actuators', {'min_torque_nm': 70}),
                  ('search_actuators',
                   {'supply_voltage_v': 110, 'min_torque_in_lb': {'value': 100000, 'op': 'gte'}})],
 't6_manual_05': [('search_actuators', {'min_torque_nm': 70}),
                  ('ask_clarification', {'field': 'decline'})],
 't6_manual_06': [('search_actuators', {'min_torque_nm': 70}),
                  ('ask_clarification', {'field': 'cancel'})],
 't6_manual_07': [('search_actuators', {'min_torque_nm': 70}),
                  ('ask_clarification', {'field': 'unsupported', 'cancel_previous': True})],
 't6_manual_08': [('search_actuators', {'min_torque_nm': 70}),
                  ('search_actuators',
                   {'supply_voltage_v': 110,
                    'min_torque_in_lb': {'value': 100000, 'op': 'gt'},
                    'cancel_previous': True})]})


IDEAL["h_no_match_power"] = [("search_actuators", {"service": "on_off", "max_motor_power_w": {"value": 5, "op": "lt"}})]


def manifest(cases_path=CASES):
    files = {path: sha(path) for path in FROZEN_FILES}
    rel = str(Path(cases_path).resolve().relative_to(ROOT)).replace("\\", "/")
    files[rel] = sha(rel)
    return files


def command_selfcheck(cases, evidence_path=None):
    bad = []
    evidence = []
    selected = {'EC05','EC10','EC15','EC20','EC25','EC30','EC35','EC40','h_compare_three','h4_hello','t6_manual_04',
                'T8_recommendation','T8_fast_compare','T8_mining', 'heldout_P5-01', 'heldout_P2-03',
                'heldout_B-FRUSTRATION-01', 'heldout_B-SHORTREF-01', 'heldout_P6-01', 'heldout_P1-03',
                'heldout_v2_Q1-03', 'heldout_v2_Q3-04', 'heldout_v2_Q4-03', 'heldout_v2_Q5-05',
                'heldout_v2_C-FRUSTRATION-01', 'heldout_v2_C-SHORTREF-02', 'heldout_v2_Q6-01',
                'heldout_v3_R1-02', 'heldout_v3_R1-03', 'heldout_v3_R5-01', 'heldout_v3_R5-05',
                'heldout_v3_R6-01', 'heldout_v3_R6-02', 'heldout_v3_R6-03',
                'heldout_v3_D-FRUSTRATION-01', 'heldout_v3_D-TOPICJUMP-01',
                'heldout_v3_D-IMPOSSIBLE-01', 'heldout_v3_D-CONFIRM-01',
                'heldout_v4_S1-05', 'heldout_v4_S1-06', 'heldout_v4_S2-06',
                'heldout_v4_S3-01', 'heldout_v4_S5-04', 'heldout_v4_S6-02',
                'heldout_v4_E-SHORTREF-01', 'heldout_v4_E-IMPOSSIBLE-01',
                'heldout_v4_E-CONFIRM-01'}
    for scenario in cases["scenarios"]:
        result = run_scenario(scenario, lambda s, i: IdealModel(s['turns'][i].get('scripted_decision') or IDEAL[s["id"]][i]))
        print(scenario["id"], result["status"], *[t["failures"] for t in result["turns"] if t["failures"]])
        if result["status"] != "passed":
            bad.append(scenario["id"])
        if scenario.get('t14_class') or scenario.get('t12_class') or scenario.get('t10_defect') or scenario['id'] in selected or scenario['id'].startswith('T9_R1_') or result['status'] != 'passed':
            evidence.append(dict(scenario=scenario['id'], **result))
    print(json.dumps(dict(selfcheck="ok" if not bad else "failed", scenarios=len(cases['scenarios']), failing=bad)))
    if evidence_path:
        Path(evidence_path).write_text(json.dumps(dict(mode='scripted; no model inference',
            scenarios=len(cases['scenarios']), failing=bad, examples=evidence), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return 1 if bad else 0


def command_probe(config):
    configure_env(config, provider_key(config))
    from backend.conversation.agent import create_model_client
    ledger = Ledger(config)
    from langchain.tools import tool

    @tool
    def ping(value: str) -> str:
        """Echo a value."""
        return value

    model = Budgeted(create_model_client(), ledger, dict(stage="probe_tool_choice_required"))
    model.bind_tools([ping], tool_choice="required")
    try:
        response = model.invoke([("human", "Call the ping tool with value 'ok'.")])
        result = dict(status="ok", tool_calls=[c["name"] for c in response.tool_calls],
                      usage=response.response_metadata.get("token_usage"), model=response.response_metadata.get("model_name"))
    except Exception as exc:
        result = dict(status="error", error=type(exc).__name__, http_status=getattr(exc, "status_code", None))
    append(OUT / "probe.jsonl", dict(result, time=time.time()))
    print(json.dumps(result, default=str))


def command_run(config, cases, only, cases_path=CASES):
    OUT.mkdir(parents=True, exist_ok=True)
    frozen_path = OUT / "frozen.json"
    current = manifest(cases_path)
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        drift = sorted(k for k in current if frozen["files"].get(k) != current[k])
        if drift:
            raise SystemExit(f"Frozen inputs changed: {drift}. Start a new cohort instead of mixing results.")
    else:
        frozen_path.write_text(json.dumps(dict(files=current, cases_version=cases["version"], frozen_at=time.time()), indent=2), encoding="utf-8")
    configure_env(config, provider_key(config))
    from backend.conversation.agent import create_model_client
    ledger = Ledger(config)
    results = read_jsonl(OUT / "results.jsonl")
    attempts = {}
    for r in results:
        attempts.setdefault(r["scenario"], []).append(r["status"])
    consecutive = 0
    for scenario in cases["scenarios"]:
        sid = scenario["id"]
        if only and sid not in only:
            continue
        history = attempts.get(sid, [])
        if any(s != "provider_failure" for s in history):
            continue  # Quality result already recorded: never re-run to improve a score.
        if len(history) > config["provider_failure_retries_per_scenario"]:
            continue
        try:
            result = run_scenario(scenario, lambda s, i: Budgeted(create_model_client(), ledger, dict(scenario=s["id"], turn=i)))
        except BudgetStop:
            print(json.dumps(dict(stopped="safety_cap", spent=ledger.spent())))
            break
        record = dict(scenario=sid, category=scenario["category"], attempt=len(history) + 1, **result, time=time.time())
        append(OUT / "results.jsonl", record)
        print(sid, result["status"], *[t["failures"] for t in result["turns"] if t["failures"]], flush=True)
        if result["status"] == "provider_failure":
            consecutive += 1
            if result.get("error_code") == "budget_exhausted" or consecutive >= config["consecutive_provider_failures_stop"]:
                print(json.dumps(dict(stopped=result.get("error_code") or "provider_failures")))
                break
        else:
            consecutive = 0
    print(json.dumps(dict(spent_conservative_usd=round(ledger.spent(), 6))))


def rescore_record(record, scenario):
    """Score recorded observations, not rerendered answers; never mutate evidence."""
    result = deepcopy(record)
    for index, turn in enumerate(result.get("turns", [])):
        expected = scenario["turns"][index]
        if turn["query"] != expected["query"]:
            raise ValueError("Recorded query differs from case; refuse rescore")
        observed = dict(turn, products=turn.get('product_snapshots', [{"base_part_number": code} for code in turn["products"]]),
                        terms=[{"term_key": key} for key in turn["terms"]])
        if "candidates" not in turn:
            observed["recorded_candidate_failures"] = [f for f in turn["failures"] if f.startswith("SQL candidate missing: ")]
        turn["passed"], turn["failures"] = score(expected, observed, [t["query"] for t in scenario["turns"][:index + 1]])
    if result["status"] in ("passed", "failed"):
        if len(result["turns"]) != len(scenario["turns"]):
            raise ValueError("Incomplete non-provider record; refuse rescore")
        result["status"] = "passed" if all(t["passed"] for t in result["turns"]) else "failed"
    return result


def command_report(config, cases):
    results = read_jsonl(OUT / "results.jsonl")
    ledger = read_jsonl(OUT / "ledger.jsonl")
    final = {}
    for r in results:
        if r["status"] != "provider_failure" or r["scenario"] not in final:
            final[r["scenario"]] = r
    recorded_counts = {status: sum(r["status"] == status for r in final.values()) for status in ("passed", "failed", "provider_failure")}
    definitions = {s["id"]: s for s in cases["scenarios"]}
    final = {name: rescore_record(record, definitions[name]) for name, record in final.items()}
    categories = {}
    for s in cases["scenarios"]:
        r = final.get(s["id"])
        status = r["status"] if r else "not_run"
        categories.setdefault(s["category"], []).append(status)
    charges, states = {}, {}
    for e in ledger:
        charges[e["id"]] = e["charged_usd"]
        states[e["id"]] = e["state"]
    turns = [t for r in final.values() for t in r.get("turns", [])]
    tokens = [e.get("usage", {}) for e in ledger if e["state"] == "settled"]
    latencies = sorted(e["latency_s"] for e in ledger if e["state"] == "settled")
    summary = dict(
        cohort=cases["version"], model=config["model"], provider=config["provider"],
        rescored=True, recorded_counts=recorded_counts,
        candidate_evidence_note="Older recordings omitted SQL candidates; only those original candidate-check verdicts are retained, other checks rescored",
        scenarios=len(cases["scenarios"]), passed=sum(r["status"] == "passed" for r in final.values()),
        failed=sum(r["status"] == "failed" for r in final.values()),
        provider_failure_only=sum(r["status"] == "provider_failure" for r in final.values()),
        not_run=len(cases["scenarios"]) - len(final),
        turns=len(turns), turns_passed=sum(t["passed"] for t in turns),
        by_category={k: dict(total=len(v), passed=v.count("passed")) for k, v in categories.items()},
        failing=[dict(scenario=r["scenario"], failures=[t["failures"] for t in r["turns"] if t["failures"]])
                 for r in final.values() if r["status"] == "failed"],
        calls=len(charges), failed_calls=sum(s == "failed" for s in states.values()),
        unsettled_reservations=sum(s == "reserved" for s in states.values()),
        conservative_charge_usd=round(sum(charges.values()), 8),
        usage_based_charge_usd=round(sum(e["charged_usd"] for e in ledger if e["state"] == "settled"), 8),
        mean_prompt_tokens=round(sum(t.get("prompt_tokens", 0) for t in tokens) / len(tokens)) if tokens else None,
        mean_completion_tokens=round(sum(t.get("completion_tokens", 0) for t in tokens) / len(tokens)) if tokens else None,
        latency_p50_s=latencies[len(latencies) // 2] if latencies else None,
        latency_p95_s=latencies[int(len(latencies) * 0.95) - 1] if len(latencies) >= 20 else None,
        safety_cap_usd=config["safety_cap_usd"], openrouter_calls=len({e["id"] for e in read_jsonl(OUT / "ledger.jsonl")}) if config["provider"] == "openrouter" else 0)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    global OUT, CONFIG
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["selfcheck", "probe", "run", "report"])
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--cohort", default="v2", help="reports/agent_acceptance/<cohort>; v1 is archived")
    parser.add_argument("--cases", default=str(CASES))
    parser.add_argument('--evidence', type=Path, help='Write selected selfcheck JSON examples (no inference)')
    args = parser.parse_args()
    OUT = ROOT / "reports/agent_acceptance" / args.cohort
    CONFIG = args.config.resolve()
    FROZEN_FILES.append(str(CONFIG.relative_to(ROOT)))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    if args.command == "selfcheck":
        return command_selfcheck(cases, args.evidence)
    if args.command == "probe":
        return command_probe(config)
    if args.command == "run":
        return command_run(config, cases, set(args.only or []), args.cases)
    return command_report(config, cases)


if __name__ == "__main__":
    raise SystemExit(main())
