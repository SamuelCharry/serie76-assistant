# T15 offline gate evidence — 2026-11-05

These logs and exit codes come from:

```text
.venv-model-eval\Scripts\python.exe reports/agent_acceptance/run_t14_gates.py
```

The runner uses `run_t12_no_env.py`: actual `.env` reads are blocked, provider
credentials are removed, embeddings are disabled, and PostgreSQL tests are
enabled. The existing database and validated extraction are preserved.

The runner writes to `t14_final` by default. T15 archives the final logs,
exit codes, summary and code manifest here, then restores the tracked historical
T14 outputs. Large per-turn JSON files are reproducible with the same command;
the retained logs list every selfcheck scenario and its result.

`summary.json` distinguishes the eight required gates from the separately
reported diagnostic `replay`. A nonzero replay exit is not a passed required
gate and does not prevent the runner from exiting zero when all required
gates pass. `code_manifest.json` identifies the exact tested source files;
the commit containing this directory is the T15 implementation commit.

See [the audit](../../submission/T15-aggregate-counts.md) for verdicts,
CSV evidence, final counts and remaining limits. No new inference was performed.
