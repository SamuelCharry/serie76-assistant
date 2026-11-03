#!/bin/sh
set -eu
python -m backend.catalog.cli migrate
python -m backend.catalog.cli load data/extracted/series76
python -m backend.catalog.cli load-context
python -m backend.auth.cli ensure-demo-users
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
