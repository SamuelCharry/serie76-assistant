"""python -m architecture_eval {setup,prepare,run,report}. No production writes."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import secrets
import statistics
import subprocess
import time

import psycopg
from psycopg.rows import dict_row

from backend.catalog.db import migrate, readiness
from backend.catalog.loader import import_catalog
from backend.conversation.agent import AgentUnavailable
from model_eval.google import api_key, ProviderFailure
from .cases import SCENARIOS, PILOT_IDS
from .context import ContextStore, extract_chunks
from .engine import Workflow
from .provider import Budget, BudgetStop, PaidRouter, append, canonical
from .scoring import score_turn

ROOT = Path("reports/architecture_eval")
CREDENTIALS = Path(".cache/architecture/db.json")
CONFIG = Path("config/architecture_eval.json")


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


@contextmanager
def controller_lock():
    import msvcrt
    path = Path(".cache/architecture/controller.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def connection():
    values = json.loads(CREDENTIALS.read_text())
    return psycopg.connect(host="127.0.0.1", port=5543, dbname="series76_architecture",
                          user="architecture", password=values["password"], row_factory=dict_row,
                          options="-c statement_timeout=15000 -c lock_timeout=5000")


def setup():
    if not CREDENTIALS.exists():
        save(CREDENTIALS, dict(password=secrets.token_urlsafe(32)))
    env = dict(os.environ, ARCH_EVAL_DB_PASSWORD=json.loads(CREDENTIALS.read_text())["password"])
    subprocess.run(["docker", "compose", "-f", "compose.architecture-eval.yml", "up", "-d", "--wait"], env=env, check=True)
    image = subprocess.run(["docker", "inspect", "series76-architecture-eval-db-1", "--format", "{{.Image}}"], capture_output=True, text=True, check=True).stdout.strip()
    with connection() as conn:
        migrate(conn)
        loaded = import_catalog(conn, Path("data/extracted/series76"), Path("data/raw/series_76_electric_data.pdf"))
        state = readiness(conn)
        columns = conn.execute("""SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns
            WHERE table_schema='series76' ORDER BY table_name,ordinal_position""").fetchall()
        fks = conn.execute("""SELECT conrelid::regclass::text AS child, confrelid::regclass::text AS parent,
            pg_get_constraintdef(oid) AS definition FROM pg_constraint
            WHERE contype='f' AND connamespace='series76'::regnamespace ORDER BY child,parent""").fetchall()
    save(ROOT / "database.json", dict(image=image, state=state, load=loaded, columns=columns, foreign_keys=fks,
                                     isolation=dict(port=5543, project="series76-architecture-eval")))
    print("Isolated PostgreSQL catalogue loaded on 127.0.0.1:5543")


def prepare(config, budget):
    chunks = extract_chunks("data/raw/series_76_summary.pdf")
    save(ROOT / "chunks.json", chunks)
    with connection() as conn:
        store = ContextStore(conn, budget, api_key(), ROOT)
        store.prepare(chunks)
        save(ROOT / "index.json", dict(signature=store.signature, model=config["embedding_model"],
                                       dimensions=config["embedding_dimensions"], chunks=len(chunks),
                                       price_source=config["price_source"]))
    print(canonical(dict(chunks=len(chunks), conservative_charge_usd=budget.spent())))


def freeze(config):
    paths = sorted(list(Path("architecture_eval").glob("*.py")) + list(Path("backend/catalog").glob("*.py")) +
                   [Path("backend/conversation/agent.py"), CONFIG, Path("data/raw/series_76_summary.pdf"),
                    Path("data/raw/series_76_electric_data.pdf"), Path("data/extracted/series76/catalog.csv")])
    manifest = dict(config=config, hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                    scenarios=[asdict(s) for s in SCENARIOS], index=json.loads((ROOT/"index.json").read_text()))
    target = ROOT / "frozen.json"
    if target.exists() and json.loads(target.read_text(encoding="utf-8")) != manifest:
        raise ValueError("Frozen experimental inputs changed; do not append to this cohort")
    save(target, manifest)


def run(config, budget, pilot_only=False):
    freeze(config)
    key = api_key()
    old = [json.loads(line) for line in (ROOT/"results.jsonl").read_text(encoding="utf-8").splitlines()] if (ROOT/"results.jsonl").exists() else []
    done = {(r["scenario"], r["configuration"]) for r in old}
    # One scenario at a time, rotating first configuration to reduce temporal/provider bias.
    ordered = [s for s in SCENARIOS if s.id in PILOT_IDS] + [s for s in SCENARIOS if s.id not in PILOT_IDS]
    if pilot_only:
        ordered = ordered[:len(PILOT_IDS)]
    with connection() as conn:
        store = ContextStore(conn, budget, key, ROOT)
        store.signature = json.loads((ROOT/"index.json").read_text())["signature"]
        for i, scenario in enumerate(ordered):
            variants = config["configurations"][i%5:] + config["configurations"][:i%5]
            for variant in variants:
                if (scenario.id, variant) in done:
                    continue
                budget.label = dict(stage="evaluation", scenario=scenario.id, configuration=variant)
                workflow = Workflow(conn, store, lambda: PaidRouter(budget, key))
                messages, context, turns = [], {}, []
                before, start = budget.spent(), time.perf_counter()
                failure, stopped = None, False
                for n, turn in enumerate(scenario.turns):
                    budget.label["turn"] = n
                    try:
                        result, fragments = workflow.run(variant, turn.query, messages, context)
                        scored = score_turn(turn, result, fragments)
                        turns.append(dict(query=turn.query, result=asdict(result), score=scored,
                                          retrieved=[dict(id=f["id"], page=f["page"], distance=f["distance"]) for f in fragments],
                                          steps=workflow.steps))
                        messages.extend([dict(role="user", content=turn.query), dict(role="assistant", content=result.answer)])
                        context = result.context
                    except (AgentUnavailable, ProviderFailure, BudgetStop, ValueError, KeyError) as exc:
                        # Production run_agent hides provider exceptions; the ledger retains categories.
                        events = budget.events()
                        last = events[-1] if events else {}
                        provider_failed = last.get("state") == "failed" and last.get("label", {}).get("scenario") == scenario.id and last.get("label", {}).get("configuration") == variant
                        failure = dict(type=type(exc).__name__, provider_failure=provider_failed,
                                       status=last.get("status") if provider_failed else None)
                        stopped = isinstance(exc, BudgetStop) or budget.blocked
                        break
                row = dict(scenario=scenario.id, category=scenario.category, configuration=variant,
                           turns=turns, passed=len(turns)==len(scenario.turns) and all(t["score"]["passed"] for t in turns),
                           failure=failure, budget_stopped=stopped, cost_usd=budget.spent()-before,
                           latency_s=time.perf_counter()-start)
                append(ROOT/"results.jsonl", row)
                print(canonical({k:row[k] for k in ("scenario","configuration","passed","failure","cost_usd")}), flush=True)
                if stopped or (failure and failure.get("status") in (401,402,403,404,429)):
                    return


def report(config, budget):
    rows = [json.loads(line) for line in (ROOT/"results.jsonl").read_text(encoding="utf-8").splitlines()] if (ROOT/"results.jsonl").exists() else []
    by = {v:[r for r in rows if r["configuration"]==v] for v in config["configurations"]}
    common = set.intersection(*(set(r["scenario"] for r in rr if not r["failure"] and not r["budget_stopped"]) for rr in by.values()))
    summary = {}
    for v, rr in by.items():
        usable = [r for r in rr if r["scenario"] in common and not r["failure"]]
        latencies = sorted(r["latency_s"] for r in usable)
        summary[v] = dict(attempted=len(rr), common_completed=len(usable),
                          passed=sum(r["passed"] for r in usable),
                          failures=sum(bool(r["failure"]) for r in rr),
                          mean_cost_usd=statistics.mean(r["cost_usd"] for r in usable) if usable else None,
                          median_latency_s=statistics.median(latencies) if latencies else None,
                          p95_latency_s=latencies[max(0, __import__('math').ceil(len(latencies)*0.95)-1)] if latencies else None,
                          changed_filters=sum(t["score"]["unrequested_or_changed_filters"] for r in usable for t in r["turns"]))
    complete = len(common)==len(SCENARIOS)
    recommendation = "inconclusive_partial_experiment"
    eligible = []
    if complete:
        baseline = summary["B"]
        for v in ("C","D","E"):
            s = summary[v]
            if (not s["changed_filters"] and s["passed"] >= baseline["passed"]+2 and
                s["mean_cost_usd"] <= 2*baseline["mean_cost_usd"] and s["p95_latency_s"] <= 2*baseline["p95_latency_s"]):
                eligible.append(v)
        candidates = eligible or [v for v in ("A","B") if not summary[v]["changed_filters"]]
        if candidates:
            recommendation = sorted(candidates, key=lambda v:(-summary[v]["passed"],summary[v]["mean_cost_usd"]))[0]
    data = dict(configurations=summary, common_scenarios=sorted(common), planned_scenarios=len(SCENARIOS),
                complete=complete, recommendation=recommendation, conservative_charge_usd=budget.spent(),
                cap_usd=config["budget_usd"], promoted=False, provider="Google experimental; OpenRouter pending")
    save(ROOT/"comparison.json", data)
    lines = ["# Comparación experimental de arquitecturas", "", "No se cambió el chat operativo. Google; aceptación OpenRouter pendiente.", "",
             "| Configuración | Comunes | Éxitos | Fallos proveedor/ejecución | Costo medio USD | Latencia p95 s |", "|---|---:|---:|---:|---:|---:|"]
    for v,s in summary.items():
        lines.append(f"| {v} | {s['common_completed']} | {s['passed']} | {s['failures']} | {s['mean_cost_usd']} | {s['p95_latency_s']} |")
    lines += ["", f"Resultado: **{recommendation}**. Escenarios comunes completos: {len(common)}/{len(SCENARIOS)}.",
              f"Cargo conservador del controlador: USD {budget.spent():.8f}; límite USD {config['budget_usd']:.2f}. No es una factura ni consulta de saldo.",
              "", "Se comparan únicamente escenarios completados por las cinco variantes. Las reservas de errores sin consumo conocido se conservan. No se declara superioridad estadística.", "", "## Fallos observados"]
    for r in rows:
        if not r["passed"]:
            lines.append(f"- {r['configuration']} / {r['scenario']}: " + (canonical(r["failure"]) if r["failure"] else canonical([t["score"] for t in r["turns"] if not t["score"]["passed"]])))
    (ROOT/"RESULTADOS.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(canonical(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup","prepare","run","pilot","report"))
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text())
    budget = Budget(ROOT, config)
    with controller_lock():
        if args.command == "setup": setup()
        elif args.command == "prepare": prepare(config,budget)
        elif args.command in ("run","pilot"):
            try: run(config,budget,pilot_only=args.command=="pilot")
            finally: report(config,budget)
        else: report(config,budget)


if __name__ == "__main__":
    main()
