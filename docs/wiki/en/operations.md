# Operations

[Wiki](index.md) · [English](../en/operations.md) · [Español](../es/operations.md)

Configuration defaults and recovery without destroying catalogue or history.

Docker Compose is the supported backend path. Copy the example only when no local configuration exists; do not overwrite a working .env. Startup migrates, imports the validated catalogue/glossary and provisions TEST ONLY users idempotently before Uvicorn. The PostgreSQL volume persists across restart and ordinary compose down; never run `docker compose down -v`.

## Configuration reference

Defaults below come from [.env.example](../../../.env.example) and [Compose](../../../docker-compose.yml), not the private local environment.

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_DB` | `series76` | PostgreSQL database on first initialization. |
| `POSTGRES_USER` | `series76` | PostgreSQL role on first initialization. |
| `POSTGRES_PASSWORD` | `replace-with-local-password` | Local placeholder; choose a private value before use beyond this TEST ONLY setup. Required by Compose; changing it does not reset an existing volume password. |
| `POSTGRES_PORT` | `5432` | Host loopback DB port; container stays 5432. |
| `API_PORT` | `8000` | Host loopback HTTP port; container stays 8000. |
| `OPENROUTER_API_KEY` | _empty_ | Private model credential; empty disables conversation interpretation. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible chat endpoint; production default is OpenRouter. |
| `OPENROUTER_CHAT_MODEL` | _empty_ | Explicit tool-calling model ID; no automatic model selection. |
| `AGENT_MAX_TOKENS` | `2048` | Maximum generated tokens per decision. |
| `AGENT_REASONING_EFFORT` | `low` | Provider reasoning effort; empty omits parameter. |
| `AGENT_TOOL_CHOICE` | `required` | Tool choice for bind_tools; empty lets provider decide. |
| `AGENT_TIMEOUT_S` | `45` | Model client timeout in seconds; max_retries=0. |
| `AGENT_TEMPERATURE` | _empty_ | Empty means provider sampling default. |
| `LANGSMITH_TRACING` | `false` | Opt-in external tracing; also requires key. |
| `LANGSMITH_API_KEY` | _empty_ | Private tracing credential; never sent to Android. |
| `LANGSMITH_PROJECT` | `serie76-assistant` | Trace project name. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Trace service endpoint; configure EU host for an EU workspace. |
| `DEV_DEBUG` | `false` | Owner-scoped developer trace endpoint; false returns 404. |
| `OPENROUTER_EMBEDDING_MODEL` | _empty_ | Unused in operational A+; no vector store. |
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
The model was evaluated through Google's OpenAI-compatible endpoint; OpenRouter acceptance is pending. A ready=200 response checks catalogue/glossary, not credentials, model routing or remaining balance. LangSmith remains off unless tracing=true and a key are both present; enabling it sends prompts/user text/tool data/catalogue rows externally. See [agent](agent.md).

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

### Android cannot connect

Use 10.0.2.2 for emulator or adb reverse for USB; rebuild if backendUrl changes. Release requires HTTPS.

For private account administration, `python -m backend.auth.cli create-user --email user@example.com --name Name` prompts for a password; do not put private credentials in command history. `assign-legacy --session UUID --email user@example.com --confirm` assigns only one ownerless conversation after an explicit ownership review. No automatic legacy-history assignment exists. Login throttles 10 attempts/email and 30/client IP per five minutes, with two concurrent password verifications per process; a trusted proxy must be designed before public exposure.

## Tool-schema preflight before any cohort

Run `python scripts/check_tool_schemas.py` offline first. It builds the real four production tools without a database or credentials and prints compact bytes, enum values, arrays, required fields, depth, numeric range keywords and lookup object arrays. Offline guards cap enums/arrays/required/depth at the pre-T6 counts (108/6/5/7) and reject numeric ranges, nullable unions/references and object arrays in get_actuator. Byte size alone did not predict the provider's cumulative schema limit.

Only after explicit paid-call approval, run `python scripts/check_tool_schemas.py --live` with OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL and optional OPENROUTER_BASE_URL already in the process environment. It never loads .env or prints the key, provider response or exception body; it sends exactly one request with all four tools and the production system/glossary prompt, disables tracing, performs no tool/SQL execution and has no retries. A 400 or other failure exits non-zero: stop before the cohort. A successful preflight checks schema acceptance only, not conversation quality. Re-run after any tool-schema change; the compact-schema live check is pending until the coordinator runs it.

Where: [preflight script](../../../scripts/check_tool_schemas.py), [complexity/one-call tests](../../../tests/test_tool_schema_budget.py), [metadata-only readiness script](../../../scripts/check_openrouter.py).

## Where in the code

- [docker/entrypoint.sh](../../../docker/entrypoint.sh#L1)
- [backend/conversation/agent.py](../../../backend/conversation/agent.py#L224)
- [backend/catalog/db.py](../../../backend/catalog/db.py#L15)
- [backend/auth/cli.py](../../../backend/auth/cli.py#L34)

## Known limits

Four concurrent conversation turns per process; a second turn for one session gets 409. Database transactions stay open during model calls. No distributed queue, global billing cap, public TLS deployment, password recovery or backup/restore campaign is established. At 100× traffic, process-local limits and long DB transactions require redesign and measurement.
