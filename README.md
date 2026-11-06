# Series 76 Technical Assistant
[English](README.md) · [Español](README.es.md)

Look up Series 76 actuators, compare models and resume previous conversations from a native Android app. The model interprets questions; PostgreSQL supplies the technical values.

## Quick start

1. **Requirements:** Git, Docker running Linux containers; Android Studio, **JDK 17**, SDK Platform 36 and a running API 26+ emulator. Run commands from the repository root; set `JAVA_HOME` to JDK 17 and `ANDROID_HOME` to your Android SDK.
2. **Configure:** `cp .env.example .env` (Windows: `copy .env.example .env`), only if `.env` does not exist. Paste your OpenRouter key into `OPENROUTER_API_KEY` for paid language interpretation; leave it empty for keyless startup. For local debug details, set `DEV_DEBUG=true` before starting.
3. **Start:** `docker compose up -d --build` (both platforms). Startup loads the catalogue and provisions the TEST ONLY accounts below without resetting existing passwords.
4. **Health:** open [http://localhost:8000/ready](http://localhost:8000/ready); wait for HTTP 200 after the initial build/load. [API / Swagger](http://localhost:8000/docs). This checks the database/catalogue/glossary, not OpenRouter.
5. **Login:** use either public **TEST ONLY** account:

| Email | Public test password |
|---|---|
| demo@series76.test | Series76-Demo-1 |
| reviewer@series76.test | Series76-Demo-2 |

6. **Build + install on the running emulator** (choose your platform):
   - macOS/Linux: `sh mobile/android/gradlew -p mobile/android :app:installDebug -PbackendUrl=http://10.0.2.2:8000/`
   - Windows PowerShell: `./mobile/android/gradlew.bat -p mobile/android :app:installDebug -PbackendUrl=http://10.0.2.2:8000/`
   - Open **Series 76**, sign in, then try `What is the motor power of 761A00-11300000/A?` (keyless). The emulator reaches the backend at **http://10.0.2.2:8000/**.
7. **Debug:** tap the profile name/email **7 times within 3 seconds**, then tap **ⓘ** on an answer. Requires `DEV_DEBUG=true`; if changed after startup, apply with `docker compose up -d backend`.


## Setup and backend

The steps above run from the repository root. Docker loads the included catalogue; you do not need to repeat OCR. Keep an existing `.env` and PostgreSQL volume. **Do not run `docker compose down -v`.**

Without an OpenRouter key, login, history and direct lookups/comparisons work. Free-language interpretation returns `503 not_configured` until configured. `/ready` checks the database and data, not the model provider.

The full template is [.env.example](.env.example). The main settings are:

- `OPENROUTER_API_KEY`: your key for language interpretation; leave empty for keyless testing.
- `OPENROUTER_CHAT_MODEL=google/gemini-3.6-flash`; `OPENROUTER_FALLBACK_MODEL=` keeps fallback disabled.
- `OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2`; `EMBEDDING_DIM=768` must match the schema.
- `DEV_DEBUG=true` enables the authenticated debug endpoint.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` and `API_PORT` configure the local services. Preserve an existing volume's password.

Apply configuration changes with `docker compose up -d backend`. For a second isolated checkout or port conflicts, follow [operations](docs/wiki/en/operations.md). [API requests and responses](docs/wiki/en/api.md#curl).

## Demo users (TEST ONLY)

The two public accounts in Quick start are for testing only. Each sees its own conversations. Startup creates missing accounts without resetting passwords; `DEMO_USERS_JSON=[]` disables creation of new demo accounts.

## Android

Use **JDK 17**, SDK Platform 36 and an API 26+ emulator. Check `java -version` before building. The emulator reaches the host at `http://10.0.2.2:8000/`; change the address with `-PbackendUrl=https://your-host/` and rebuild. [SDK setup, USB devices and build commands](docs/wiki/en/android.md).

**Debug:** enable `DEV_DEBUG=true`, tap the profile name/email seven times in three seconds, then open **ⓘ** on an answer. It shows tools, parameters and returned data; `llm_called` tells you whether the model was used.

**Voice:** tap the microphone, review the transcript and press Send. Android handles recognition; no audio goes to this backend. On-device recognition is preferred, but the fallback service may use the network. Real recognition was manually confirmed in the emulator; physical-device behavior remains unverified. [Voice and debug details](mobile/android/README.md).

## Ingestion

The validated data is in [data/extracted/series76](data/extracted/series76). To regenerate it, use a separate Python 3.12 environment and a new output folder:

```sh
# macOS/Linux
python3 -m venv .venv-ingest
. .venv-ingest/bin/activate
pip install -r requirements-ingest.lock.txt
python scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/new-import
```

```powershell
# Windows PowerShell
python -m venv .venv-ingest
.\.venv-ingest\Scripts\Activate.ps1
pip install -r requirements-ingest.lock.txt
python scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/new-import
```

The first run downloads public OCR weights; recognition then runs locally. CSV/JSON/HTML and the manifest appear in a per-document subfolder under the output root. Ambiguous extraction blocks validated export. [Pipeline, validation and loading](docs/wiki/en/ingestion.md).

## Models, design and limitations

Android uses Kotlin/Compose and calls FastAPI. LangChain makes one completed tool decision when interpretation is needed; direct lookups and structured actions skip the model. Code validates arguments, queries SQL and builds the answer. This keeps figures tied to the PDF, but requires explicit rules and does not eliminate interpretation errors.

Flash was retained for the quality/latency balance observed in the [model comparison](docs/wiki/en/testing.md#openrouter-model-selection). There is no fallback model. pgvector retrieves interpretation examples; it does not supply product figures. [Architecture](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura) · [Design decisions](https://github.com/SamuelCharry/serie76-assistant/wiki/Decisiones).

The measured candidate passed **79.4%** of conversations on average, versus **61.1%** previously. Later fixes passed offline checks but have no new independent paid score. Recorded evaluation spend was **USD 6.17 of 10**, not a live balance. [Results and known limits](reports/submission/P2-A.md).

## Example bank

Optional semantic examples help interpret phrasing. Startup does not generate their vectors; loading them consumes provider credit. [Dry-run, loading and configuration](docs/wiki/en/operations.md#example-bank).

## Reproduction gates

[T18](reports/submission/T18-tag-clean-clone.md) records a fresh-clone test of `v1.0-submission`: 10/10 steps, 795 Python tests passed with 2 skipped, and 126 Android JVM tests passed. These are scoped checks, not proof of every input or device.

For local tests, first follow the [Python environment setup](docs/wiki/en/testing.md#run-locally). With Compose running:

```text
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
python scripts/check_tool_schemas.py
python scripts/verify_catalog_db.py
```

## Repository map

[Backend](backend/) · [Android](mobile/android/) · [OCR](catalog_ingest/) · [Tests](tests/) · [AI assistant configuration](.claude/)

[Wiki](https://github.com/SamuelCharry/serie76-assistant/wiki) · [Assessment checklist](docs/SUBMISSION.md) · [Assessment](docs/assessment-en.pdf)
