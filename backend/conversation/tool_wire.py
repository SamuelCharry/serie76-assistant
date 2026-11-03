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


def array(items, maximum):
    return {"type": "array", "items": items, "maxItems": maximum}


def obj(properties, required=()):
    result = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        result["required"] = list(required)
    return result


def schemas(term_keys):
    terms = array(enum(term_keys), 3)
    focus = obj({"field": enum(FOCUS_FIELDS), "service": enum(["on_off", "modulating"]),
                 "frequency_hz": {"type": "integer", "enum": [50, 60]}}, ["field"])
    bound = obj({"field": enum(COMPARISONS), "op": enum(["gt", "gte", "lt", "lte"]),
                 "value": {"type": "number", "minimum": 0, "maximum": 1e12}}, ["field", "op", "value"])
    assumption = obj({"field": enum(policy.FILTER_FIELDS), "user_phrase": {"type": "string", "minLength": 2, "maxLength": 80}}, ["field", "user_phrase"])
    boolean = {"type": "boolean"}
    return {
        "get_actuator": obj({"part_numbers": {**array({"type": "string", "maxLength": 40}, 4), "minItems": 1},
                             "focus": array(focus, 9), "explain_terms": terms, "cancel_previous": boolean}, ["part_numbers"]),
        "search_actuators": obj({
            "enclosure": enum(["weatherproof", "explosionproof"]),
            "supply_voltage_v": {"type": "number", "exclusiveMinimum": 0, "maximum": 1e12},
            "supply_current": enum(["AC", "DC", "AC/DC"]),
            "phase_count": {"type": "integer", "enum": [1, 3]}, "service": enum(["on_off", "modulating"]),
            "frequency_hz": {"type": "integer", "enum": [50, 60]}, "csa_required": boolean,
            "bounds": array(bound, len(COMPARISONS)),
            "sort_by": array(enum(["fastest", "lowest_power", "highest_torque", "lowest_current"]), 4),
            "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            "refine": boolean, "more": boolean, "cancel_previous": boolean,
            "remove": array(enum(policy.FILTER_FIELDS), 8), "assumptions": array(assumption, 4), "explain_terms": terms}),
        "explain_terms": obj({"term_keys": {**terms, "minItems": 1}}, ["term_keys"]),
        "ask_clarification": obj({"field": enum(["part_number", "service", "frequency", "supply", "requirements", "which_product",
                                                "term_not_in_summary", "unsupported", "cancel", "decline"]),
                                  "cancel_previous": boolean}, ["field"]),
    }


def canonical_arguments(name, raw):
    """Expand compact bounds; reject duplicates/unknown fields, never lose a filter."""
    if not isinstance(raw, dict):
        raise ValueError("Tool arguments must be an object")
    args = deepcopy(raw)
    if name == "search_actuators" and "bounds" in args:
        bounds = args.pop("bounds")
        if not isinstance(bounds, list) or len(bounds) > len(COMPARISONS):
            raise ValueError("Invalid bounds list")
        for bound in bounds:
            if not isinstance(bound, dict) or set(bound) != {"field", "op", "value"}:
                raise ValueError("Invalid bound shape")
            field = bound["field"]
            if not isinstance(field, str) or field not in COMPARISONS or field in args:
                raise ValueError("Unknown or duplicate bound field")
            args[field] = {"value": bound["value"], "op": bound["op"]}
    return args
