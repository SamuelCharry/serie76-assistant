"""Import verified OCR artifacts, never manual reference values."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from psycopg.types.json import Jsonb

from .models import validate_part_number

SERVICE_FIELDS = ("torque_in_lb", "torque_nm", "duty_s4_percent")
FREQUENCY_FIELDS = ("operating_time", "fla", "lra")
NUMERIC_FIELDS = tuple(
    [f"{s}_{f}" for s in ("on_off", "modulating", "shared") for f in SERVICE_FIELDS]
    + ["cycles_per_hour", "starts_per_hour", "motor_power_w"]
    + [
        f"{f}_{q}_{'s' if f == 'operating_time' else 'a'}"
        for q in ("60hz", "50hz", "unqualified")
        for f in FREQUENCY_FIELDS
    ]
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(
        path.read_text(encoding="utf-8-sig"),
        parse_constant=lambda _: (_ for _ in ()).throw(
            ValueError("Non-finite JSON value")
        ),
    )


def verify_bundle(folder: Path, source_pdf: Path):
    folder = folder.resolve()
    manifest = read_json(folder / "manifest.json")
    if (
        manifest.get("status") != "ready"
        or manifest.get("issues") != 0
        or manifest.get("notes_unconfirmed") != 0
        or manifest.get("values_from_ocr") is not True
        or manifest.get("reference_values_loaded") is not False
    ):
        raise ValueError("Only complete, validated OCR outputs can be imported")
    if (
        source_pdf.name != "series_76_electric_data.pdf"
        or digest(source_pdf) != manifest["source_sha256"]
    ):
        raise ValueError("Electrical source PDF does not match the OCR manifest")
    if not re.fullmatch("[0-9a-f]{64}", manifest["pipeline_signature"]):
        raise ValueError("Invalid pipeline signature")
    hashes = manifest["artifact_sha256"]
    if (
        not {"catalog.json", "catalog.csv", "cells.jsonl", "review_queue.jsonl"}
        <= hashes.keys()
    ):
        raise ValueError("Missing required artifact checksums")
    for name, checksum in hashes.items():
        file = (folder / name).resolve()
        if (
            not file.is_relative_to(folder)
            or not file.is_file()
            or digest(file) != checksum
        ):
            raise ValueError(f"Artifact integrity failed: {name}")
    if (folder / "review_queue.jsonl").stat().st_size:
        raise ValueError("Review queue is not empty")
    if (folder / "catalog.json").stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Catalogue exceeds this loader version limit (64 MiB)")
    catalog = read_json(folder / "catalog.json")
    if (
        catalog["source"]["sha256"] != manifest["source_sha256"]
        or catalog["source"]["pipeline_signature"] != manifest["pipeline_signature"]
    ):
        raise ValueError("Catalogue provenance mismatch")
    if not catalog["rows"] or len(catalog["rows"]) != manifest["rows"]:
        raise ValueError("Catalogue row count mismatch")
    fingerprint = hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return manifest, catalog, fingerprint


def validate_row(row, source_hash):
    validate_part_number(row["base_part_number"])
    if row["source_sha256"] != source_hash:
        raise ValueError("Row source does not match document")
    if row["source_part_number"] not in (
        row["base_part_number"],
        row["base_part_number"] + "*",
    ):
        raise ValueError("Source identity differs from normalized identity")
    if set(row["field_status"]) != set(NUMERIC_FIELDS):
        raise ValueError("Unsupported numeric field schema")
    for field in NUMERIC_FIELDS:
        status, value = row["field_status"][field], row.get(field)
        if status not in ("reported", "source_NA", "not_in_layout"):
            raise ValueError(f"Unsupported state: {field}")
        if (status == "reported") != (value is not None):
            raise ValueError(f"Value/state mismatch: {field}")
        if value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= 1e12
            ):
                raise ValueError(f"Invalid numeric value: {field}")
            if "duty" in field and value > 100:
                raise ValueError("Duty cycle outside 0..100")
            if field in ("cycles_per_hour", "starts_per_hour") and (
                value != int(value) or value > 2147483647
            ):
                raise ValueError("Invalid rate count")
    if row["data_status"] == "source_NA" and any(
        row.get(f) is not None for f in NUMERIC_FIELDS
    ):
        raise ValueError("N/A row contains measurements")


def row_identity(row):
    return row["source_table"], row["source_row"]


def import_catalog(connection, folder: Path, source_pdf: Path, *, activate=True):
    manifest, catalog, fingerprint = verify_bundle(folder, source_pdf)
    source_hash = manifest["source_sha256"]
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(760002)")
        existing = connection.execute(
            "SELECT id,artifact_fingerprint FROM series76.imports WHERE document_sha256=%s AND pipeline_signature=%s",
            (source_hash, manifest["pipeline_signature"]),
        ).fetchone()
        if existing:
            if existing["artifact_fingerprint"] != fingerprint:
                raise ValueError(
                    "Conflicting artifacts for an existing source/pipeline version"
                )
            if activate:
                set_active(connection, existing["id"])
            return dict(
                status="already_loaded",
                import_id=existing["id"],
                rows=manifest["rows"],
                activated=activate,
            )
        connection.execute(
            "INSERT INTO series76.documents(sha256,filename,kind) VALUES (%s,%s,'electrical') ON CONFLICT DO NOTHING",
            (source_hash, manifest["source_file"]),
        )
        import_id = connection.execute(
            """INSERT INTO series76.imports(document_sha256,pipeline_signature,artifact_fingerprint,artifact_hashes,manifest)
            VALUES (%s,%s,%s,%s,%s) RETURNING id""",
            (
                source_hash,
                manifest["pipeline_signature"],
                fingerprint,
                Jsonb(manifest["artifact_sha256"]),
                Jsonb(manifest),
            ),
        ).fetchone()["id"]
        tables = {}
        for page in catalog["pages"]:
            for table in page["tables"]:
                # Shared source values remain one measurement. Both service rate headings
                # and the explicit common-duty note are required before applying them.
                fields = {c["field"] for c in table["columns"]}
                common_note = any(
                    re.search(
                        r"duty cycle .*for on/off and modulating service",
                        n["text"],
                        re.I,
                    )
                    for n in page["notes"]
                )
                shared = (
                    table["family"] == "shared"
                    and {"cycles_per_hour", "starts_per_hour"} <= fields
                    and common_note
                )
                next_header = min(
                    (
                        t["header_bbox"][1]
                        for t in page["tables"]
                        if t["header_bbox"][1] > table["header_bbox"][1]
                    ),
                    default=float("inf"),
                )
                notes = []
                for note in page["notes"]:
                    if note["kind"] == "footnote":
                        if not table["header_bbox"][3] < note["bbox"][1] < next_header:
                            continue
                        scope = {"kind": "table", "table": table["id"]}
                    else:
                        scope = {"kind": "page", "page": page["page"]}
                    notes.append(dict(note, scope=scope))
                metadata = {
                    k: v for k, v in page.items() if k not in ("tables", "notes")
                }
                table_id = connection.execute(
                    """INSERT INTO series76.source_tables(import_id,source_table,source_page,title,layout,header,page_metadata,notes,shared_services_confirmed)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (
                        import_id,
                        table["id"],
                        page["page"],
                        table["title"],
                        table["family"],
                        Jsonb(table),
                        Jsonb(metadata),
                        Jsonb(notes),
                        bool(shared),
                    ),
                ).fetchone()["id"]
                if table["id"] in tables:
                    raise ValueError("Duplicate source table identity")
                tables[table["id"]] = (table_id, table, page)
        if len(tables) != manifest["tables"]:
            raise ValueError("Source table count mismatch")
        entries, expected_cells, observed, codes = {}, {}, {}, {}
        for row in catalog["rows"]:
            validate_row(row, source_hash)
            table_id, table, page = tables[row["source_table"]]
            published = {c["field"] for c in table["columns"]}
            if not published <= set(NUMERIC_FIELDS):
                raise ValueError("Table contains unsupported measurement fields")
            for field in NUMERIC_FIELDS:
                if (field in published) != (
                    row["field_status"][field] != "not_in_layout"
                ):
                    raise ValueError(
                        "Row field states disagree with published table layout"
                    )
            if (
                row["source_page"] != page["page"]
                or row["service_layout"] != table["family"]
            ):
                raise ValueError("Row table context mismatch")
            identity = row_identity(row)
            if identity in entries:
                raise ValueError("Repeated source row identity")
            content = {k: v for k, v in row.items() if not k.startswith("source_")}
            code = row["base_part_number"]
            if code in codes and codes[code] != content:
                raise ValueError("Conflicting duplicate part number within import")
            codes[code] = content
            eid = connection.execute(
                """INSERT INTO series76.entries(import_id,table_id,source_row,base_part_number,source_part_number,enclosure,supply_voltage_v,supply_current,phase_count,data_status,motor_power_w,field_status,certification_header_raw,source_footnote,csa_status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    import_id,
                    table_id,
                    row["source_row"],
                    code,
                    row["source_part_number"],
                    row["enclosure"],
                    row["supply_voltage_v"],
                    row["supply_current"],
                    row["phase_count"],
                    row["data_status"],
                    row["motor_power_w"],
                    Jsonb(row["field_status"]),
                    row["certification_header_raw"],
                    row["source_footnote"],
                    row["csa_status"],
                ),
            ).fetchone()["id"]
            entries[identity] = eid
            expected_cells[identity] = {
                "base_part_number": row["source_part_number"],
                **{
                    f: row[f]
                    for f in NUMERIC_FIELDS
                    if row["field_status"][f] != "not_in_layout"
                },
            }
            observed[identity] = set()
            for service in ("on_off", "modulating", "shared"):
                values = [row.get(f"{service}_{f}") for f in SERVICE_FIELDS]
                cycles = row["cycles_per_hour"] if service == "on_off" else None
                starts = row["starts_per_hour"] if service == "modulating" else None
                included = (
                    any(
                        row["field_status"][f"{service}_{f}"] != "not_in_layout"
                        for f in SERVICE_FIELDS
                    )
                    or (
                        service == "on_off"
                        and row["field_status"]["cycles_per_hour"] != "not_in_layout"
                    )
                    or (
                        service == "modulating"
                        and row["field_status"]["starts_per_hour"] != "not_in_layout"
                    )
                )
                if included:
                    connection.execute(
                        "INSERT INTO series76.service_specs(entry_id,service,torque_in_lb,torque_nm,duty_s4_percent,cycles_per_hour,starts_per_hour) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (eid, service, *values, cycles, starts),
                    )
            for qualifier, hz in (("60hz", 60), ("50hz", 50), ("unqualified", None)):
                fields = [
                    f"{f}_{qualifier}_{'s' if f == 'operating_time' else 'a'}"
                    for f in FREQUENCY_FIELDS
                ]
                if any(row["field_status"][f] != "not_in_layout" for f in fields):
                    scope = (
                        "specified"
                        if hz
                        else (
                            "not_applicable"
                            if row["supply_current"] == "DC"
                            else "not_specified"
                        )
                    )
                    connection.execute(
                        "INSERT INTO series76.frequency_specs(entry_id,frequency_hz,frequency_scope,operating_time_s,fla_a,lra_a) VALUES (%s,%s,%s,%s,%s,%s)",
                        (eid, hz, scope, *[row[f] for f in fields]),
                    )
        with (folder / "cells.jsonl").open(encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                cell = json.loads(line)
                identity = row_identity(cell)
                field = cell["field"]
                if (
                    identity not in entries
                    or field not in expected_cells[identity]
                    or field in observed[identity]
                ):
                    raise ValueError("Unexpected or repeated evidence cell")
                value = expected_cells[identity][field]
                expected_status = "reported" if value is not None else "source_NA"
                if (
                    cell.get("value") != value
                    or cell["status"] != expected_status
                    or cell["source_sha256"] != source_hash
                ):
                    raise ValueError("Evidence does not match normalized row")
                if not cell.get("bbox") or not cell.get("readings"):
                    # Explicit N/A may be represented by a merged block, not numeric readings.
                    if expected_status != "source_NA":
                        raise ValueError("Reported cell has no OCR evidence")
                connection.execute(
                    "INSERT INTO series76.source_cells(entry_id,field,status,unit,evidence) VALUES (%s,%s,%s,%s,%s)",
                    (
                        entries[identity],
                        field,
                        cell["status"],
                        cell.get("unit"),
                        Jsonb(cell),
                    ),
                )
                observed[identity].add(field)
        if any(observed[key] != set(expected_cells[key]) for key in entries):
            raise ValueError("Incomplete cell provenance")
        for table_name, (_, table, _) in tables.items():
            if sum(key[0] == table_name for key in entries) != table["row_count"]:
                raise ValueError("Table row count mismatch")
        # Detect files changed while loading before activating or committing anything.
        for name, checksum in manifest["artifact_sha256"].items():
            if digest(folder / name) != checksum:
                raise ValueError("Artifacts changed during import")
        if activate:
            set_active(connection, import_id)
        return dict(
            status="loaded", import_id=import_id, rows=len(entries), activated=activate
        )


def set_active(connection, import_id):
    connection.execute(
        """INSERT INTO series76.catalog_state(singleton,active_import_id) VALUES (true,%s)
        ON CONFLICT(singleton) DO UPDATE SET active_import_id=excluded.active_import_id""",
        (import_id,),
    )
