"""Answer templates. Every magnitude comes from a SQL result; every definition is a
verbatim summary quote with its page. The LLM writes none of this text.
"""
from __future__ import annotations

from .policy import describe

UNIT = {"s": "s", "a": "A"}


def _num(value):
    return f"{value:g}" if isinstance(value, float) else str(value)


def _frequency_label(product, qualifier):
    if qualifier != "unqualified":
        return f"at {qualifier.removesuffix('hz')} Hz"
    scopes = {f.get("frequency_scope") for f in product.get("frequencies", [])}
    return "(DC: no mains frequency)" if "not_applicable" in scopes else "(frequency not specified in the source)"


def _status_text(status):
    return {"source_NA": "N/A in the source table",
            "not_in_layout": "not published in this table layout"}.get(status, "not available")


def _torque(product, service):
    m, status = product["measurements"], product["field_status"]
    layout = product.get("service_layout")
    prefix = "shared" if layout == "shared" else service
    nm, inlb = m.get(f"{prefix}_torque_nm"), m.get(f"{prefix}_torque_in_lb")
    if nm is None and inlb is None:
        return None if status.get(f"{prefix}_torque_nm") == "not_in_layout" else _status_text(status.get(f"{prefix}_torque_nm"))
    text = " / ".join(x for x in (f"{_num(inlb)} in-lb" if inlb is not None else "",
                                  f"{_num(nm)} Nm" if nm is not None else "") if x)
    return text + (" (published once for On/Off and modulating)" if layout == "shared" else "")


def product_lines(product, focus, service=None):
    m, status = product["measurements"], product["field_status"]
    code = product["base_part_number"]
    supply = f"{_num(product['supply_voltage_v'])} V {product['supply_current']}"
    if product.get("phase_count"):
        supply += f" {product['phase_count']}-phase"
    header = f"{code} — {product['enclosure']}, {supply}"
    if product["data_status"] != "reported":
        return [header + ": every performance value of this row is N/A in the source table; nothing can be inferred."]
    lines = []
    # A search for one service summarises that service only; a lookup shows both.
    services = ("shared",) if product.get("service_layout") == "shared" else ((service,) if service else ("on_off", "modulating"))

    def per_service(field, unit, label):
        for service in services:
            key = f"{service}_{field}"
            value = m.get(key)
            name = {"on_off": "On/Off", "modulating": "Modulating", "shared": "On/Off and modulating (shared)"}[service]
            if value is not None:
                lines.append(f"{label} {name}: {_num(value)}{unit}")
            elif status.get(key) == "source_NA":
                lines.append(f"{label} {name}: {_status_text('source_NA')}")

    def per_frequency(field, unit_key, label):
        for qualifier in ("50hz", "60hz", "unqualified"):
            key = f"{field}_{qualifier}_{unit_key}"
            value = m.get(key)
            if value is not None:
                lines.append(f"{label} {_frequency_label(product, qualifier)}: {_num(value)} {UNIT[unit_key]}")
            elif status.get(key) == "source_NA":
                lines.append(f"{label} {_frequency_label(product, qualifier)}: {_status_text('source_NA')}")

    if focus in ("overview", "torque"):
        for service in services:
            text = _torque(product, service)
            if text:
                name = {"on_off": "On/Off", "modulating": "Modulating", "shared": "Torque"}[service]
                lines.append(f"{name} torque: {text}" if service != "shared" else f"Torque: {text}")
    if focus in ("overview", "duty"):
        per_service("duty_s4_percent", "%", "Duty S4")
    if focus in ("overview", "rates"):
        for key, label in (("cycles_per_hour", "On/Off cycles per hour"), ("starts_per_hour", "Modulating starts per hour")):
            if m.get(key) is not None:
                lines.append(f"{label}: {_num(m[key])}")
            elif status.get(key) == "source_NA":
                lines.append(f"{label}: {_status_text('source_NA')}")
    if focus in ("overview", "operating_time"):
        per_frequency("operating_time", "s", "Operating time")
    if focus in ("overview", "fla"):
        per_frequency("fla", "a", "FLA")
    if focus in ("overview", "lra"):
        per_frequency("lra", "a", "LRA")
    if focus in ("overview", "motor_power"):
        if m.get("motor_power_w") is not None:
            lines.append(f"Motor power: {_num(m['motor_power_w'])} W")
        else:
            lines.append(f"Motor power: {_status_text(status.get('motor_power_w'))}")
    if focus == "certification":
        cert = product.get("certification", {})
        lines.append(f"Certification marks in the table header: {cert.get('header') or 'none published'}"
                     + (" (this part is marked as an exception in the source)" if cert.get("footnote_marker") else ""))
    if not lines:
        lines.append(f"The requested value is {_status_text('not_in_layout')}.")
    source = product.get("source", {})
    return [header] + ["  • " + line for line in lines] + [f"  Source: series_76_electric_data.pdf, page {source.get('page')}, table {source.get('table')}."]


