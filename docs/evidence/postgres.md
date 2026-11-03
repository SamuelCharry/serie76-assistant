# PostgreSQL verification

The archived PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2) run passed 62 tests, loaded 68 rows and 869 numeric values, and preserved 4 source N/A rows. SQL reconstruction matched 941/941 primary checks and 272/272 context checks. The grid SHA-256 before and after restart was `f7454653c8c1562455e84b2b1e06681915f0dea18e4a140ed88da6ee4c4c116d`.

Reproduce: `python scripts/verify_catalog_db.py` with the local PostgreSQL catalogue available. See [PostgreSQL setup](../wiki/en/operations.md). This command uses an offline reference evaluator, not a model.

[Exact archived summary](data/postgres-summary.json). [Original archive](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/postgres).

Use the activated generic backend environment from [test setup](../wiki/en/testing.md#run-locally); it installs requirements-dev.txt.
