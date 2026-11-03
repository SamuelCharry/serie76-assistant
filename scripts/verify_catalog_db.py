"""Verify PostgreSQL round-trip, real HTTP, restart persistence and query plans.

Run after Docker Compose startup and catalogue loading. --restart restarts only
this project's db/backend containers; it never removes containers or volumes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.catalog.cli import local_environment
from backend.catalog.db import connect, readiness
from backend.catalog.loader import NUMERIC_FIELDS, read_json
from backend.catalog.repository import export_rows


def http(base, path, body=None):
    request = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def wait_ready(base):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            status, result = http(base, "/ready")
            if status == 200:
                return result
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Backend did not become ready within 60 seconds")


def canonical_hash(rows):
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def benchmark(connection):
    """Temporary synthetic relational workload, rolled back; no production edits."""
    catalogue_lookup = connection.execute(
        """EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT e.* FROM series76.entries e
        WHERE e.import_id=(SELECT active_import_id FROM series76.catalog_state WHERE singleton)
        AND e.base_part_number=%s""",
        ("764B00-11300000/A",),
    ).fetchone()["QUERY PLAN"][0]
    with connection.transaction(force_rollback=True):
        connection.execute("""CREATE TEMP TABLE bench_entries ON COMMIT DROP AS
            SELECT g::bigint AS id, ('B'||lpad(g::text,5,'0')||'-00000000/A') AS base_part_number,
                CASE WHEN g%2=0 THEN 110 ELSE 220 END AS supply_voltage_v
            FROM generate_series(0,99999) g""")
        connection.execute("""CREATE TEMP TABLE bench_service ON COMMIT DROP AS
            SELECT g::bigint AS entry_id, 'on_off'::text AS service, (80+g%1900)::numeric AS torque_nm
            FROM generate_series(0,99999) g""")
        connection.execute("CREATE UNIQUE INDEX ON bench_entries(base_part_number)")
        connection.execute("CREATE INDEX ON bench_entries(supply_voltage_v,id)")
        connection.execute("CREATE INDEX ON bench_service(service,torque_nm,entry_id)")
        connection.execute("ANALYZE bench_entries")
        connection.execute("ANALYZE bench_service")
        exact = connection.execute(
            "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM bench_entries WHERE base_part_number=%s",
            ("B50000-00000000/A",),
        ).fetchone()["QUERY PLAN"][0]
        filtered = connection.execute(
            """EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON)
            SELECT e.base_part_number,s.torque_nm FROM bench_entries e JOIN bench_service s ON s.entry_id=e.id
            WHERE e.supply_voltage_v=%s AND s.service=%s AND s.torque_nm>=%s
            ORDER BY e.base_part_number LIMIT 20""",
            (220, "on_off", 1800),
        ).fetchone()["QUERY PLAN"][0]
        return dict(
            catalogue_lookup=catalogue_lookup,
            rows_per_table=100000,
            exact_lookup=exact,
            filtered_join=filtered,
            scope="Temporary synthetic tables and representative joins, not an OCR corpus or production load-test SLA.",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/postgres"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    local_environment()
    with connect() as connection:
        ready = readiness(connection)
        rows = export_rows(connection)
        version = connection.execute("SHOW server_version").fetchone()["server_version"]
        measurements = sum(r[f] is not None for r in rows for f in NUMERIC_FIELDS)
        plans = benchmark(connection)
    expected = read_json(ROOT / "data/extracted/series76/catalog.json")["rows"]
    assert len(rows) == len(expected) == 68
    for actual, original in zip(rows, expected):
        for field in actual:
            assert actual[field] == original[field], (actual["base_part_number"], field)
    assert measurements == 869
    csv_path = args.out / "database_catalog.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {**row, "field_status": json.dumps(row["field_status"], sort_keys=True)}
            )
    subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_ingestion.py",
            "--catalog",
            str(csv_path),
            "--reference",
            "data/reference/serie76_tablas_extraidas.csv",
            "--out",
            str(args.out / "roundtrip_evaluation.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    # Tests use savepoints/rollback and never delete the catalogue or database.
    environment = dict(os.environ, SERIES76_TEST_DB="1")
    with (args.out / "tests.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    http_checks = []
    wait_ready(args.base_url)
    for path, body, expected_status, expected_total in [
        ("/health", None, 200, None),
        ("/api/actuators/764B00-11300000/A", None, 200, None),
        ("/api/actuators/761A00", None, 422, None),
        ("/api/actuators/999Z99-99999999/A", None, 404, None),
        (
            "/api/actuators/search",
            {"supply_voltage_v": 24, "service": "on_off", "supply_current": "AC"},
            200,
            5,
        ),
        (
            "/api/actuators/search",
            {
                "service": "modulating",
                "supply_voltage_v": 220,
                "phase_count": 3,
                "min_torque_nm": 100,
            },
            200,
            7,
        ),
        ("/api/actuators/search", {"min_torque_nm": 100}, 200, 0),
        ("/api/actuators/search", {"max_operating_time_s": 20}, 200, 0),
        ("/api/actuators/search", {"unknown": 1}, 422, None),
    ]:
        status, response = http(args.base_url, path, body)
        assert status == expected_status, (path, status)
        if expected_total is not None:
            assert response["total"] == expected_total
        if body and body in ({"min_torque_nm": 100}, {"max_operating_time_s": 20}):
            assert response["status"] == "needs_clarification"
        if path.endswith("764B00-11300000/A"):
            assert response["measurements"]["on_off_torque_nm"] == 1100
        http_checks.append(
            dict(
                path=path,
                request=body,
                status=status,
                result_status=response.get("status"),
                total=response.get("total"),
            )
        )
    before = canonical_hash(rows)
    persisted = None
    if args.restart:
        subprocess.run(
            ["docker", "compose", "restart", "db", "backend"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        after_ready = wait_ready(args.base_url)
        with connect() as connection:
            after = canonical_hash(export_rows(connection))
        assert (
            after == before and after_ready["catalog"]["id"] == ready["catalog"]["id"]
        )
        persisted = dict(
            status="passed",
            catalog_sha256_before=before,
            catalog_sha256_after=after,
            active_import_id=ready["catalog"]["id"],
        )
    summary = dict(
        status="passed",
        tests_run=int(
            re.search(
                r"Ran (\d+) tests", (args.out / "tests.log").read_text(encoding="utf-8")
            ).group(1)
        ),
        postgres_version=version,
        active_catalog=ready["catalog"],
        rows=len(rows),
        numeric_values=measurements,
        source_na_rows=sum(r["data_status"] == "source_NA" for r in rows),
        http_checks=http_checks,
        restart_persistence=persisted,
        grid_sha256=before,
        reference_use="Offline evaluator only; database loader never reads manual/reference/reviewed.",
    )
    for name, data in [("summary.json", summary), ("query_plans.json", plans)]:
        (args.out / name).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
