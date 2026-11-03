"""Real PostgreSQL integration tests, isolated by transaction rollback.

Run with SERIES76_TEST_DB=1 after migration and catalogue loading.
No test deletes the catalogue, schema, database or Docker volume.
"""

import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from backend.catalog.cli import local_environment
from backend.catalog.db import connect, migrate, readiness
from backend.catalog.loader import NUMERIC_FIELDS, digest, import_catalog, read_json
from backend.catalog.models import SearchFilters, validate_part_number
from backend.catalog.repository import (
    active_import,
    export_rows,
    get_actuator,
    search_actuators,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "data/extracted/series76"
PDF = ROOT / "data/raw/series_76_electric_data.pdf"


class QueryInputTests(unittest.TestCase):
    def test_filter_precision_and_boolean_counts_are_rejected(self):
        for query in (
            {"min_torque_nm": "1e-400"},
            {"min_cycles_per_hour": True},
            {"limit": True},
        ):
            with self.subTest(query=query), self.assertRaises(ValidationError):
                SearchFilters(**query)

    def test_complete_part_number(self):
        self.assertEqual(
            validate_part_number(" 761A00-11300000/A "), "761A00-11300000/A"
        )
        for code in (
            "761A00",
            "761A00-11300000/A*",
            "' OR 1=1 --",
            "761a00-11300000/A",
        ):
            with self.subTest(code=code), self.assertRaises(ValueError):
                validate_part_number(code)

    def test_unsupported_and_incompatible_filters(self):
        for query in (
            {"torque": 80},
            {"supply_current": "DC", "frequency_hz": 50},
            {"service": "on_off", "min_starts_per_hour": 1},
            {"service": "modulating", "min_cycles_per_hour": 1},
            {"min_cycles_per_hour": 1, "min_starts_per_hour": 1},
            {"max_fla_a": -1},
            {"max_fla_a": "NaN"},
            {"min_duty_s4_percent": 101},
            {"frequency_hz": True},
        ):
            with self.subTest(query=query), self.assertRaises(ValidationError):
                SearchFilters(**query)


@unittest.skipUnless(
    os.environ.get("SERIES76_TEST_DB") == "1",
    "Set SERIES76_TEST_DB=1 for real PostgreSQL tests",
)
class PostgresCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local_environment(ROOT / ".env")

    def setUp(self):
        self.connection = connect()
        self.transaction = self.connection.transaction(force_rollback=True)
        self.transaction.__enter__()
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.transaction.__exit__(None, None, None)
        self.connection.close()
        self.temporary.cleanup()

    def search(self, **kwargs):
        return search_actuators(self.connection, SearchFilters(**kwargs))

    def variant(self, *, remove_cell=False, conflict=False):
        """Generate test-only alternate version without ever replacing the source."""
        import shutil

        folder = Path(self.temporary.name) / "bundle"
        shutil.copytree(BUNDLE, folder)
        manifest = read_json(folder / "manifest.json")
        catalog = read_json(folder / "catalog.json")
        if not conflict:
            manifest["pipeline_signature"] = "a" * 64
            catalog["source"]["pipeline_signature"] = manifest["pipeline_signature"]
        if remove_cell:
            p = folder / "cells.jsonl"
            lines = [
                line
                for line in p.read_text(encoding="utf-8-sig").splitlines()
                if line.strip()
            ]
            p.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        (folder / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        for name in manifest["artifact_sha256"]:
            manifest["artifact_sha256"][name] = digest(folder / name)
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return folder

    def test_roundtrip_all_fields_and_evidence(self):
        actual = export_rows(self.connection)
        expected = read_json(BUNDLE / "catalog.json")["rows"]
        self.assertEqual(len(actual), 68)
        for a, e in zip(actual, expected):
            for key in a:
                self.assertEqual(a[key], e[key], (e["base_part_number"], key))
        self.assertEqual(
            sum(r[f] is not None for r in actual for f in NUMERIC_FIELDS), 869
        )
        count = self.connection.execute(
            "SELECT count(*) AS n FROM series76.source_cells WHERE entry_id IN (SELECT id FROM series76.entries WHERE import_id=%s)",
            (active_import(self.connection),),
        ).fetchone()["n"]
        self.assertEqual(
            count,
            sum(
                1 + sum(s != "not_in_layout" for s in r["field_status"].values())
                for r in expected
            ),
        )

    def test_idempotent_import(self):
        before = active_import(self.connection)
        result = import_catalog(self.connection, BUNDLE, PDF)
        self.assertEqual(result["status"], "already_loaded")
        self.assertEqual(result["import_id"], before)
        self.assertEqual(len(export_rows(self.connection)), 68)

    def test_failed_load_rolls_back_everything_and_keeps_active(self):
        before = self.connection.execute(
            "SELECT count(*) AS n FROM series76.imports"
        ).fetchone()["n"]
        active = active_import(self.connection)
        with self.assertRaisesRegex(ValueError, "Incomplete cell provenance"):
            import_catalog(self.connection, self.variant(remove_cell=True), PDF)
        self.assertEqual(active_import(self.connection), active)
        self.assertEqual(
            self.connection.execute(
                "SELECT count(*) AS n FROM series76.imports"
            ).fetchone()["n"],
            before,
        )

    def test_conflicting_same_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting artifacts"):
            import_catalog(self.connection, self.variant(conflict=True), PDF)

    def test_integrity_and_source_mismatch_rejected(self):
        folder = self.variant()
        (folder / "catalog.csv").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "Artifact integrity"):
            import_catalog(self.connection, folder, PDF)
        with self.assertRaisesRegex(ValueError, "Electrical source"):
            import_catalog(
                self.connection, BUNDLE, ROOT / "data/raw/series_76_summary.pdf"
            )

    def test_valid_version_activation_is_atomic_and_optional(self):
        before = active_import(self.connection)
        folder = self.variant()
        result = import_catalog(self.connection, folder, PDF, activate=False)
        self.assertNotEqual(result["import_id"], before)
        self.assertEqual(active_import(self.connection), before)
        again = import_catalog(self.connection, folder, PDF)
        self.assertEqual(again["status"], "already_loaded")
        self.assertEqual(active_import(self.connection), result["import_id"])
        self.assertEqual(len(export_rows(self.connection)), 68)

    def test_unit_pairs_source_na_and_missing_values(self):
        p = get_actuator(self.connection, "764B00-11300000/A")
        self.assertEqual(
            (
                p["measurements"]["on_off_torque_in_lb"],
                p["measurements"]["on_off_torque_nm"],
            ),
            (9700, 1100),
        )
        na = get_actuator(self.connection, "761A00-11330C00/A")
        self.assertEqual(na["data_status"], "source_NA")
        self.assertTrue(all(v is None for v in na["measurements"].values()))
        self.assertEqual(na["field_status"]["motor_power_w"], "source_NA")
        self.assertIsNone(get_actuator(self.connection, "999Z99-99999999/A"))

    def test_service_specific_torque(self):
        on = self.search(supply_voltage_v=110, service="on_off", min_torque_nm=70)
        mod = self.search(supply_voltage_v=110, service="modulating", min_torque_nm=70)
        code = "761A00-11300000/A"
        self.assertIn(code, [p["base_part_number"] for p in on["products"]])
        self.assertNotIn(code, [p["base_part_number"] for p in mod["products"]])

    def test_24v_supply_and_unqualified_frequency(self):
        on = self.search(supply_voltage_v=24, service="on_off", supply_current="AC")
        self.assertEqual(on["total"], 5)
        self.assertTrue(all(p["supply_current"] == "AC/DC" for p in on["products"]))
        self.assertEqual(
            self.search(supply_voltage_v=24, service="modulating", supply_current="AC")[
                "total"
            ],
            0,
        )
        dc = self.search(
            supply_voltage_v=24,
            service="modulating",
            supply_current="DC",
            max_operating_time_s=20,
        )
        self.assertEqual(dc["status"], "ok")
        self.assertEqual(dc["total"], 2)
        self.assertTrue(
            all(
                p["frequencies"][0]["frequency_scope"] == "not_applicable"
                for p in dc["products"]
            )
        )
        self.assertEqual(self.search(supply_voltage_v=24, frequency_hz=60)["total"], 0)

    def test_shared_values_are_not_duplicated(self):
        result = self.search(
            supply_voltage_v=220, phase_count=3, service="modulating", min_torque_nm=100
        )
        self.assertEqual(result["total"], 7)
        for p in result["products"]:
            self.assertEqual(p["match_scope"], "shared_as_published")
            self.assertIsNone(p["measurements"]["modulating_torque_nm"])
            self.assertIsNotNone(p["measurements"]["shared_torque_nm"])

    def test_ambiguity_returns_clarification(self):
        self.assertEqual(self.search(min_torque_nm=100)["fields"], ["service"])
        self.assertEqual(
            self.search(max_operating_time_s=20)["fields"], ["frequency_hz"]
        )
        self.assertEqual(
            self.search(max_operating_time_s=20, frequency_hz=60)["status"], "ok"
        )

    def test_csa_exception_and_note_scope(self):
        p = get_actuator(self.connection, "766A00-11320000/A")
        self.assertEqual(
            p["certification"]["csa_status"], "explicitly_not_CSA_certified"
        )
        self.assertTrue(any(n["kind"] == "footnote" for n in p["notes"]))
        p1 = get_actuator(self.connection, "761A00-11300000/A")
        self.assertFalse(any(n["kind"] == "footnote" for n in p1["notes"]))
        result = self.search(csa_required=True, limit=100)
        self.assertEqual(result["total"], 59)

    def test_pagination_stable_and_no_matches(self):
        p1 = self.search(limit=5)
        p2 = self.search(limit=5, offset=5)
        codes = [p["base_part_number"] for p in p1["products"] + p2["products"]]
        self.assertEqual(codes, sorted(set(codes)))
        self.assertEqual(
            self.search(service="on_off", min_torque_nm=999999)["total"], 0
        )

    def test_migration_checksum_is_checked(self):
        with self.connection.transaction():
            self.connection.execute(
                "UPDATE series76.schema_migrations SET checksum='modified'"
            )
            with self.assertRaisesRegex(ValueError, "checksum"):
                migrate(self.connection)
        with self.assertRaises(ValueError):
            readiness(self.connection)

    def test_failed_migration_rolls_back_ddl(self):
        import psycopg
        from backend.catalog.db import migration_files

        files = migration_files() + [
            (
                "999_test_failure.sql",
                "CREATE TABLE series76.rollback_probe(id int); SELECT * FROM series76.definitely_missing;",
            )
        ]
        with patch("backend.catalog.db.migration_files", return_value=files):
            with self.assertRaises(psycopg.errors.UndefinedTable):
                migrate(self.connection)
        self.assertIsNone(
            self.connection.execute(
                "SELECT to_regclass('series76.rollback_probe') AS name"
            ).fetchone()["name"]
        )
        self.assertEqual(readiness(self.connection)["status"], "ready")

    def test_api_contract_and_unavailable_database(self):
        from fastapi.testclient import TestClient
        from backend.app.main import app

        @contextmanager
        def current_connection():
            yield self.connection

        with (
            patch("backend.app.main.connect", current_connection),
            TestClient(app) as client,
        ):
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/ready").status_code, 200)
            response = client.get("/api/actuators/764B00-11300000/A")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["measurements"]["on_off_torque_nm"], 1100)
            self.assertEqual(
                client.get("/api/actuators/999Z99-99999999/A").status_code, 404
            )
            self.assertEqual(client.get("/api/actuators/761A00").status_code, 422)
            self.assertEqual(
                client.post("/api/actuators/search", json={"unknown": 1}).status_code,
                422,
            )
            self.assertEqual(
                client.post("/api/actuators/search", json={"min_torque_nm": 80}).json()[
                    "status"
                ],
                "needs_clarification",
            )
        import psycopg

        with (
            patch(
                "backend.app.main.connect",
                side_effect=psycopg.OperationalError("private detail"),
            ),
            TestClient(app) as client,
        ):
            self.assertEqual(client.get("/health").status_code, 200)
            response = client.get("/ready")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private detail", response.text)


if __name__ == "__main__":
    unittest.main()
