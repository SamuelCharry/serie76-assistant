# Testing

[Wiki](index.md) · [English](../en/testing.md) · [Español](../es/testing.md)

What each suite proves, and what still requires real-provider acceptance.

A scripted model returns predetermined tool calls; the real tools then execute validation, SQL and rendering. That proves deterministic behavior and persistence, not language understanding. Real-provider cohorts test interpretation separately. No test command below authorizes paid inference.

- [test_reviewed_catalog.py](../../../tests/test_reviewed_catalog.py): Evaluation-only manual reference and exact correction fixtures.
- [test_dynamic_geometry.py](../../../tests/test_dynamic_geometry.py): Novel rows, shifts and table reconstruction.
- [test_pipeline_safety.py](../../../tests/test_pipeline_safety.py): Failure isolation, integrity, guarded reference/network access and bounded ingestion.
- [test_catalog_db.py](../../../tests/test_catalog_db.py): Real SQL filters, scoped measurements, provenance and imports.
- [test_agent_policy.py](../../../tests/test_agent_policy.py): Grounding, codes, contradictions and filter merging.
- [test_agent_scenarios.py](../../../tests/test_agent_scenarios.py): Tool execution against scripted decisions and real catalogue.
- [test_conversations.py](../../../tests/test_conversations.py): API contract, transaction rollback, snapshots and session history.
- [test_auth.py](../../../tests/test_auth.py): Hashed auth, revocation, owner isolation and Android-facing auth contract.
- [test_submission_readiness.py](../../../tests/test_submission_readiness.py): Routing require_parameters, process call guard and idempotent demo users.

## Run locally

Start Compose from the [README](../../../README.md); then create and activate a Python 3.12 environment from the repository root. Run only the block for your shell:

```sh
# macOS/Linux
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
SERIES76_TEST_DB=1 python -m unittest discover -s tests
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
python -m unittest discover -s tests
```

## PostgreSQL connection

Tests connect to Compose service `db` through host loopback `127.0.0.1:5432`, not Docker hostname `db`. The connection helper `backend.catalog.cli.local_environment()` reads the repository-root .env without printing it: PGHOST defaults to 127.0.0.1; POSTGRES_PORT → PGPORT (default 5432), POSTGRES_DB → PGDATABASE (default series76), POSTGRES_USER → PGUSER (default series76), POSTGRES_PASSWORD → PGPASSWORD. Existing process PG* values take precedence. Use the same local values that initialized the Compose volume; changing .env does not reset its password. CI supplies PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD directly in the workflow. Without SERIES76_TEST_DB=1 the database tests skip.

In the activated backend environment:

```sh
python scripts/verify_catalog_db.py
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json
```

