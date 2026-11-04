"""Deterministic presentation policy. All products and options originate in SQL rows."""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from math import log2

from .rendering import product_lines, _num, _status_text, _search_focus, _frequency_label
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
    return {"supply_voltage_v": lambda: f"Use {_num(value)} V", "enclosure": lambda: f"Use {str(value).capitalize()}",
            "supply_current": lambda: f"Use {value}", "phase_count": lambda: f"Use {value} phase"}[field]()


def replies(result, terms=None):
    """Optional executable actions only; questions own their options."""
    choices = result.context.pop("reply_options", [])
    if result.interaction or result.clarification or result.comparison:
        return []
    if choices:
        return list(dict.fromkeys(choices))[:3]
    trace = result.tool_calls[0] if result.tool_calls else {}
    if trace.get("name") == "search_actuators" and 2 <= trace.get("data", {}).get("total", 0) <= 4 and len(result.products) >= 2:
        # Full SQL measurements decide the most informative pair, even if cards have a narrow focus.
        products = trace.get("data", {}).get("products") or result.products
        pair = max(combinations(products, 2), key=lambda ps: len(comparison(list(ps))["rows"]))
        return ["Compare " + pair[0]["base_part_number"] + " vs " + pair[1]["base_part_number"]]
    return []


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
    detail = {"service": "the service (On/Off or Modulating)", "frequency": "the frequency (50 or 60 Hz)"}.get(field)
    if detail is None and field:
        detail = "the " + LABELS.get(field, field.replace("_", " "))
    return ("No problem. Tell me " + detail + " whenever you like, or ask about a specific part number."
            if detail else "No problem. Share any requirements whenever you like, or ask about a specific part number.")


def comparison(products, focus=None, filters=None):
    """Human labels, grouped published units, differences only; no unit conversion."""
    a, b = products[:2]
    # (stable machine ID, visible label, published component keys/units, preference)
    specs = [("enclosure", "Enclosure", [("enclosure", "")], None),
             ("supply_voltage_v", "Supply voltage", [("supply_voltage_v", "V")], None),
             ("supply_current", "Current type", [("supply_current", "")], None),
             ("phase_count", "Phases", [("phase_count", "")], None),
             ("motor_power_w", "Motor power", [("motor_power_w", "W")], "lower")]
    for service, label in [("on_off", "On/Off"), ("modulating", "Modulating"), ("shared", "Shared")]:
        specs += [(service + "_torque", label + " torque", [(service + "_torque_in_lb", "in-lb"), (service + "_torque_nm", "Nm")], "higher"),
                  (service + "_duty_s4_percent", label + " duty S4", [(service + "_duty_s4_percent", "%")], None)]
    specs += [("cycles_per_hour", "On/Off cycles", [("cycles_per_hour", "/h")], "higher"),
              ("starts_per_hour", "Modulating starts", [("starts_per_hour", "/h")], None)]
    for qualifier in ("50hz", "60hz", "unqualified"):
        suffixes = [_frequency_label(p, qualifier) for p in products]
        suffix = suffixes[0] if len(set(suffixes)) == 1 else "(frequency scope varies)"
        for name, label, unit in [("operating_time", "Operating time", "s"), ("fla", "FLA", "A"), ("lra", "LRA", "A")]:
            key = name + "_" + qualifier + "_" + unit.lower()
            specs.append((key, label + " " + suffix, [(key, unit)], "lower"))

    def cell(product, key):
        value = product[key] if key in product else product["measurements"].get(key)
        return value, product["field_status"].get(key) if value is None else None

    def display(product, components):
        values = []
        for key, unit in components:
            value, status = cell(product, key)
            if value is not None:
                values.append(_num(value) + (" " + unit if unit else ""))
            elif status == "source_NA":
                values.append(_status_text(status) + (" (" + unit + ")" if unit else ""))
        status = cell(product, components[0][0])[1]
        text = " / ".join(values) if values else ('—' if status == 'not_in_layout' else _status_text(status))
        if ("_unqualified_" in components[0][0]
                and _frequency_label(a, "unqualified") != _frequency_label(b, "unqualified")):
            text += " " + _frequency_label(product, "unqualified")
        return text.capitalize() if key == 'enclosure' else text

    rows, hidden, missing_models = [], [], set()
    focus = normalized_focus(focus or ['overview'])
    keys = set().union(*(focus_keys(p, focus) for p in products))
    overview = any(f['field'] == 'overview' for f in focus)
    filtered_public = {name for name in (filters or {}) if name in
                       ('enclosure', 'supply_voltage_v', 'supply_current', 'phase_count')}
    for field, label, components, preference in specs:
        if not overview and field not in filtered_public and not any(key in keys for key, _ in components):
            continue
        cells = [[cell(p, key) for key, _ in components] for p in products]
        if not any(value is not None or status == 'source_NA' for values in cells for value, status in values):
            continue
        for index, values in enumerate(cells):
            if any(status == 'not_in_layout' for value, status in values):
                missing_models.add(products[index]['base_part_number'])
        row = dict(field=field, label=label, values=[display(p, components) for p in products], better=None)
        if len(products) >= 2 and len(set(row['values'])) == 1:
            hidden.append(row)
            continue
        if len(products) == 2 and preference:
            # Unknown or source N/A is never treated as zero or assigned a winner.
            if all(isinstance(v, (int, float)) for values in cells for v, status in values):
                directions = {0 if ((x > y) if preference == 'higher' else (x < y)) else 1
                              for (x, _), (y, _) in zip(cells[0], cells[1]) if x != y}
                if len(directions) == 1:
                    row['better'] = directions.pop()
        rows.append(row)
    models = [p['base_part_number'] for p in products]
    keys = []
    if len(products) > 2:
        filters = filters or {}
        requested = []
        for name in filters:
            target = {'min_torque_nm': 'torque', 'min_torque_in_lb': 'torque',
                      'max_operating_time_s': 'operating_time', 'max_fla_a': 'fla',
                      'max_lra_a': 'lra', 'max_motor_power_w': 'motor_power'}.get(name, name)
            if target in ('service', 'frequency_hz'):
                continue
            matching = [r['field'] for r in rows if r['field'] == target or target in r['field']]
            if matching and matching[0] not in requested:
                requested.append(matching[0])
        ordered = sorted(rows, key=lambda r: (-len(set(r['values'])), r['field']))
        keys = (requested + [r['field'] for r in ordered if r['field'] not in requested])[:4]
        summary = 'Compare ' + str(len(products)) + ' models using the published torque, operating time, FLA and motor power.'
        assumptions = ''
    else:
        wins = [sum(r['better'] == index for r in rows) for index in (0, 1)]
        judged = sum(wins)
        summary = (models[0] + ' wins ' + str(wins[0]) + ' of ' + str(judged) + ' differing fields with an agreed direction; '
                   + models[1] + ' wins ' + str(wins[1]) + '. This is an unweighted field count, not an overall suitability rating.')
        assumptions = 'More is better for torque and cycles; less is better for time, current and motor power.'
    return dict(layout='table' if len(products) == 2 else 'cards', models=models, summary=summary,
                assumptions=assumptions, rows=rows, hidden_rows=hidden, missing_models=sorted(missing_models), key_fields=keys,
                key_fields_reason='Fields you filtered on, then the ones that differ most' if len(products) > 2 else '')


