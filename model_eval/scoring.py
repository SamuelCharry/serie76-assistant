"""Deterministic scoring independent of any model judge."""

from decimal import Decimal, InvalidOperation


def equivalent(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if a == b:
        return True
    if a is None or b is None:
        return False
    try:
        return Decimal(str(a)).is_finite() and Decimal(str(a)) == Decimal(str(b))
    except InvalidOperation:
        return False


def dotted(data, path):
    for key in path.split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def arguments_match(args, required, *, search=False):
    if not all(
        k in args and equivalent(args[k], value) for k, value in required.items()
    ):
        return False
    if search:
        for key, value in args.items():
            if key in required or key == "limit":
                continue
            default = (
                False if key == "csa_required" else (0 if key == "offset" else None)
            )
            if not equivalent(value, default):
                return False
    return True


def score(case, result):
    traces = result.tool_calls
    if len(traces) != 1:
        return dict(
            passed=False,
            exact_tool=False,
            correct_arguments=False,
            facts_ok=False,
            valid_call=False,
            reasons=["not_exactly_one_tool"],
        )
    trace = traces[0]
    name, args, data = trace["name"], trace["parameters"], trace["data"]
    exact = name == case.expected_tool
    valid = data.get("status") != "invalid_parameters"
    reasons = []
    # The actual system explicitly permits search to ask for a missing condition.
    # Do not rank models by an arbitrary tool-name preference for equivalent behavior.
    clarification_equivalent = False
    if (
        case.expected_tool == "ask_clarification"
        and name == "search_actuators"
        and valid
    ):
        field = case.expected_arguments.get("field")
        normalized = {"frequency_hz": "frequency"}
        fields = [normalized.get(f, f) for f in data.get("fields", [])]
        alternative = case.alternative_search_arguments
        clarification_equivalent = (
            data.get("status") == "needs_clarification"
            and field in fields
            and alternative is not None
            and arguments_match(args, alternative, search=True)
        )
    correct_args = exact and arguments_match(
        args, case.expected_arguments, search=name == "search_actuators"
    )
    facts = {}
    if clarification_equivalent:
        facts_ok = True
    else:
        for path, expected in case.expected_facts.items():
            try:
                actual = dotted(data, path)
                ok = equivalent(actual, expected)
            except (KeyError, IndexError, TypeError, ValueError):
                actual, ok = None, False
            facts[path] = dict(expected=expected, actual=actual, passed=ok)
        facts_ok = all(f["passed"] for f in facts.values())
    if not valid:
        reasons.append("invalid_arguments_rejected_by_backend")
    if not (exact or clarification_equivalent):
        reasons.append("wrong_tool")
    if exact and not correct_args:
        reasons.append("requirements_not_preserved")
    if not facts_ok:
        reasons.append("wrong_tool_result")
    passed = (
        valid and facts_ok and ((exact and correct_args) or clarification_equivalent)
    )
    return dict(
        passed=passed,
        exact_tool=exact,
        correct_arguments=correct_args,
        valid_call=valid,
        facts_ok=facts_ok,
        clarification_equivalent=clarification_equivalent,
        fact_checks=facts,
        reasons=reasons,
    )