OCR uses a second environment: follow [ingestion setup](ingestion.md#rerun), then run these commands with that OCR environment active:

```sh
python -m unittest discover -s tests -p test_dynamic_geometry.py
python -m unittest discover -s tests -p test_pipeline_safety.py
python scripts/verify_ingestion.py
```

Android (Windows; on macOS/Linux substitute `sh mobile/android/gradlew` for the .bat wrapper):

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
./mobile/android/gradlew.bat -p mobile/android connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest
```

Instrumented tests require a running emulator. The excluded live-auth helper needs its own explicit test-account setup; see [`verify_android_auth.py`](../../../scripts/verify_android_auth.py). [`verify_mobile_backend.py`](../../../scripts/verify_mobile_backend.py) exercises controlled HTTP/restart paths; neither establishes real-model understanding. Preserve the DB volume. An offline selfcheck validates expectations, not model quality.

## T7 / v6 offline acceptance

[v6 cases](../../../config/agent_acceptance_cases_v6.json) retain all 63 v5 scenarios and add the 40 EC scenarios from the [edge-case specification](../../evaluation/edge-case-suite.es.md). Historical v5 files remain unchanged; v6 records approved presentation changes and exploratory policies. Expectations use the validated CSV; scripted decisions stay out of real-model prompts.

[Backend evidence](../../../reports/submission/T7-backend.md): 202 Python tests, 2 optional OCR/geometry module skips; 103/103 selfcheck scenarios; six mutation checks; keyless rebuild and `/ready` 200. [Android evidence](../../../reports/submission/T7-android.md): 40 JVM tests and debug APK build, not device visual acceptance. These are recorded worker results, not a claim that this documentation edit reran the suites.

With PostgreSQL running and the backend Python environment active:

```sh
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json
python -m unittest discover -s tests -p test_acceptance_v6.py -v
python scripts/check_tool_schemas.py
```

The independent CSV oracle checks values, N/A, scopes, full candidate sets, units/winners and public interaction shape. Corruption tests first accept a valid result, then require failure for `gt → gte`, N/A → zero, wrong unit, dropped requirement, substituted code (even with the same numeric value), and a dropped upper range bound. This tests whether the scorer catches these specific faults; it does not prove universal detection or real-model comprehension. [Scorer](../../../scripts/acceptance_contract.py), [mutations](../../../tests/test_acceptance_v6.py), [captured examples](../../../reports/submission/T7-scenarios.json).

Before a live cohort, run the offline schema gate below; only with explicit paid-call authorization run the one-call live preflight. Freeze code/cases/catalogue/config, count every transport attempt in the ledger, and keep provider failure separate from semantic failure. The USD 1.00 v6 configuration cap is not permission to spend. Production retries are bounded by the shared deadline; the schema preflight itself never retries.

**Coordinator placeholder — do not infer a result from selfcheck:**

v6 real-model result: pending coordinator run

## Real-model evidence

[Agent cohorts v1–v4](../../evidence/agent_acceptance.md), production A+ client through Google OpenAI-compatible API, zero OpenRouter calls:

| Cohort | Passed/scenarios | Quality failures | Provider-only failures |
|---|---:|---:|---:|
| v1 | 25/27 | 2 | 0 |
| v2 | 38/43 | 2 | 3 |
| v3 | 46/51 | 3 | 2 |
| v4 | 50/55 | 1 | 4 |

Cohorts overlap: never add them as independent samples. v4 strict power-limit correction is not rechecked with a real model; four provider-error cases remained unevaluated. Initial native-Google model selection used a separate frozen development corpus and historical [model comparison](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval). It suggested Gemini 3.6 Flash on qualitative technical fidelity; it does not validate availability, pricing or routing today.

Method: freeze corpus/code/config/catalogue hashes before inference; keep expected arguments out of prompts; score tool/arguments, extra filters, SQL facts and authorized clarifications. Record token usage, latency and provider errors independently. Reserve budget before calls, retain reservations for unknown usage, use one controller. Historical cohort settings are not the T7 transport retry policy. Restore archived experiments in a separate checkout for reproduction; paid runs require explicit approval. The [A–E comparison](../../evidence/architecture_comparison.md) is inconclusive, not a ranking.

## CI

[CI workflow](../../../.github/workflows/ci.yml) provisions PostgreSQL, installs backend dev dependencies, migrates, loads catalogue/glossary and runs unittest; Android runs JVM tests on JDK 17. It does not run paid inference, full OCR inference or emulator instrumented tests. Workflow presence is implementation evidence, not proof of the latest remote CI run. This task runs local checks only.

## Tool-schema preflight before any cohort

Run `python scripts/check_tool_schemas.py` offline first. It builds the real four production tools without a database or credentials and prints compact bytes, enum values, arrays, required fields, depth, numeric range keywords and lookup object arrays. Offline guards cap enums/arrays/required/depth at the pre-T6 counts (108/6/5/7) and reject numeric ranges, nullable unions/references and object arrays in get_actuator. Byte size alone did not predict the provider's cumulative schema limit.

Only after explicit paid-call approval, run `python scripts/check_tool_schemas.py --live` with OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL and optional OPENROUTER_BASE_URL already in the process environment. It never loads .env or prints the key, provider response or exception body; it sends exactly one request with all four tools and the production system/glossary prompt, disables tracing, performs no tool/SQL execution and has no retries. A 400 or other failure exits non-zero: stop before the cohort. A successful preflight checks schema acceptance only, not conversation quality. Re-run after any tool-schema change; the compact-schema live check is pending until the coordinator runs it.

Where: [preflight script](../../../scripts/check_tool_schemas.py), [complexity/one-call tests](../../../tests/test_tool_schema_budget.py), [metadata-only readiness script](../../../scripts/check_openrouter.py).

## Where in the code

- [tests/test_agent_scenarios.py](../../../tests/test_agent_scenarios.py#L1)
- [scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L1)
- [scripts/verify_ingestion.py](../../../scripts/verify_ingestion.py#L1)

## Known limits

No automatic test establishes arbitrary-language correctness or heterogeneous OCR accuracy. Local DB tests may create scoped test records or rollback transactions. OpenRouter acceptance and the full Android → real model → SQL → Android path remain pending.