def comparison_lead(compared):
    if compared['layout'] == 'cards':
        return compared['summary']
    descriptions = []
    for index, model in enumerate(compared['models']):
        winners = [r['label'] for r in compared['rows'] if r['better'] == index]
        if winners:
            descriptions.append(model + ' leads on ' + ', '.join(winners[:3]))
    return '; '.join(descriptions) + '.' if descriptions else 'The models have no differing published fields with an agreed direction.'


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
    if not products and total:
        message = ("That's the only model that meets these requirements. Relax one requirement to see alternatives."
                   if total == 1 else 'There are no more models under these requirements. Relax one requirement to see alternatives.')
        return message, [], None, [], focus
    if sort_by:
        labels = {"fastest": "shortest operating time", "lowest_power": "lowest motor power", "highest_torque": "highest torque", "lowest_current": "lowest FLA"}
        text = f"{total} actuators match {criteria}. Top {len(products)} ranked by " + ", then ".join(labels[key] for key in sort_by) + "."
        if "lowest_power" in sort_by:
            text += " Motor power is the published rated motor power, not total electrical consumption."
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
            text = f"{total} actuators meet: {criteria}. Which {label} do you need? Options: " + ", ".join(str(r["value"]).capitalize() if r["value"] is not None else "not published" for r in values) + "."
            return (prefix + "\n" + text).strip(), [], field, options, focus
        return (prefix + f"\n{total} actuators meet: {criteria}. Here are the leading published models.").strip(), [], None, [], focus
    text = f"{total} {'actuator meets' if total == 1 else 'actuators meet'}: {criteria}."
    if total == 1:
        text += "\n" + render_focused(products[0], focus)
    else:
        for p in products:
            # One SQL value per row; the focus follows the user's numeric requirement.
            details = render_focused(p, focus).splitlines()
            text += "\n" + p["base_part_number"] + " — " + (details[1].strip(" •") if len(details) > 1 else p["enclosure"])
        if total > 3:
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
