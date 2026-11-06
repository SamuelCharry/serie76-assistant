# Operations

[Wiki](index.md) · [English](../en/operations.md) · [Español](../es/operations.md)

Configuration defaults and recovery without destroying catalogue or history.

Docker Compose is the supported backend path. Copy the example only when no local configuration exists; do not overwrite a working .env. Startup migrates, imports the validated catalogue/glossary and provisions TEST ONLY users idempotently before Uvicorn. The PostgreSQL volume persists across restart and ordinary compose down; never run `docker compose down -v`.

For an independent second checkout, add `COMPOSE_PROJECT_NAME=serie76-clean`, `POSTGRES_PORT=55432` and `API_PORT=18000` to its `.env` before running Compose. Use `http://localhost:18000` in HTTP examples and `-PbackendUrl=http://10.0.2.2:18000/` for its emulator build. These names and ports isolate this checkout; keep its database password consistent with its own volume.

## Configuration reference

Defaults below come from [.env.example](../../../.env.example) and [Compose](../../../docker-compose.yml), not the private local environment.

The README table covers the added embedding/debug settings. [.env.example](../../../.env.example) is the full configuration template: startup uses `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` and `API_PORT`; Compose also accepts `COMPOSE_PROJECT_NAME`. Language interpretation requires `OPENROUTER_API_KEY` and `OPENROUTER_CHAT_MODEL`. Preserve empty credentials for keyless evaluation; advanced retries, deadlines, tracing and evaluation-only variables are commented in that template.

| Variable | Default | Purpose |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | checkout directory name | Compose project/volume isolation; set explicitly for a second checkout. |
| `POSTGRES_DB` | `series76` | PostgreSQL database on first initialization. |
| `POSTGRES_USER` | `series76` | PostgreSQL role on first initialization. |
| `POSTGRES_PASSWORD` | `replace-with-local-password` | Local placeholder; choose a private value before use beyond this TEST ONLY setup. Required by Compose; changing it does not reset an existing volume password. |
| `POSTGRES_PORT` | `5432` | Host loopback DB port; container stays 5432. |
| `API_PORT` | `8000` | Host loopback HTTP port; container stays 8000. |
| `OPENROUTER_API_KEY` | _empty_ | Private model credential; empty disables conversation interpretation. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible chat endpoint; production default is OpenRouter. |
| `OPENROUTER_CHAT_MODEL` | `google/gemini-3.6-flash` (provisional) | Explicit tool-calling model ID; no automatic model selection. |
| `OPENROUTER_FALLBACK_MODEL` | empty (disabled) | Optional fallback model on the same endpoint/key; empty disables it. Transient failures only. |
| `AGENT_TURN_DEADLINE_S` | `60` | Shared deadline for primary attempts and fallback, below Android's 70/75 s timeouts. |
| `AGENT_RETRY_MIN_REMAINING_S` | `10` | Minimum remaining seconds to start an attempt; otherwise record deadline_skipped without a reservation. |
| `AGENT_MAX_TOKENS` | `2048` | Maximum generated tokens per decision. |
| `AGENT_REASONING_EFFORT` | `low` | Provider reasoning effort; empty omits parameter. |
| `AGENT_TOOL_CHOICE` | `required` | Tool choice for bind_tools; empty lets provider decide. |
| `AGENT_TIMEOUT_S` | `45` | Per-attempt ceiling, reduced to remaining deadline; SDK max_retries=0, LangChain owns bounded retry. |
| `AGENT_TEMPERATURE` | _empty_ | Empty means provider sampling default. |
| `LANGSMITH_TRACING` | `false` | Opt-in external tracing; also requires key. |
| `LANGSMITH_API_KEY` | _empty_ | Private tracing credential; never sent to Android. |
| `LANGSMITH_PROJECT` | `serie76-assistant` | Trace project name. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Trace service endpoint; configure EU host for an EU workspace. |
| `DEV_DEBUG` | `false` | Owner-scoped developer trace endpoint; false returns 404. |
| `OPENROUTER_EMBEDDING_MODEL` | `google/gemini-embedding-2` (provisional) | Optional model; Google `gemini-embedding-2`, OpenRouter `google/gemini-embedding-2`. |
| `EMBEDDINGS_ENABLED` | `true` | ON only with a configured model; `false` forces OFF. |
| `EMBEDDING_DIM` | `768` | Only dimension accepted by schema/client. |
| `EMBEDDING_BASE_URL` | _empty_ | Inherits `OPENROUTER_BASE_URL` when empty. |
| `EMBEDDING_API_KEY` | _empty_ | Inherits `OPENROUTER_API_KEY` when empty. |
| `EMBEDDING_EXCLUDE_SOURCES` | _empty_ | Comma-separated held-out source IDs; excluded before ranking/LIMIT. |
| `TESSERACT_CMD` | _empty_ | Legacy local OCR executable override, not current RapidOCR ingestion; not forwarded to backend. |
| `GOOGLE_API_KEY` | _empty_ | Evaluation only; not forwarded to production backend. Never enables paid work by itself. |
| `OPENROUTER_REQUIRE_PARAMETERS` | `true` | Adds provider.require_parameters for openrouter.ai routing. |
| `AGENT_MAX_CALLS_PER_HOUR` | `120` | Rolling-hour attempt cap per process; restart resets it; not money/global quota. |
| `DEMO_USERS_JSON` | _empty_ | Empty provisions public TEST ONLY accounts; [] disables new provisioning; existing passwords never reset. Override is a JSON array of email/name/password objects. |

