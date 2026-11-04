"""Small provider-facing schemas; canonical Pydantic validation stays server-side.

Use explicit primitive schemas instead of exporting Optional/Decimal/model unions.
The wire format and legacy internal arguments share one validated execution path.
"""
from copy import deepcopy

from . import policy
from backend.catalog.repository import COMPARISONS

FOCUS_FIELDS = ["overview", "motor_power", "torque", "operating_time", "fla", "lra", "duty", "rates", "certification"]


def enum(values):
    return {"type": "string", "enum": list(values)}


def array(items):
    return {"type": "array", "items": items}


def obj(properties, required=()):
    result = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        result["required"] = list(required)
    return result


def schemas(term_keys):
    terms = array(enum(term_keys))
    bound = obj({"field": enum(COMPARISONS), "op": enum(["gt", "gte", "lt", "lte"]),
                 "value": {"type": "number"}})
    assumption = obj({name: {"type": "string"} for name in policy.FILTER_FIELDS})
    boolean = {"type": "boolean"}
    return {
        "get_actuator": obj({"part_numbers": array({"type": "string"}),
                             "focus": array(enum(FOCUS_FIELDS)), "focus_frequency_hz": {"type": "integer", "enum": [50, 60]},
                             "focus_service": enum(["on_off", "modulating"]), "explain_terms": {"type": "string"}, "cancel_previous": boolean}, ["part_numbers"]),
        "search_actuators": obj({
            "enclosure": enum(["weatherproof", "explosionproof"]),
            "supply_voltage_v": {"type": "number"},
            "supply_current": enum(["AC", "DC", "AC/DC"]),
            "phase_count": {"type": "integer", "enum": [1, 3]}, "service": enum(["on_off", "modulating"]),
            "frequency_hz": {"type": "integer", "enum": [50, 60]}, "csa_required": boolean,
            "bounds": array(bound),
            "sort_by": array(enum(["fastest", "lowest_power", "highest_torque", "lowest_current"])),
            "limit": {"type": "integer"},
            "refine": boolean, "more": boolean, "cancel_previous": boolean,
            "remove": array(enum(policy.FILTER_FIELDS)), "assumptions": assumption, "explain_terms": {"type": "string"}}),
        "explain_terms": obj({"term_keys": terms}, ["term_keys"]),
        "ask_clarification": obj({"field": enum(["part_number", "service", "frequency", "supply", "requirements", "which_product",
                                                "term_not_in_summary", "unsupported", "cancel", "decline"]),
                                  "cancel_previous": boolean}, ["field"]),
    }


def canonical_arguments(name, raw):
    """Expand compact bounds; reject duplicates/unknown fields, never lose a filter."""
    if not isinstance(raw, dict):
        raise ValueError("Tool arguments must be an object")
    args = deepcopy(raw)
    if name == "get_actuator":
        frequency = args.pop("focus_frequency_hz", None)
        service = args.pop("focus_service", None)
        if frequency is not None or service is not None:
            focus = args.get("focus")
            if not isinstance(focus, list) or not focus or not all(isinstance(f, str) for f in focus):
                raise ValueError("Focus qualifiers require flat focus fields")
            if frequency is not None and (type(frequency) is not int or frequency not in (50, 60)):
                raise ValueError("Invalid focus frequency")
            if service is not None and service not in ("on_off", "modulating"):
                raise ValueError("Invalid focus service")
            args["focus"] = [{"field": f,
                              **({"frequency_hz": frequency} if frequency is not None and f in ("operating_time", "fla", "lra") else {}),
                              **({"service": service} if service is not None and f == "torque" else {})} for f in focus]
    if name in ("get_actuator", "search_actuators") and isinstance(args.get("explain_terms"), str):
        args["explain_terms"] = [key.strip() for key in args["explain_terms"].split(",") if key.strip()]
    if name == "search_actuators" and isinstance(args.get("assumptions"), dict):
        args["assumptions"] = [{"field": key, "user_phrase": phrase} for key, phrase in args["assumptions"].items()]
    if name == "search_actuators" and "bounds" in args:
        bounds = args.pop("bounds")
        if not isinstance(bounds, list) or len(bounds) > 2 * len(COMPARISONS):
            raise ValueError("Invalid bounds list")
        seen = set(args)
        for bound in bounds:
            if not isinstance(bound, dict) or set(bound) != {"field", "op", "value"}:
                raise ValueError("Invalid bound shape")
            field = bound["field"]
            if not isinstance(field, str) or field not in COMPARISONS or field in seen:
                raise ValueError("Unknown or duplicate bound field")
            item = {"value": bound["value"], "op": bound["op"]}
            if field in args:
                previous = args[field]
                if isinstance(previous, list) or (previous['op'] in ('gt', 'gte')) == (item['op'] in ('gt', 'gte')):
                    raise ValueError('A field allows only one lower and one upper bound')
                args[field] = [previous, item]
            else:
                args[field] = item
    return args
