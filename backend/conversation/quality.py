"""Deterministic presentation policy. All products and options originate in SQL rows."""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from math import log2

from .rendering import product_lines, _num, _status_text, _search_focus
from .policy import LABELS

DEFAULT_REPLIES = ["Find an actuator for my requirements", "Explain Base Part Number", "Explain FLA"]


def normalized_focus(focus):
    if isinstance(focus, str):
        focus = [focus]
    return [dict(field=item) if isinstance(item, str) else dict(item) for item in focus]


def focus_keys(product, focus):
    keys = set()
    for spec in normalized_focus(focus):
        field, service, hz = spec["field"], spec.get("service"), spec.get("frequency_hz")
        for key in product["measurements"]:
            if field == "overview":
                keys.add(key)
            elif field == "torque" and "torque" in key or field == "duty" and "duty" in key:
                if not service or key.startswith(service + "_") or key.startswith("shared_"):
                    keys.add(key)
            elif field in ("operating_time", "fla", "lra") and key.startswith(field + "_"):
                dc_unqualified = "_unqualified_" in key and any(
                    f.get("frequency_scope") == "not_applicable" for f in product.get("frequencies", []))
                if not hz or f"_{hz}hz_" in key or dc_unqualified:
                    keys.add(key)
            elif field == "motor_power" and key == "motor_power_w":
                keys.add(key)
            elif field == "rates" and key in ("starts_per_hour", "cycles_per_hour"):
                keys.add(key)
    return keys


def focused_product(product, focus):
    result = deepcopy(product)
    keys = focus_keys(product, focus)
    result["measurements"] = {k: v for k, v in product["measurements"].items() if k in keys}
    result["field_status"] = {k: v for k, v in product["field_status"].items() if k in keys}
    return result


def render_focused(product, focus):
    focus = normalized_focus(focus)
    lines = []
    for spec in focus:
        item = focused_product(product, [spec])
        block = product_lines(item, spec["field"], spec.get("service"))
        for line in block[1:-1]:
            if line not in lines:
                lines.append(line)
    return "\n".join([product["base_part_number"], *lines, block[-1]])


def ranking_focus(sort_by, filters):
    fields = {"fastest": "operating_time", "lowest_power": "motor_power", "highest_torque": "torque", "lowest_current": "fla"}
    return [dict(field=fields[key], **({"frequency_hz": filters["frequency_hz"]} if filters.get("frequency_hz") and key in ("fastest", "lowest_current") else {}),
                 **({"service": filters["service"]} if filters.get("service") and key == "highest_torque" else {})) for key in sort_by]


def choose_split(facets):
    def entropy(rows):
        total = sum(r["n"] for r in rows)
        return -sum((r["n"] / total) * log2(r["n"] / total) for r in rows)
    return max(facets, key=lambda key: entropy(facets[key]), default=None)


def split_reply(field, value):
    if value is None:
        return "Cancel"
    return {"supply_voltage_v": lambda: f"Use {_num(value)} V", "enclosure": lambda: f"Use {value}",
            "supply_current": lambda: f"Use {value}", "phase_count": lambda: f"Use {value} phase"}[field]()


def replies(result, terms=None):
    choices = list(result.context.pop("reply_options", []))
    pending = (result.clarification or {}).get("field") or result.context.get("pending_clarification")
    cancelled = result.answer.startswith("Cancelled")
    if pending:
        choices += {"service": ["On/Off service", "Modulating service", "Explain On/Off service"],
                    "frequency": ["Use 50 Hz", "Use 60 Hz"],
                    "part_number": (result.clarification or {}).get("options", [])}.get(pending, [])
    codes = result.context.get("part_numbers") or []
    if len(codes) >= 2:
        choices += [f"Compare {a} vs {b}" for a, b in combinations(codes, 2)]
    elif codes:
        choices += [f"Show all specifications for {codes[0]}", f"What is the motor power of {codes[0]}?"]
    if result.context.get("pagination", {}).get("has_more") and not result.clarification:
        choices.append("Show more")
    if pending and not cancelled:
        choices.append("Cancel")
    available = {term["term_key"] for term in terms} if terms is not None else {"base_part_number", "fla"}
    choices.append(DEFAULT_REPLIES[0])
    choices += [text for key, text in [("base_part_number", "Explain Base Part Number"), ("fla", "Explain FLA")] if key in available]
    choices += ["Look up a complete part number", "Compare two actuators"]
    # Controls are useful only when executable in the current SQL/pending state.
    choices = [choice for choice in choices if not (
        choice == "Show more" and not result.context.get("pagination", {}).get("has_more")
        or choice == "Cancel" and (not pending or cancelled)
        or choice == "Explain On/Off service" and pending != "service")]
    return list(dict.fromkeys(choices))[:3]