def render_lookup(products, focus, missing, notes):
    blocks = list(notes)
    for product in products:
        blocks.append("\n".join(product_lines(product, focus)))
    if focus == "motor_power" and products:
        blocks.append("Motor power is the rated power of the internal motor; the catalogue does not publish total "
                      "electrical consumption. FLA/LRA describe the current drawn.")
    for code, similar in missing:
        text = f"{code} is not in the supplied Series 76 electrical catalogue."
        if similar:
            text += " Catalogue codes in the same family: " + ", ".join(similar) + " (listed for reference, not as a substitute)."
        blocks.append(text)
    return "\n\n".join(blocks)


def render_search(result, filters, notes, assumptions, supplies, relaxations):
    blocks = list(notes)
    if assumptions:
        blocks.append("Interpretation: " + "; ".join(
            f"'{a['user_phrase']}' read as {describe({a['field']: a['value']})}" for a in assumptions)
            + ". Tell me if that is not what you meant.")
    criteria = describe(filters) or "no technical constraints"
    products = result["products"]
    if not products:
        text = f"No actuator in the supplied catalogue meets all of: {criteria}."
        if relaxations:
            text += " Relaxing one requirement: " + "; ".join(f"without '{label}' there would be {count}" for label, count in relaxations) + "."
        text += " Which requirement can you relax?"
        blocks.append(text)
        return "\n\n".join(blocks)
    start = result.get("offset", 0) + 1
    blocks.append(f"{result['total']} actuators meet: {criteria}. Showing {start}–{start + len(products) - 1}; "
                  "values below are the published catalogue data.")
    focus = _search_focus(filters)
    for product in products:
        blocks.append("\n".join(product_lines(product, focus, filters.get("service"))[:-1]))
    if result["total"] > result.get("offset", 0) + len(products):
        blocks.append("Ask for more to see the next results.")
    if not filters.get("supply_voltage_v") and not filters.get("supply_current") and result["total"] > len(products):
        blocks.append("To narrow the list: which power supply is available? Published supplies: " + supplies + ".")
    return "\n\n".join(blocks)


def _search_focus(filters):
    if any(filters.get(k) is not None for k in ("max_fla_a",)):
        return "fla"
    if filters.get("max_lra_a") is not None:
        return "lra"
    if filters.get("max_operating_time_s") is not None:
        return "operating_time"
    if filters.get("max_motor_power_w") is not None:
        return "motor_power"
    if filters.get("min_duty_s4_percent") is not None:
        return "duty"
    if filters.get("min_cycles_per_hour") is not None or filters.get("min_starts_per_hour") is not None:
        return "rates"
    return "torque"


def supplies_text(rows):
    seen = []
    for row in rows:
        text = f"{_num(row['supply_voltage_v'])} V {row['supply_current']}" + (f" {row['phase_count']}-phase" if row["phase_count"] else "")
        if text not in seen:
            seen.append(text)
    return ", ".join(seen)


CATALOG_NOTE = {
    "weatherproof": "General description from the summary; whether a specific part carries a certification mark comes from its electrical-catalogue table.",
    "explosionproof": "General description from the summary; whether a specific part carries a certification mark comes from its electrical-catalogue table.",
}


def render_terms(terms, supplies):
    blocks = []
    for term in terms:
        text = f"{term['label']}: {term['definition']} [{term['document']}, p. {term['page']}]"
        if term["term_key"] in CATALOG_NOTE:
            text += "\n" + CATALOG_NOTE[term["term_key"]]
        if term["term_key"].startswith("supply_"):
            text += "\nSupplies published in the electrical catalogue: " + supplies + "."
        blocks.append(text)
    return "\n\n".join(blocks)
