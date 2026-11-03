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

Start Compose first. Create a Python 3.12 environment and install `requirements-dev.txt`; OCR needs the separate `requirements-ingest.lock.txt` environment. The commands use the existing local verification environment; on a fresh checkout create it first:

```sh
python -m venv .venv-model-eval
# macOS/Linux
.venv-model-eval/bin/python -m pip install -r requirements-dev.txt
SERIES76_TEST_DB=1 .venv-model-eval/bin/python -m unittest discover -s tests
# Windows PowerShell
.venv-model-eval/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
```
For complete local OCR checks, also follow [ingestion](ingestion.md) to install its runtime; then run its two suites and verifiers. Use `.venv-ingest/bin/python` on macOS/Linux for the following Windows paths.

```powershell
.venv-ingest/Scripts/python.exe -m unittest discover -s tests -p test_dynamic_geometry.py
.venv-ingest/Scripts/python.exe -m unittest discover -s tests -p test_pipeline_safety.py
.venv-ingest/Scripts/python.exe scripts/verify_ingestion.py
.venv-model-eval/Scripts/python.exe scripts/verify_catalog_db.py
.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v4.json
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
./mobile/android/gradlew.bat -p mobile/android connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest
```
On macOS/Linux use `sh mobile/android/gradlew` instead of the .bat wrapper. Instrumented tests require a running emulator; the excluded live auth helper requires its own backend/accounts setup. [`scripts/verify_android_auth.py`](../../../scripts/verify_android_auth.py) and [`scripts/verify_mobile_backend.py`](../../../scripts/verify_mobile_backend.py) exercise controlled HTTP/restart paths and create verification records; they do not test a real LLM. Preserve the PostgreSQL volume. Without SERIES76_TEST_DB=1, DB tests skip explicitly. An offline selfcheck validates expectations, not model quality.

## Real-model evidence

[Agent cohorts v1–v4](../../evidence/agent_acceptance.md), production A+ client through Google OpenAI-compatible API, zero OpenRouter calls:

| Cohort | Passed/scenarios | Quality failures | Provider-only failures |
|---|---:|---:|---:|
| v1 | 25/27 | 2 | 0 |
| v2 | 38/43 | 2 | 3 |
| v3 | 46/51 | 3 | 2 |
| v4 | 50/55 | 1 | 4 |

Cohorts overlap: never add them as independent samples. v4 strict power-limit correction is not rechecked with a real model; four provider-error cases remained unevaluated. Initial native-Google model selection used a separate frozen development corpus and historical [model comparison](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval). It suggested Gemini 3.6 Flash on qualitative technical fidelity; it does not validate availability, pricing or routing today.

Method: freeze corpus/code/config/catalogue hashes before inference; keep expected arguments out of prompts; score tool/arguments, extra filters, SQL facts and authorized clarifications. Record token usage, latency and provider errors independently. Reserve budget before calls, retain reservations for unknown usage, use one controller, no automatic retries. Restore archived experiments in a separate checkout for reproduction; paid runs require explicit approval. The [A–E comparison](../../evidence/architecture_comparison.md) is inconclusive, not a ranking.

## CI

[CI workflow](../../../.github/workflows/ci.yml) provisions PostgreSQL, installs backend dev dependencies, migrates, loads catalogue/glossary and runs unittest; Android runs JVM tests on JDK 17. It does not run paid inference, full OCR inference or emulator instrumented tests. Workflow presence is implementation evidence, not proof of the latest remote CI run. This task runs local checks only.

## Where in the code

- [tests/test_agent_scenarios.py](../../../tests/test_agent_scenarios.py#L1)
- [scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L1)
- [scripts/verify_ingestion.py](../../../scripts/verify_ingestion.py#L1)

## Known limits

No automatic test establishes arbitrary-language correctness or heterogeneous OCR accuracy. Local DB tests may create scoped test records or rollback transactions. OpenRouter acceptance and the full Android → real model → SQL → Android path remain pending.