def impossible_replies(filters, closest):
    """Construct executable next searches from the scoped SQL extrema, not guesses."""
    from .policy import describe
    from backend.catalog.models import bound_operator
    found = [row for row in closest if row["value"] is not None]
    choices = ["Show " + found[0]["models"][0]] if found else []
    for row in found:
        trial = {key: value for key, value in filters.items() if key not in ("limit", "offset", "sort_by")}
        field = row["field"]
        default = "gte" if field.startswith("min_") else "lte"
        op = "gte" if bound_operator(filters[field], default) in ("gt", "gte") else "lte"
        trial[field] = dict(value=row["value"], op=op)
        if row.get("service"):
            trial["service"] = row["service"]
        if row.get("frequency_hz"):
            trial["frequency_hz"] = row["frequency_hz"]
        choices.append("Find actuators with " + describe(trial))
    return list(dict.fromkeys(choices))


def decline_message(field):
    detail = {"service": "the service (On/Off or modulating)", "frequency": "the frequency (50 or 60 Hz)"}.get(field)
    if detail is None and field:
        detail = "the " + LABELS.get(field, field.replace("_", " "))
    return ("No problem. Tell me " + detail + " whenever you like, or ask about a specific part number."
            if detail else "No problem. Share any requirements whenever you like, or ask about a specific part number.")


def comparison(products):
    """Differences only; 'better' uses a narrow, explicit engineering direction."""
    a, b = products
    fields = ["enclosure", "supply_voltage_v", "supply_current", "phase_count"] + list(dict.fromkeys([*a["measurements"], *b["measurements"]]))
    rows, hidden = [], 0
    for field in fields:
        av = a.get(field) if field in a else a["measurements"].get(field)
        bv = b.get(field) if field in b else b["measurements"].get(field)
        if av is None and bv is None:
            continue
        if av == bv:
            hidden += 1
            continue
        unit = " in-lb" if field.endswith("in_lb") else " Nm" if field.endswith("_nm") else " W" if field.endswith("_w") else " s" if field.endswith("_s") else " A" if field.endswith("_a") else " V" if field == "supply_voltage_v" else " %" if "percent" in field else ""
        def display(product, value):
            return _num(value) + unit if value is not None else _status_text(product["field_status"].get(field))
        better = None
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            higher = "torque" in field
            lower = field.startswith(("operating_time", "fla_", "lra_")) or field == "motor_power_w"
            if higher or lower:
                better = "a" if ((av > bv) if higher else (av < bv)) else "b"
        label = field.replace("_", " ").replace("hz", " Hz")
        rows.append(dict(field=field, label=label, a=display(a, av), b=display(b, bv), better=better))
    return dict(models=[p["base_part_number"] for p in products], rows=rows, identical_fields_hidden=hidden)


