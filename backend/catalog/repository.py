"""Deterministic queries: all magnitudes come from PostgreSQL columns."""

from __future__ import annotations

from decimal import Decimal

from .loader import FREQUENCY_FIELDS, NUMERIC_FIELDS, SERVICE_FIELDS
from .models import SearchFilters, validate_part_number

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


def search_actuators(connection, filters: SearchFilters):
    version = active_import(connection)
    service_fields = (
        "min_torque_nm",
        "min_torque_in_lb",
        "min_duty_s4_percent",
        "min_cycles_per_hour",
        "min_starts_per_hour",
    )
    if filters.service is None and any(
        getattr(filters, f) is not None for f in service_fields
    ):
        return dict(
            status="needs_clarification",
            fields=["service"],
            message="Specify on_off or modulating before comparing service performance.",
            products=[],
            total=0,
        )
    service = filters.service or "on_off"
    joins = """ LEFT JOIN series76.service_specs s ON s.entry_id=e.id AND s.service=%s
        LEFT JOIN series76.service_specs sh ON sh.entry_id=e.id AND sh.service='shared' AND t.shared_services_confirmed"""
    params = [service, version]
    conditions = ["e.import_id=%s", "e.data_status='reported'"]
    for field in ("enclosure", "supply_voltage_v", "phase_count"):
        value = getattr(filters, field)
        if value is not None:
            conditions.append(f"e.{field}=%s")
            params.append(value)
    if filters.supply_current:
        if filters.supply_current in ("AC", "DC"):
            conditions.append("e.supply_current IN (%s,'AC/DC')")
        else:
            conditions.append("e.supply_current=%s")
        params.append(filters.supply_current)
    if filters.service:
        conditions.append(
            "(t.layout IN ('mixed',%s) OR (t.layout='shared' AND t.shared_services_confirmed))"
        )
        params.append(service)
    if filters.csa_required:
        conditions.append("e.csa_status='reported_in_header'")
    comparisons = {
        "min_torque_nm": ("COALESCE(s.torque_nm,sh.torque_nm)", ">="),
        "min_torque_in_lb": ("COALESCE(s.torque_in_lb,sh.torque_in_lb)", ">="),
        "min_duty_s4_percent": ("COALESCE(s.duty_s4_percent,sh.duty_s4_percent)", ">="),
        "min_cycles_per_hour": ("s.cycles_per_hour", ">="),
        "min_starts_per_hour": ("s.starts_per_hour", ">="),
        "max_motor_power_w": ("e.motor_power_w", "<="),
    }
    for name, (expression, op) in comparisons.items():
        value = getattr(filters, name)
        if value is not None:
            conditions.append(f"{expression}{op}%s")
            params.append(value)
    frequency_filters = {
        name: getattr(filters, name)
        for name in ("max_operating_time_s", "max_fla_a", "max_lra_a")
        if getattr(filters, name) is not None
    }
    base = BASE_SELECT + joins + " WHERE " + " AND ".join(conditions)
    if filters.frequency_hz is None and frequency_filters:
        columns = [name.removeprefix("max_") for name in frequency_filters]
        distinct = " OR ".join(f"count(DISTINCT f.{c})>1" for c in columns)
        ambiguous = connection.execute(
            "SELECT EXISTS(SELECT 1 FROM ("
            + base
            + ") candidates JOIN series76.frequency_specs f ON f.entry_id=candidates.id GROUP BY candidates.id HAVING "
            + distinct
            + ") AS ambiguous",
            params,
        ).fetchone()["ambiguous"]
        if ambiguous:
            return dict(
                status="needs_clarification",
                fields=["frequency_hz"],
                message="Specify 50 or 60 Hz; published values differ for matching candidates.",
                products=[],
                total=0,
            )
    frequency_conditions, frequency_params = [], []
    if filters.frequency_hz:
        frequency_conditions.append("f.frequency_hz=%s")
        frequency_params.append(filters.frequency_hz)
    for name, value in frequency_filters.items():
        frequency_conditions.append(f"f.{name.removeprefix('max_')}<=%s")
        frequency_params.append(value)
    if frequency_conditions:
        base += (
            " AND EXISTS(SELECT 1 FROM series76.frequency_specs f WHERE f.entry_id=e.id AND "
            + " AND ".join(frequency_conditions)
            + ")"
        )
        params += frequency_params
    # De-duplicate identical source occurrences, keeping all occurrences in exact lookup.
    unique = (
        "SELECT DISTINCT ON (base_part_number) * FROM ("
        + base
        + ") q ORDER BY base_part_number,source_page,source_table,source_row"
    )
    total = connection.execute(
        "SELECT count(*) AS total FROM (" + unique + ") q", params
    ).fetchone()["total"]
    rows = connection.execute(
        unique + " LIMIT %s OFFSET %s", [*params, filters.limit, filters.offset]
    ).fetchall()
    products = hydrate(connection, rows)
    for product in products:
        product["matched_constraints"] = json_numbers(
            filters.model_dump(exclude_none=True, exclude={"limit", "offset"})
        )
        if filters.service and product["service_layout"] == "shared":
            product["match_scope"] = "shared_as_published"
    return dict(
        status="ok",
        total=total,
        limit=filters.limit,
        offset=filters.offset,
        products=products,
    )


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
