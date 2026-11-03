"""Deterministic queries: all magnitudes come from PostgreSQL columns."""

from __future__ import annotations

from decimal import Decimal

from .loader import FREQUENCY_FIELDS, NUMERIC_FIELDS, SERVICE_FIELDS
from .models import SearchFilters, validate_part_number, bound_value, bound_operator

BASE_SELECT = """SELECT e.*, t.source_table, t.source_page, t.title, t.layout,
    t.notes, t.header, t.page_metadata, t.shared_services_confirmed,
    i.document_sha256, i.pipeline_signature
    FROM series76.entries e
    JOIN series76.source_tables t ON t.id=e.table_id
    JOIN series76.imports i ON i.id=e.import_id"""


def json_numbers(value):
    if isinstance(value, Decimal):
        result = int(value) if value == value.to_integral_value() else float(value)
        if Decimal(str(result)) != value:
            raise ValueError(
                "Database numeric cannot be represented losslessly in JSON"
            )
        return result
    if isinstance(value, dict):
        return {k: json_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_numbers(v) for v in value]
    return value


def active_import(connection):
    row = connection.execute(
        "SELECT active_import_id FROM series76.catalog_state WHERE singleton"
    ).fetchone()
    if not row:
        raise ValueError("No active catalogue")
    return row["active_import_id"]


def hydrate(connection, rows, *, include_evidence=False):
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    services = {eid: [] for eid in ids}
    frequencies = {eid: [] for eid in ids}
    evidence = {eid: [] for eid in ids}
    for r in connection.execute(
        "SELECT * FROM series76.service_specs WHERE entry_id=ANY(%s) ORDER BY service",
        (ids,),
    ):
        services[r["entry_id"]].append({k: v for k, v in r.items() if k != "entry_id"})
    for r in connection.execute(
        "SELECT * FROM series76.frequency_specs WHERE entry_id=ANY(%s) ORDER BY frequency_hz NULLS LAST",
        (ids,),
    ):
        frequencies[r["entry_id"]].append(
            {k: v for k, v in r.items() if k not in ("id", "entry_id")}
        )
    if include_evidence:
        for r in connection.execute(
            "SELECT entry_id,field,evidence FROM series76.source_cells WHERE entry_id=ANY(%s) ORDER BY field",
            (ids,),
        ):
            evidence[r["entry_id"]].append(r["evidence"])
    products = []
    for row in rows:
        eid = row["id"]
        values = dict.fromkeys(NUMERIC_FIELDS)
        values["motor_power_w"] = row["motor_power_w"]
        for spec in services[eid]:
            for field in SERVICE_FIELDS:
                values[f"{spec['service']}_{field}"] = spec[field]
            if spec["service"] == "on_off":
                values["cycles_per_hour"] = spec["cycles_per_hour"]
            if spec["service"] == "modulating":
                values["starts_per_hour"] = spec["starts_per_hour"]
        for spec in frequencies[eid]:
            q = f"{spec['frequency_hz']}hz" if spec["frequency_hz"] else "unqualified"
            for field in FREQUENCY_FIELDS:
                unit = "s" if field == "operating_time" else "a"
                values[f"{field}_{q}_{unit}"] = spec[
                    f"{field}_{unit}"
                    if field != "operating_time"
                    else "operating_time_s"
                ]
        product = {
            "base_part_number": row["base_part_number"],
            "source_part_number": row["source_part_number"],
            "enclosure": row["enclosure"],
            "supply_voltage_v": row["supply_voltage_v"],
            "supply_current": row["supply_current"],
            "phase_count": row["phase_count"],
            "data_status": row["data_status"],
            "service_layout": row["layout"],
            "measurements": values,
            "field_status": row["field_status"],
            "services": services[eid],
            "frequencies": frequencies[eid],
            "certification": {
                "header": row["certification_header_raw"],
                "csa_status": row["csa_status"],
                "footnote_marker": row["source_footnote"],
            },
            "notes": row["notes"],
            "provenance": {
                "import_id": row["import_id"],
                "source_sha256": row["document_sha256"],
                "pipeline_signature": row["pipeline_signature"],
                "page": row["source_page"],
                "table": row["source_table"],
                "row": row["source_row"],
                "title": row["title"],
                "entry_id": eid,
                "shared_services_confirmed": row["shared_services_confirmed"],
            },
        }
        if include_evidence:
            product["evidence"] = evidence[eid]
            product["source_header"] = row["header"]
        products.append(json_numbers(product))
    return products


def get_actuator(connection, part_number):
    code = validate_part_number(part_number)
    version = active_import(connection)
    rows = connection.execute(
        BASE_SELECT
        + " WHERE e.import_id=%s AND e.base_part_number=%s ORDER BY t.source_page,t.source_table,e.source_row",
        (version, code),
    ).fetchall()
    if not rows:
        return None
    products = hydrate(connection, rows, include_evidence=True)
    first = products[0]
    first["occurrences"] = [p["provenance"] for p in products]
    return first


