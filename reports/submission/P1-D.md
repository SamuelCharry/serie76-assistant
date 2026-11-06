# P1-D: dependency audit and keyless clean-clone smoke

Date: 2026-11-05. Audited source: `31f4329eb8213a216052dc71f03068459ec8e996` on `release/submission`, after `git pull` reported up to date.

## Dependency result

Removed: **none**. Every declared direct dependency has a code import or an explicit runtime requirement. Removing packages merely because their distribution name differs from their import name would break supported paths. No version changes, lock regeneration or Dockerfile changes were justified; existing exact pins remain consistent.

| Direct dependency | Decision and evidence |
|---|---|
| fastapi | Keep: API/router imports in `backend/app/main.py`, `backend/auth/api.py`, conversation API and tests. |
| uvicorn | Keep: executable server in `docker/entrypoint.sh`; no Python import is necessary. |
| pydantic | Keep: contracts, catalogue models and interpretation validation. |
| PyMuPDF | Keep in both sets: imported as `pymupdf` by `catalog_ingest/summary.py`, pipeline and `scripts/make_pipeline_fixtures.py`; tests cover the PDF paths. No backend-only import, but demonstrably used in the requested audit scope. Moving it between environments would be a separate packaging change. |
| psycopg[binary] | Keep: catalogue/auth database code; binary extra supplies libpq runtime (`psycopg-binary` lock pin). |
| langchain-core | Keep: messages, StructuredTool and RunnableLambda in agent plus schema conversion scripts/tests. |
| langchain-openai | Keep: ChatOpenAI in agent and OpenAIEmbeddings in embeddings module. |
| langsmith | Keep: traceable/tracing_context in agent; local fixture tracing tests and opt-in demo. |
| openai | Keep: exception classes and provider error mapping in agent/tests. |
| httpx (dev) | Keep: HTTP clients in verification scripts and response/error fixtures in tests. |
| rapidocr (ingest) | Keep: lazy RapidOCR import and adapter in `catalog_ingest/ocr.py`. |
| onnxruntime (ingest) | Keep: selected RapidOCR inference engine, explicit version metadata and engine configuration in OCR module; runtime need despite no direct import. |
| opencv-python-headless (ingest) | Keep: imported as `cv2` by pipeline, OCR, metadata and processing modules. |
| numpy (ingest) | Keep: geometry, OCR, pipeline and processing arrays. |

The backend lock also includes `langchain`/`langgraph`: `scripts/agent_acceptance.py` imports `langchain.tools`, so they are not safely removable lock-only leftovers. Other lock-only packages remain transitive pins; absence of a project import does not prove they are unused. `requirements-dev.txt` includes the backend lock; the ingest environment remains separate. AST inspection confirmed imports for fastapi (19), pydantic (9), pymupdf (4), psycopg (14), langchain_core (9), langchain_openai (3), langsmith (4), openai (6), httpx (5), rapidocr (2), cv2 (4), numpy (5), and langchain (1). Static search covered nested/lazy imports and package-name aliases across backend, scripts, catalog_ingest and tests, plus the server entrypoint.

## Gates

| Gate | Result |
|---|---|
| `docker compose build backend` | Exit 0. |
| `SERIES76_TEST_DB=1 .venv-model-eval/Scripts/python.exe -m unittest discover -s tests` | Exit 0; 660 run, 658 passed, 2 skipped, 328.406 s. |
| `.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t14_gates.py` | Exit 0; required subgates below all exit 0. |
| Backend image `python -m pip check` | Exit 0; no broken requirements. |

T14 subgates: unittest 660 run / 658 passed / 2 skipped (321.462 s); v7 **453/453**; T10 **48/48**; T12 **47/47**; T14 **42/42**; schema **5,520 bytes / 108 enum values / 0 forbidden nodes**; public text exit 0; ranking **40 queries / 2,720 judgments, NDCG@3 0.965378, returned compliance 1.0, no safety failures**.

**Diagnostic exception:** replay exits **1**, with **28/45 passing and 17/45 failing**. The existing runner explicitly excludes `replay` from its final exit calculation; its overall exit 0 must not be read as replay success. This matches the documented historical diagnostic 28/45 result and is outside dependency cleanup. No gate logic was changed. Raw refreshed runner artifacts were copied to `%TEMP%/p1d-t14-final` before restoring this run's generated tracked artifacts, so only the assigned report is committed.

No paid inference was executed. Build used `COMPOSE_ENV_FILES=.env.example` to avoid the existing private `.env`. Database-enabled unittest used only the three DB connection variables obtained from the existing container without printing them, `SERIES76_SKIP_DOTENV=1`, empty provider keys and disabled tracing/embeddings. The existing T14 runner uses its no-env wrapper. An initial PowerShell argument-quoting failure prevented retrieval of the DB password: that attempt ran 660 tests with 464 connection errors and two skips; it is a launcher failure, not a passing gate, and was rerun with correctly transported arguments.

## README clean clone

Clone retained for coordinator deletion: `<local-home>\Desktop\dev\serie76-clean-p1d-20261105`.

Created with local Git clone of the committed release branch (no working-tree files or existing environment copied). Copied its tracked `.env.example` to a new `.env`, then appended only the README isolation settings: `COMPOSE_PROJECT_NAME=serie76-clean`, `POSTGRES_PORT=55432`, `API_PORT=18000`. Keys stayed empty. Docker consumed the new configuration; the audit did not open any `.env`. No migrations, catalogue fixes or manual provisioning beyond README startup were necessary. HTTP API calls substitute for the Android UI in this backend smoke scope.

| Check, in requested order | Observed result |
|---|---|
| `docker compose up -d --build` | Exit 0; isolated database healthy and backend started. |
| GET `/ready` | HTTP 200, ready, 68 catalogue rows and 16 context terms. |
| Login `demo@series76.test` | HTTP 200 with README test password; token not logged. |
| Login `reviewer@series76.test` | HTTP 200 with README test password; token not logged. |
| `What is the motor power of 761A00-11300000/A?` | HTTP 200; 15 W, electrical catalogue page 1. |
| `What is the motor power of 999Z99-99999999/A?` | HTTP 200; explicitly not in catalogue / not found. |
| `What is the motor power of 761a00-11300000/a?` | HTTP 200; 15 W; answer explicitly states normalization to `761A00-11300000/A`, with matching `assumptions` field. |
| `I need an actuator for an outdoor valve` | HTTP 503, JSON `error_code: not_configured`. |
| `docker compose -p serie76-clean down -v` | Exit 0; only isolated clean containers, network and `serie76-clean_postgres_data` removed. |

Scope: keyless local backend and database only; no real provider, Android/device, load-test or new OCR accuracy claims. Existing project database volume was preserved.