def search_presentation(raw, products, filters, notes, assumptions):
    """Return answer, shown products, optional narrowing field/options, focus."""
    from .policy import describe
    total, sort_by = raw["total"], filters.get("sort_by", [])
    prefix = "\n".join(notes)
    if assumptions:
        prefix += "\nInterpretation: " + "; ".join(f"'{a['user_phrase']}' read as {describe({a['field']: a['value']})}" for a in assumptions) + "."
    criteria = describe(filters) or "the stated preferences"
    focus = ranking_focus(sort_by, filters) if sort_by else [dict(field=_search_focus(filters), **({"service": filters["service"]} if filters.get("service") else {}))]
    if not sort_by and filters.get("frequency_hz") and focus[0]["field"] in ("operating_time", "fla", "lra"):
        focus[0]["frequency_hz"] = filters["frequency_hz"]
    if sort_by:
        labels = {"fastest": "shortest operating time", "lowest_power": "lowest motor power", "highest_torque": "highest torque", "lowest_current": "lowest FLA"}
        text = f"{total} actuators match {criteria}. Top {len(products)} ranked by " + ", then ".join(labels[key] for key in sort_by) + "."
        if "lowest_power" in sort_by:
            text += " Motor power is the published rated motor power, not total electrical consumption."
        if not filters.get("frequency_hz") and any(k in sort_by for k in ("fastest", "lowest_current")):
            text += " Ranking uses the lowest published value across frequencies; all displayed values retain their frequency."
        text += "\n\n" + "\n\n".join(render_focused(p, focus) for p in products)
        field = choose_split(raw.get("facets", {}))
        options = [split_reply(field, row["value"]) for row in raw["facets"][field]] if field else []
        text += "\nWhich " + (LABELS.get(field, field.replace("_", " ")) if field else "additional performance requirement") + " do you need?"
        return (prefix + "\n" + text).strip(), [focused_product(p, focus) for p in products], field or "requirements", options, focus
    if total > 4:
        field = choose_split(raw.get("facets", {}))
        if field:
            values = raw["facets"][field]
            options = [split_reply(field, row["value"]) for row in values]
            label = LABELS.get(field, field.replace("_", " "))
            text = f"{total} actuators meet: {criteria}. Which {label} do you need? Options: " + ", ".join(str(r["value"]) if r["value"] is not None else "not published" for r in values) + "."
            return (prefix + "\n" + text).strip(), [], field, options, focus
        return (prefix + f"\n{total} actuators meet: {criteria}. Which additional performance requirement do you need?").strip(), [], "requirements", [], focus
    text = f"{total} actuators meet: {criteria}."
    if total == 1:
        text += "\n" + render_focused(products[0], focus)
    else:
        for p in products:
            # One SQL value per row; the focus follows the user's numeric requirement.
            details = render_focused(p, focus).splitlines()
            text += "\n" + p["base_part_number"] + " — " + (details[1].strip(" •") if len(details) > 1 else p["enclosure"])
        text += "\nChoose two models to compare their differences."
    return (prefix + "\n" + text).strip(), [focused_product(p, focus) for p in products], None, [], focus


def render_impossible(filters, closest):
    from .policy import describe
    from backend.catalog.models import bound_value
    text = "No actuator in the supplied catalogue meets all of: " + describe(filters) + "."
    for row in closest:
        field = row["field"]
        others = {k: v for k, v in filters.items() if k != field}
        label = LABELS[field].removeprefix("minimum ").removeprefix("maximum ")
        if row.get("service"):
            label = {"on_off": "On/Off", "modulating": "Modulating"}[row["service"]] + " " + label
        if row.get("frequency_hz"):
            label += " at " + str(row["frequency_hz"]) + " Hz"
        elif row.get("frequency_scope"):
            label += " (DC: no mains frequency)" if row["frequency_scope"] == "not_applicable" else " (frequency not specified)"
        if row["value"] is None:
            text += "\nNo published " + label + " under the remaining constraint combination: " + (describe(others) or "the catalogue scope") + "."
        else:
            unit = "in-lb" if field.endswith("in_lb") else "Nm" if field.endswith("_nm") else "W" if field.endswith("_w") else "s" if field.endswith("_s") else "A" if field.endswith("_a") else "%" if "percent" in field else "/h"
            text += f"\nClosest published {label}: {_num(row['value'])} {unit}, held by " + ", ".join(row["models"]) + (" (shared as published)." if row.get("shared_as_published") else ".")
    if not closest:
        text += " The stated constraint combination has no model in the supplied catalogue."
    return text
