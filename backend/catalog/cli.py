"""python -m backend.catalog.cli: explicit migration, import and query commands."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import psycopg

from .db import connect, migrate, readiness
from .loader import import_catalog, set_active
from .models import SearchFilters
from .repository import export_rows, get_actuator, search_actuators


def local_environment(path=Path(".env")):
    """CLI-only .env handling. Never print secrets; existing process env wins."""
    if not path.is_file():
        return
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    mapping = {
        "PGHOST": ("PGHOST", "127.0.0.1"),
        "PGPORT": ("POSTGRES_PORT", "5432"),
        "PGDATABASE": ("POSTGRES_DB", "series76"),
        "PGUSER": ("POSTGRES_USER", "series76"),
        "PGPASSWORD": ("POSTGRES_PASSWORD", ""),
    }
    for target, (key, default) in mapping.items():
        os.environ.setdefault(target, values.get(key, default))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    commands.add_parser("status")
    load = commands.add_parser("load")
    load.add_argument("folder", type=Path)
    load.add_argument(
        "--source-pdf", type=Path, default=Path("data/raw/series_76_electric_data.pdf")
    )
    load.add_argument("--no-activate", action="store_true")
    export = commands.add_parser("export")
    export.add_argument("--out", type=Path, required=True)
    get = commands.add_parser("get")
    get.add_argument("part_number")
    search = commands.add_parser("search")
    search.add_argument("--filters", default="{}", help="JSON SearchFilters object")
    activate = commands.add_parser("activate")
    activate.add_argument("import_id", type=int)
    args = parser.parse_args()
    local_environment()
    try:
        with connect() as connection:
            if args.command == "migrate":
                migrate(connection)
                result = dict(status="migrated")
            elif args.command == "load":
                result = import_catalog(
                    connection,
                    args.folder,
                    args.source_pdf,
                    activate=not args.no_activate,
                )
            elif args.command == "status":
                result = readiness(connection)
            elif args.command == "get":
                product = get_actuator(connection, args.part_number)
                result = dict(status="ok" if product else "not_found", product=product)
            elif args.command == "search":
                result = search_actuators(
                    connection, SearchFilters.model_validate_json(args.filters)
                )
            elif args.command == "activate":
                with connection.transaction():
                    connection.execute("SELECT pg_advisory_xact_lock(760002)")
                    if not connection.execute(
                        "SELECT 1 FROM series76.entries WHERE import_id=%s LIMIT 1",
                        (args.import_id,),
                    ).fetchone():
                        raise ValueError("Import is missing or empty")
                    set_active(connection, args.import_id)
                result = dict(status="activated", import_id=args.import_id)
            else:
                rows = export_rows(connection)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                with args.out.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(
                            {
                                **row,
                                "field_status": json.dumps(
                                    row["field_status"], sort_keys=True
                                ),
                            }
                        )
                result = dict(status="exported", rows=len(rows), output=str(args.out))
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError) as exc:
        print(f"Catalogue operation rejected: {exc}", file=sys.stderr)
        return 2
    except psycopg.Error:
        print(
            "PostgreSQL operation failed; check connectivity, migrations and database constraints. No partial import was committed.",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
