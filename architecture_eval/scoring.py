"""Evaluate interpretation separately from SQL-backed numerical fidelity."""
from model_eval.scoring import arguments_match, dotted, equivalent


def score_turn(turn, result, fragments):
    traces = result.tool_calls
    trace = traces[0] if len(traces) == 1 else {}
    name, args, data = trace.get("name"), trace.get("parameters", {}), trace.get("data", {})
    exact = name == turn.tool
    correct = exact and arguments_match(args, turn.args, search=name == "search_actuators")
    equivalent_clarification = False
    if turn.alternative is not None and name == "search_actuators":
        fields = ["frequency" if f == "frequency_hz" else f for f in data.get("fields", [])]
        equivalent_clarification = (data.get("status") == "needs_clarification" and
            turn.args.get("field") in fields and arguments_match(args, turn.alternative, search=True))
    facts = {}
    for path, expected in turn.facts.items():
        try:
            actual = dotted(data, path)
            facts[path] = equivalent(actual, expected)
        except (KeyError, IndexError, TypeError):
            facts[path] = False
    evidence = data.get("evidence", [])
    context_ok = (name == "explain_context" and bool(evidence) and
                  all(word.lower() in result.answer.lower() for word in turn.keywords)) if turn.tool == "explain_context" else True
    # This is constraint fidelity, not a claim that the LLM generated the SQL numbers.
    unsafe = name == "search_actuators" and not arguments_match(args, turn.args if turn.tool == "search_actuators" else (turn.alternative or {}), search=True)
    return dict(passed=bool((correct or equivalent_clarification) and all(facts.values()) and context_ok),
                tool=name, arguments_ok=bool(correct or equivalent_clarification), facts=facts,
                context_ok=context_ok, unrequested_or_changed_filters=bool(unsafe),
                numeric_authority="deterministic_sql", cited_context_ids=[e["fragment_id"] for e in evidence])
