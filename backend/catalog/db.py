"""Short-lived PostgreSQL connections and checksummed transactional migrations."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS = Path(__file__).parent / "migrations"


def connect():
    # libpq reads PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD. Never log DSNs.
    return psycopg.connect(
        os.environ.get("DATABASE_URL", ""),
        connect_timeout=5,
        row_factory=dict_row,
        options="-c statement_timeout=15000 -c lock_timeout=5000",
    )


def migration_files():
    return [
        (p.name, p.read_text(encoding="utf-8"))
        for p in sorted(MIGRATIONS.glob("*.sql"))
    ]


def migrate(connection):
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(760001)")
        connection.execute("CREATE SCHEMA IF NOT EXISTS series76")
        connection.execute("""CREATE TABLE IF NOT EXISTS series76.schema_migrations (
            name text PRIMARY KEY, checksum text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now())""")
        applied = {
            r["name"]: r["checksum"]
            for r in connection.execute("SELECT * FROM series76.schema_migrations")
        }
        files = migration_files()
        if set(applied) - {name for name, _ in files}:
            raise ValueError("Database contains migrations unknown to this application")
        for name, sql in files:
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            if name in applied:
                if applied[name] != checksum:
                    raise ValueError(f"Applied migration checksum mismatch: {name}")
                continue
            connection.execute(sql, prepare=False)
            connection.execute(
                "INSERT INTO series76.schema_migrations(name,checksum) VALUES (%s,%s)",
                (name, checksum),
            )


def readiness(connection):
    applied = {
        r["name"]: r["checksum"]
        for r in connection.execute(
            "SELECT name,checksum FROM series76.schema_migrations"
        )
    }
    expected = {
        name: hashlib.sha256(sql.encode()).hexdigest()
        for name, sql in migration_files()
    }
    if applied != expected:
        raise ValueError("Schema migrations are not current")
    row = connection.execute("""SELECT i.id, i.document_sha256, i.pipeline_signature,
        (SELECT count(*) FROM series76.entries e WHERE e.import_id=i.id) AS rows
        FROM series76.catalog_state c JOIN series76.imports i ON i.id=c.active_import_id""").fetchone()
    if not row or not row["rows"]:
        raise ValueError("No populated active catalogue")
    return dict(status="ready", catalog=row)
