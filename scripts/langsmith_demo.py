"""Send a short, real conversation to LangSmith to see how the agent works, turn by turn.

Uses the production run_agent with the experimental Google endpoint (OPENROUTER_* point to it)
and the LANGSMITH_* values from the ignored .env. Each turn appears in LangSmith as:
  serie76_turn (chain)  ->  llm_decision (ChatOpenAI, prompt + tool call)  ->  <tool> (SQL + rendering)
Runs inside a rollback-only transaction; every LLM call is reserved in the acceptance ledger.
Keys are never printed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.agent_acceptance as acceptance  # noqa: E402

TURNS = [
    "I need an on/off actuator for 110 V with at least 70 Nm",
    "what about modulating?",
    "What does S4 mean?",
    "Show me 761A00-11300000/A and how much power does it draw?",
    "I need a 24 V DC actuator that runs at 60 Hz",
]


def dotenv(name):
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def main():
    for name in ("LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LANGSMITH_ENDPOINT"):
        os.environ.setdefault(name, dotenv(name))
    if not os.environ.get("LANGSMITH_API_KEY"):
        raise SystemExit("Add LANGSMITH_API_KEY to the ignored .env first")
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = os.environ.get("LANGSMITH_PROJECT") or "serie76-assistant"
    config = json.loads((ROOT / "config/agent_acceptance.json").read_text(encoding="utf-8"))
    acceptance.OUT = ROOT / "reports/agent_acceptance/langsmith_demo"
    acceptance.configure_env(config, acceptance.google_key())
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    from backend.conversation import agent
    from langchain_core.tracers.langchain import wait_for_all_tracers
    from langsmith.run_trees import get_cached_client
    local_environment()
    ledger = acceptance.Ledger(config)
    history, context = [], {}
    with connect() as connection, connection.transaction(force_rollback=True):
        for query in TURNS:
            try:
                result = agent.run_agent(connection, query, history, context,
                                         model=acceptance.Budgeted(agent.create_model_client(), ledger, dict(stage="langsmith_demo", query=query)))
            except agent.AgentUnavailable as exc:
                print(f"{query!r}: provider {exc.code}")
                continue
            history += [dict(role="user", content=query), dict(role="assistant", content=result.answer)]
            context = result.context
            print(f"{query!r} -> {result.tool_calls[0]['name']} {result.tool_calls[0]['validation']}")
    wait_for_all_tracers()
    get_cached_client().flush()
    print(json.dumps(dict(project=os.environ["LANGSMITH_PROJECT"], spent_conservative_usd=round(ledger.spent(), 6))))


if __name__ == "__main__":
    main()