Compose forwards these backend connection variables directly (they are not additional .env.example settings):

| Variable | Compose value | Purpose / Propósito |
|---|---|---|
| PGHOST | db | DB service / servicio DB |
| PGPORT | 5432 | Container DB port / puerto interno DB |
| PGDATABASE | POSTGRES_DB, fallback series76 | Database / base |
| PGUSER | POSTGRES_USER, fallback series76 | Role / rol |
| PGPASSWORD | POSTGRES_PASSWORD, required | Private connection password / contraseña privada |

`POSTGRES_PASSWORD` has no Compose fallback: it must be nonempty; the copied example provides a TEST ONLY placeholder. The image healthcheck also uses the container POSTGRES_USER/POSTGRES_DB. `DATABASE_URL` is an optional local backend connection override in `backend/catalog/db.py`, not forwarded by this Compose file. Local CLI loads connection settings via local_environment(); Uvicorn outside Docker requires exported PG* variables. Never dump environment/configuration into reports.

## Enable language interpretation

Only after explicit inference authorization, set these private local values and recreate backend. This documents configuration; it does not authorize a call or claim OpenRouter acceptance.

```dotenv
OPENROUTER_API_KEY=<your-private-key>
OPENROUTER_CHAT_MODEL=google/gemini-3.6-flash
```