COMPARISONS = {
    "min_torque_nm": ("COALESCE(s.torque_nm,sh.torque_nm)", "gte"),
    "min_torque_in_lb": ("COALESCE(s.torque_in_lb,sh.torque_in_lb)", "gte"),
    "min_duty_s4_percent": ("COALESCE(s.duty_s4_percent,sh.duty_s4_percent)", "gte"),
    "min_cycles_per_hour": ("s.cycles_per_hour", "gte"),
    "min_starts_per_hour": ("s.starts_per_hour", "gte"),
    "max_motor_power_w": ("e.motor_power_w", "lte"),
    "max_operating_time_s": ("f.operating_time_s", "lte"),
    "max_fla_a": ("f.fla_a", "lte"),
    "max_lra_a": ("f.lra_a", "lte"),
}
OPERATORS = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}


def _matching_sql(connection, filters):
    joins = """ LEFT JOIN series76.service_specs s ON s.entry_id=e.id
        AND (%s::text IS NULL OR s.service=%s)
        LEFT JOIN series76.service_specs sh ON sh.entry_id=e.id AND sh.service='shared' AND t.shared_services_confirmed"""
    params = [filters.service, filters.service, active_import(connection)]
    conditions = ["e.import_id=%s", "e.data_status='reported'"]
    for field in ("enclosure", "supply_voltage_v", "phase_count"):
        value = getattr(filters, field)
        if value is not None:
            conditions.append(f"e.{field}=%s")
            params.append(value)
    if filters.supply_current:
        conditions.append("e.supply_current IN (%s,'AC/DC')" if filters.supply_current in ("AC", "DC") else "e.supply_current=%s")
        params.append(filters.supply_current)
    if filters.service:
        conditions.append("(t.layout IN ('mixed',%s) OR (t.layout='shared' AND t.shared_services_confirmed))")
        params.append(filters.service)
    if filters.csa_required:
        conditions.append("e.csa_status='reported_in_header'")
    frequency_conditions, frequency_params = [], []
    if filters.frequency_hz:
        frequency_conditions.append("f.frequency_hz=%s")
        frequency_params.append(filters.frequency_hz)
    for name, (expression, default) in COMPARISONS.items():
        value = getattr(filters, name)
        if value is not None:
            condition = expression + OPERATORS[bound_operator(value, default)] + "%s"
            if expression.startswith("f."):
                frequency_conditions.append(condition)
                frequency_params.append(bound_value(value))
            else:
                conditions.append(condition)
                params.append(bound_value(value))
    if frequency_conditions:
        conditions.append("EXISTS(SELECT 1 FROM series76.frequency_specs f WHERE f.entry_id=e.id AND " + " AND ".join(frequency_conditions) + ")")
        params += frequency_params
    base = BASE_SELECT + joins + " WHERE " + " AND ".join(conditions)
    unique = "SELECT DISTINCT ON (base_part_number) * FROM (" + base + ") q ORDER BY base_part_number,source_page,source_table,source_row"
    return unique, params


def search_actuators(connection, filters: SearchFilters, *, allow_ambiguous=False):
    unique, params = _matching_sql(connection, filters)
    total = connection.execute("SELECT count(*) AS total FROM (" + unique + ") q", params).fetchone()["total"]
    # Feasibility precedes ambiguity: there is no reason to ask about an empty set.
    fields = []
    if total and not allow_ambiguous:
        if filters.service is None and any(getattr(filters, name) is not None for name in COMPARISONS if name.startswith("min_")):
            fields.append("service")
        frequency_fields = [name.removeprefix("max_") for name in ("max_operating_time_s", "max_fla_a", "max_lra_a") if getattr(filters, name) is not None]
        if filters.frequency_hz is None and frequency_fields:
            distinct = " OR ".join(f"count(DISTINCT f.{name})>1" for name in frequency_fields)
            ambiguous = connection.execute("SELECT EXISTS(SELECT 1 FROM (" + unique + ") q JOIN series76.frequency_specs f ON f.entry_id=q.id GROUP BY q.id HAVING " + distinct + ") AS ambiguous", params).fetchone()["ambiguous"]
            if ambiguous:
                fields.append("frequency_hz")
    if fields:
        return dict(status="needs_clarification", fields=fields, message="Specify service or frequency for matching candidates.", products=[], total=total)
    # Explicit preferences use published extrema when no frequency/service was requested.
    orders = []
    rank_params = []
    for preference in filters.sort_by:
        if preference == "lowest_power":
            expression = "q.motor_power_w ASC NULLS LAST"
        elif preference == "highest_torque":
            expression = "(SELECT max(s.torque_nm) FROM series76.service_specs s WHERE s.entry_id=q.id AND (%s::text IS NULL OR s.service=%s OR s.service='shared')) DESC NULLS LAST"
            rank_params += [filters.service, filters.service]
        else:
            column = "operating_time_s" if preference == "fastest" else "fla_a"
            expression = f"(SELECT min(f.{column}) FROM series76.frequency_specs f WHERE f.entry_id=q.id AND (%s::int IS NULL OR f.frequency_hz=%s)) ASC NULLS LAST"
            rank_params += [filters.frequency_hz, filters.frequency_hz]
        orders.append(expression)
    ordered = "SELECT * FROM (" + unique + ") q ORDER BY " + ",".join([*orders, "q.base_part_number"])
    rows = connection.execute(ordered + " LIMIT %s OFFSET %s", [*params, *rank_params, filters.limit, filters.offset]).fetchall()
    products = hydrate(connection, rows)
    facets = {}
    if total > 4:
        for name in ("supply_voltage_v", "enclosure", "supply_current", "phase_count"):
            groups = connection.execute(f"SELECT {name} AS value,count(*) AS n FROM (" + unique + f") q GROUP BY {name} ORDER BY {name} NULLS LAST", params).fetchall()
            # A missing phase cannot be submitted as a phase filter. Prefer a
            # fully reported, filterable facet rather than offering "None".
            if len(groups) > 1 and all(group["value"] is not None for group in groups):
                facets[name] = json_numbers(groups)
    for product in products:
        product["matched_constraints"] = json_numbers(filters.model_dump(exclude_none=True, exclude={"limit", "offset"}))
        if filters.service and product["service_layout"] == "shared":
            product["match_scope"] = "shared_as_published"
    return dict(status="ok", total=total, limit=filters.limit, offset=filters.offset, products=products, facets=facets)