```sh
docker compose up -d backend
curl http://localhost:8000/ready
```
The adopted improvement averaged 79.4% versus 61.1% in three paired v17 runs; about 20% of novel conversations still fail. See [current results and repair boundaries](../../../README.md#models-design-and-limitations). A ready=200 response checks catalogue/glossary, not credentials, model routing or remaining balance. LangSmith remains off unless tracing=true and a key are both present; enabling it sends prompts/user text/tool data/catalogue rows externally. See [agent](agent.md).

The OpenRouter bank reload used `google/gemini-embedding-2`: 658 examples + 100 anchors, about USD 0.0015; see [Models](../../../README.md#models-design-and-limitations).

## pgvector

Compose and CI pin `pgvector/pgvector:pg17-trixie@sha256:01215e09bd4bd582d20230e025b6c971deeeffee49ceef1aae167e839cb62a7e`. Migration 007 enables vector and creates `series76.example_bank`/`concept_anchor`; 008 adds versions, active state and an immutable manifest. Catalogue figures remain relational.

Before changing the image for an existing PG17 volume, back it up and check actual collation/glibc versions. The verified volume was created with glibc 2.41; the initial pg17 tag carried 2.36. Trixie retains 2.41, with collations and row counts verified after the change. Do not delete the volume or change its password to upgrade; never `docker compose down -v`. A mismatch needs a migration/reindexing plan, not a version refresh that hides it. [T9 backup and checks](../../../reports/submission/T9-embeddings.md).

## Example bank

The loader uses `config/agent_acceptance_cases_v7.json` and `config/concept_anchors.json`: 658 unique phrasings/interpretations plus 100 anchors. It stores neither answers nor published figures as knowledge; quantities in an example are that example's requirements, not a new query's requirements. It preserves all source IDs, excludes ambiguous/conflicting labels and supports held-out source exclusion. The bank includes historical v7 cases: their replay is regression, not held-out acceptance. [Method](testing.md#behavior-evaluation).

The bank is optional for keyless operation. With no model configured, `--dry-run` reports all supplied examples/anchors without a database, API key or inference (`scope: input_only`); it does not check existing vectors. With an explicit model it checks pending rows in the running DB, still without inference. The second command below loads vectors for the named model and must wait for paid-inference authorization; configure that same model for backend retrieval. Start Compose for a model-specific pending-row check. Commands from the root for PowerShell and macOS/Linux; the mount supplies config without changing the image or normal entrypoint:

```text
docker compose run --rm --no-deps --entrypoint python -v ./config:/app/config:ro backend scripts/load_example_bank.py --dry-run
```

Only after inference authorization:

```text
docker compose run --rm --no-deps --entrypoint python -e OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2 -v ./config:/app/config:ro backend scripts/load_example_bank.py
docker compose up -d backend
```

The initial Google load estimated USD 0.004911 (about USD 0.005), 749 texts in 24 requests; this is neither a receipt nor a guaranteed OpenRouter cost. A verified repeat had no pending texts or additional estimated cost. Vectors are namespaced by model ID: switching to `google/gemini-embedding-2` requires a newly authorized load, never relabel old vectors. Loading is transactional/idempotent; failure does not refund incurred charges. `--replace-dataset --dataset-version VERSION` explicitly replaces the complete set, deactivates absent/conflicting rows and retains historical provenance; do not submit a subset as a complete replacement.

A real load requires an explicit model and valid inference credentials; the model-free dry-run only previews the input. In conversation, OFF/missing configuration/timeout/SQL failure omits retrieval and retains the deterministic parser; without configured chat, turns requiring interpretation return 503. Startup only prepares the client, never pays for embeddings; deterministic routes do not invoke them either. Startup does not load the bank automatically. [Loader code](../../../scripts/load_example_bank.py), [client and deadline](../../../backend/conversation/embeddings.py).

**Voice/debug:** voice uses Android permission, without a backend speech key. For traces set `DEV_DEBUG=true`, recreate backend and use the seven-tap gesture; return to `false` after review. The GET is lazy and owner-scoped. [Android instructions](android.md#developer-debug).

## Troubleshooting

### Port 5432 busy

Set POSTGRES_PORT=5433 locally and recreate db/backend; do not stop unrelated databases. Container PGPORT stays 5432.

### /ready 503

Check docker compose ps, then docker compose logs --tail 100 backend db locally. Startup must complete migrations/catalogue/glossary; rerun cli status. Missing model configuration alone does not fail readiness.

### Docker not running

Start Docker Desktop with Linux containers; verify docker info and retry up --build -d. No reset/reinstall or volume deletion is needed.

### CRLF entrypoint

docker/entrypoint.sh must use LF (.gitattributes). If logs show /bin/sh^M or exec format failure, restore LF and rebuild backend; preserve the DB volume.

### 503 not_configured

Set both key and model only after authorization; ensure backend was recreated. Missing/invalid provider credentials also map here. History/catalogue routes still work when the model is unconfigured.

### Other 503 codes

Check the API error table: provider timeout/quota/budget/unreachable, local call guard or concurrency capacity. Do not blindly retry POST; reload history first.

### Login fails after restart

Existing demo passwords are never reset. Use existing credentials or explicit account administration; do not delete the volume to force the published TEST ONLY password.

### First tap fails after idle

The T7 connection mismatch was a pooled OkHttp socket outliving Uvicorn's former 5 s keep-alive. Update/rebuild both backend and APK: client pool expiry is now 30 s and server keep-alive 75 s. Confirm the backend uses `--timeout-keep-alive 75`; do not enable POST retries to mask the error. On uncertain delivery, reload history before resending. [Local regression and its limits](android.md#first-tap-connection-failure).

For slow provider responses, distinguish keep-alive from the 60 s decision deadline. Only 503/timeout/connection failures may retry (two attempts per model); no 4xx. Optional fallback shares the deadline and every real attempt consumes the process cap. `turn_deadline` / `deadline_skipped` means no time remained for another safe attempt; blindly increasing timeouts can outlast the app's call timeout. See [agent](agent.md#retry-fallback-and-deadline).

### Android cannot connect

Use 10.0.2.2 for emulator or adb reverse for USB; rebuild if backendUrl changes. Release requires HTTPS.

For private account administration, `python -m backend.auth.cli create-user --email user@example.com --name Name` prompts for a password; do not put private credentials in command history. `assign-legacy --session UUID --email user@example.com --confirm` assigns only one ownerless conversation after an explicit ownership review. No automatic legacy-history assignment exists. Login throttles 10 attempts/email and 30/client IP per five minutes, with two concurrent password verifications per process; a trusted proxy must be designed before public exposure.

## Tool-schema preflight before any cohort

Run `python scripts/check_tool_schemas.py` offline first. It builds the real four production tools without a database or credentials and prints compact bytes, enum values, arrays, required fields, depth, numeric range keywords and lookup object arrays. Offline guards cap enums/arrays/required/depth at the pre-T6 counts (108/6/5/7) and reject numeric ranges, nullable unions/references and object arrays in get_actuator. Byte size alone did not predict the provider's cumulative schema limit.

Only after explicit paid-call approval, run `python scripts/check_tool_schemas.py --live` with OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL and optional OPENROUTER_BASE_URL already in the process environment. It never loads .env or prints the key, provider response or exception body; it sends exactly one request with all four tools and the production system/glossary prompt, disables tracing, performs no tool/SQL execution and has no retries. A 400 or other failure exits non-zero: stop before the cohort. A successful preflight checks schema acceptance only, not conversation quality. Re-run after any tool-schema change; see the recorded [OpenRouter preflight results](testing.md#openrouter-model-selection).

Where: [preflight script](../../../scripts/check_tool_schemas.py), [complexity/one-call tests](../../../tests/test_tool_schema_budget.py), [metadata-only readiness script](../../../scripts/check_openrouter.py).

## Where in the code

- [docker/entrypoint.sh](../../../docker/entrypoint.sh#L1)
- [backend/conversation/agent.py](../../../backend/conversation/agent.py#L224)
- [backend/catalog/db.py](../../../backend/catalog/db.py#L15)
- [backend/auth/cli.py](../../../backend/auth/cli.py#L34)

## Known limits

Four concurrent conversation turns per process; a second turn for one session gets 409. Database transactions stay open during model calls. No distributed queue, global billing cap, public TLS deployment, password recovery or backup/restore campaign is established. At 100× traffic, process-local limits and long DB transactions require redesign and measurement.