def closest_numeric(connection, filters):
    """Published extrema for each failed bound under every other constraint (SQL)."""
    results = []
    for name, (expression, default) in COMPARISONS.items():
        value = getattr(filters, name)
        if value is None:
            continue
        trial = SearchFilters.model_validate(filters.model_dump(exclude={name, "sort_by"}))
        unique, params = _matching_sql(connection, trial)
        # Removing only this bound is diagnostic; do not silently relax other filters.
        frequency = " AND f.frequency_hz=%s" if filters.frequency_hz else ""
        frequency_params = [filters.frequency_hz] if frequency else []
        expr = expression.replace("e.", "q.")
        joins = """ LEFT JOIN series76.service_specs s ON s.entry_id=q.id AND (%s::text IS NULL OR s.service=%s)
            LEFT JOIN series76.service_specs sh ON sh.entry_id=q.id AND sh.service='shared' AND q.shared_services_confirmed
            LEFT JOIN series76.frequency_specs f ON f.entry_id=q.id""" + frequency
        all_params = [*params, filters.service, filters.service, *frequency_params]
        remaining = []
        # Re-apply remaining measurement predicates to the SAME outer service/frequency
        # row used for the extremum, not merely to another row of the same actuator.
        for other, (other_expression, other_default) in COMPARISONS.items():
            other_value = getattr(trial, other)
            if other_value is not None:
                remaining.append(other_expression.replace("e.", "q.") + OPERATORS[bound_operator(other_value, other_default)] + "%s")
                all_params.append(bound_value(other_value))
        values = "SELECT q.base_part_number," + expr + " AS value FROM (" + unique + ") q" + joins
        if remaining:
            values += " WHERE " + " AND ".join(remaining)
        aggregate = "max" if bound_operator(value, default) in ("gt", "gte") else "min"
        sql = "WITH bound_values AS (" + values + ") SELECT DISTINCT base_part_number,value FROM bound_values WHERE value=(SELECT " + aggregate + "(value) FROM bound_values) ORDER BY base_part_number"
        found = connection.execute(sql, all_params).fetchall()
        if found:
            results.append(dict(field=name, value=json_numbers(found[0]["value"]), models=[r["base_part_number"] for r in found]))
        else:
            results.append(dict(field=name, value=None, models=[]))
    return results


def export_rows(connection):
    """Reconstruct the OCR numeric grid exclusively from relational columns."""
    rows = connection.execute(
        BASE_SELECT
        + " WHERE e.import_id=%s ORDER BY t.source_page,t.source_table,e.source_row",
        (active_import(connection),),
    ).fetchall()
    result = []
    for product in hydrate(connection, rows):
        result.append(
            {
                **{
                    k: product[k]
                    for k in (
                        "base_part_number",
                        "source_part_number",
                        "enclosure",
                        "supply_voltage_v",
                        "supply_current",
                        "phase_count",
                        "data_status",
                        "service_layout",
                    )
                },
                **product["measurements"],
                "field_status": product["field_status"],
                "source_page": product["provenance"]["page"],
                "source_table": product["provenance"]["table"],
                "source_row": product["provenance"]["row"],
                "source_table_title": product["provenance"]["title"],
                "source_sha256": product["provenance"]["source_sha256"],
                "certification_header_raw": product["certification"]["header"],
                "source_footnote": product["certification"]["footnote_marker"],
                "csa_status": product["certification"]["csa_status"],
            }
        )
    return result
