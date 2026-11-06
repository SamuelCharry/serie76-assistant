# T9-C1 - Clean README reproducibility audit

> Update 2026-11-05: this historical report retains its original run scope and numbers; OpenRouter acceptance and bank reload are now completed, with provisional model defaults and pending post-fix held-out v12 documented in [README Models](../../README.md#models-design-and-limitations).

Commit: `54a0a83936f7185180ed1ec2c73f8998680e5575` (`release/submission`).
Clone: `<local-home>\orca\clean-test\serie76-assistant`.
Started: 2026-11-04 22:56:15 UTC. Verification and cleanup finished: 2026-11-04 23:15:23 UTC. Total wall time: **19 minutes 8 seconds** (includes installs, report drafting, audit commands and explicit-isolation rerun; excludes final delivery).

## Verdict and boundaries

Full README reproduction FAILS: the documented v6 selfcheck fails 21/103 scenarios, the catalogue verifier fails an HTTP-auth check, and the keyless motor-power walkthrough returns 503. The Python database suite passes 484 tests with two skips (211.941 s); Docker startup, authenticated comparison/numeric grounding, OCR and the debug APK also pass. The optional bank dry-run needs an explicit model ID. The catalogue verifier initially probed port 8000; an explicitly isolated rerun is recorded separately below.

Only the local Git clone was used for repository content; the original checkout and its `.env` were not opened. No provider key was supplied and no paid inference was run. Existing Docker layer, pip-wheel and Gradle caches were available on this Windows host: this is a clean checkout and new database volume, not a pristine OS/offline installation. No emulator installation or device interaction was performed.

## Setup and command conventions

Executed:

```powershell
git clone <repository> <local-home>\orca\clean-test\serie76-assistant --branch release/submission
git status --short
git rev-parse HEAD
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
$cleanEnv = Get-Content .env -Raw
$cleanEnv = $cleanEnv.Replace('POSTGRES_PORT=5432','POSTGRES_PORT=55432').Replace('API_PORT=8000','API_PORT=18000')
Set-Content .env ($cleanEnv + "`nCOMPOSE_PROJECT_NAME=serie76-clean`n") -Encoding ascii
docker compose -p serie76-clean config --format json
```

Output: `Cloning ... done`; initially clean Git status; commit above. Configuration inspection emitted only project/ports/volume metadata: project `serie76-clean`, `127.0.0.1:55432 -> 5432`, `127.0.0.1:18000 -> 8000`, volume `serie76-clean_postgres_data`. The startup log confirms that volume was **Created**, not reused. All following Compose commands ran from this clone with that `.env`; Manual HTTP examples substituted port 18000 for 8000. No Docker command targeted project `serie76-assistant`; however, the first documented catalogue-verifier execution used its internal default HTTP port 8000, as disclosed below.

The README delegates API examples and tests to linked wiki pages; those pages were followed. Shell redirection/Tee-Object captured evidence under `reports/submission/t9-clean-evidence/`. PowerShell sometimes wraps ordinary native stderr in `NativeCommandError`; exit codes and final tool summaries, not that wrapper alone, determine the result.

## Step table

| Step | Result | Exact command / check | Output excerpt / evidence |
|---|---|---|---|
| 1 Git | PASS | `git --version` | `git version 2.54.0.windows.1` |
| 1 Python | PASS | `python --version`; `python -c "import platform,struct; print(platform.python_version(),struct.calcsize('P')*8)"` | `Python 3.12.10`; `3.12.10 64` |
| 1 Docker | PASS | `docker --version`; `docker compose version`; `docker info --format '{{.OSType}}'` | `29.7.2`; `v5.3.1`; `linux` |
| 1 JDK 17 requirement | FAIL | `java -version` | Available runtime is Microsoft OpenJDK `21.0.11`; JDK 17 was not available in the inspected standard installation directories; build below passed on 21, not proof of a 17 run |
| 1 SDK Platform 36 | PASS | `Get-Content "$env:ANDROID_HOME/platforms/android-36/source.properties"` | `AndroidVersion.ApiLevel=36`, revision 2; ANDROID_HOME points to the installed SDK |
| 1 adb on PATH | FAIL | `adb version` | `The term 'adb' is not recognized`; `& "$env:ANDROID_HOME/platform-tools/adb.exe" version` succeeds with `1.0.41`, platform-tools `37.0.1-15733141`; no installation attempted |
| 2 Build/start | PASS | `docker compose up --build -d` | Exit 0; clean image/network/volume/containers created; `docker-build.log` |
| 2 Migrations/data/users | PASS | `docker compose logs --no-color backend`; `docker compose exec -T backend python -m backend.catalog.cli status` | `migrated`; `loaded ... rows: 68`; `terms: 16`; `2 created; existing accounts unchanged`; `startup.log` |
| 2 Readiness | PASS | `curl.exe -i http://localhost:18000/ready` | `HTTP/1.1 200 OK`, `status: ready`, `rows: 68`, `context_terms: 16`; `ready.txt` |
| 2 Example-bank default dry-run | FAIL | `docker compose run --rm --no-deps --entrypoint python -v ./config:/app/config:ro backend scripts/load_example_bank.py --dry-run` | Nonzero exit: `Set OPENROUTER_EMBEDDING_MODEL in the process environment`; model is empty by default |
| 2 Example-bank explicit model dry-run | PASS | `docker compose run --rm --no-deps --entrypoint python -e OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2 -v ./config:/app/config:ro backend scripts/load_example_bank.py --dry-run` | Exit 0; `pending_texts: 749`, `examples: 649`, `anchors: 100`, `batches: 24`, estimated USD `0.004911`; no vectors generated, no inference authorized |
| 3 Login | PASS | Windows file-input commands in API transcript below | Demo user authenticated; token kept in process memory and omitted from evidence |
| 3 Documented motor-power query | FAIL | `curl.exe -sS -i http://localhost:18000/api/conversation -H "Authorization: Bearer $token" -H 'Content-Type: application/json' --data-binary '@query.json'`, with the exact linked question | `HTTP/1.1 503 Service Unavailable`, `error_code: not_configured`; `documented-query-http.txt` |
| 3 Greeting/comparison | PASS | Same POST, query `hola`, then `Compare 761A00-11300000/A vs 761B00-11300000/A` | Greeting HTTP 200; comparison returns persisted answer and two products; `greeting.json`, `comparison.json` |
| 3 History | PASS | `curl.exe -sS http://localhost:18000/api/sessions -H "Authorization: Bearer $token"`; `curl.exe -sS "http://localhost:18000/api/sessions/$session/messages" -H "Authorization: Bearer $token"` | Both HTTP 200; comparison history has 2 messages; `sessions.json`, `messages.json` |
| 3 Numeric grounding | PASS | `curl.exe -sS http://localhost:18000/api/actuators/761A00-11300000/A -H "Authorization: Bearer $token"`; `python reports/submission/t9-clean-evidence/check-numeric.py` | Product HTTP 200; API and retained CSV both give `15 W` motor power and `80 Nm` On/Off torque; comparison gives `80 Nm vs 100 Nm` |
| 3 Expected keyless interpretation | PASS | Same POST with `I need an actuator suitable for my factory, please help select it` | HTTP 503 `not_configured`, as README describes; `keyless.txt` |
| 4 OCR environment | PASS | `python -m venv .venv-ingest`; `.\.venv-ingest\Scripts\Activate.ps1`; `pip install -r requirements-ingest.lock.txt` | Exit 0; dependencies installed; `ingest-install.log` |
| 4 Fresh extraction | PASS | `python scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/new-import` | Exit 0; 4 pages, 7 tables, 68 rows, zero issues, `status: ready`, `reused: False`; `ingest.log` |
| 4 OCR geometry/safety tests | PASS | In OCR environment: `python -m unittest discover -s tests -p test_dynamic_geometry.py`; `python -m unittest discover -s tests -p test_pipeline_safety.py` | 8 tests / 17 tests, both OK; `geometry-tests.log`, `pipeline-tests.log` |
| 4 Retained-data reload | PASS | `docker compose exec -T backend python -m backend.catalog.cli load data/extracted/series76` | `status: already_loaded`, `import_id: 1`, `rows: 68`, `activated: true` |
| 5 Python environment | PASS | `python -m venv .venv`; `.\.venv\Scripts\Activate.ps1`; `pip install -r requirements-dev.txt` | Exit 0; `backend-install.log` |
| 5 Python database suite | PASS | `$env:SERIES76_TEST_DB='1'`; `python -m unittest discover -s tests` | `Ran 484 tests in 211.941s`, `OK (skipped=2)`; `python-tests.log`; clean connection explicitly pinned to 55432 |
| 5 Catalogue verifier, documented default | FAIL | `python scripts/verify_catalog_db.py` | Exit 1; numeric checks 941/941 and nested suite 484 tests / 2 skips pass, then actuator HTTP 401; default HTTP port 8000 is an isolation deviation, not clean-API evidence; `verify-catalog.log` |
| 5 Catalogue verifier, isolated rerun | FAIL | `python scripts/verify_catalog_db.py --base-url http://127.0.0.1:18000 --out reports/submission/t9-clean-evidence/catalog-isolated` | Exit 1; same actuator 401 on the CLEAN backend; nested suite 484 tests / 2 skips passes in 193.347 s; `verify-catalog-isolated.log` |
| 5 Selfcheck | FAIL | `python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json` | Exit 1; 103 scenarios, 21 failing, 82 passing; `selfcheck.log` |
| 6 Debug APK | PASS | `./mobile/android/gradlew.bat -p mobile/android assembleDebug` | `BUILD SUCCESSFUL in 1m 3s`; `39 actionable tasks: 39 executed`; `android-build.log` |
| 6 App documentation | PASS | Read README Android section | `-PbackendUrl=...`, emulator `10.0.2.2`, USB reverse, seven taps within three seconds, per-answer info button, `DEV_DEBUG=true`, voice permission/fallback/transcript all present |
| 7 README links | PASS | `python reports/submission/t9-clean-evidence/audit-docs.py`; `curl.exe -sS -o NUL -w 'Swagger HTTP %{http_code}\n' http://localhost:18000/docs` | 45 unique local paths/fragments resolve; one localhost Swagger link resolves on the isolated port with HTTP 200; `docs-audit.json` |
| 7 Environment/model docs | PASS | Audit README table against `.env.example` and `docker-compose.yml` | All six listed defaults match; OpenRouter endpoint, model IDs, choice rationale and pending acceptance present; table intentionally says New variable, not a complete inventory |

## API transcript and numeric evidence

The linked Windows API recipe was used with the isolated port. Token output was captured in a local variable, not logged:

```powershell
'{"email":"demo@series76.test","password":"Series76-Demo-1"}' | Set-Content -Encoding ascii login.json
$login = curl.exe -sS http://localhost:18000/api/auth/login -H 'Content-Type: application/json' --data-binary '@login.json' | ConvertFrom-Json
$token = $login.access_token
'{"query":"What is the motor power of 761A00-11300000/A?"}' | Set-Content -Encoding ascii query.json
curl.exe -sS -i http://localhost:18000/api/conversation -H "Authorization: Bearer $token" -H 'Content-Type: application/json' --data-binary '@query.json'
# Replace query.json with each tested query, using the same POST:
'{"query":"hola"}' | Set-Content -Encoding ascii query.json
'{"query":"Compare 761A00-11300000/A vs 761B00-11300000/A"}' | Set-Content -Encoding ascii query.json
Remove-Item -LiteralPath login.json,query.json
```

The comparison returned `On/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm`. The first product's API measurements and the retained CSV row `base_part_number=761A00-11300000/A` both contain `motor_power_w=15`, `on_off_torque_nm=80`. The checking script accounts for the CSV's UTF-8 BOM. An initial audit-helper attempt used the wrong CSV column/encoding; that was an auditor script error, corrected before the successful assertions, not a product finding.

## Ingestion destination

New output is at:

`data/processed/new-import/doc-series_76_electric_data-4c28023929183df8-1ec4358fe0/`

It contains `catalog.csv`, `catalog.json`, `catalog.html`, `manifest.json`, `cells.jsonl`, `review_queue.jsonl`, `evidence/` and `work.sqlite3`. The manifest reports `ready`, 68 rows, four source-N/A rows, zero issues, zero reference values loaded and zero external API calls; extraction elapsed time is 159.66 seconds. Initial public model-weight downloads happened before local recognition and are described in the linked ingestion guide. The manifest is inside the per-document folder, not directly at the output root; this agrees with the linked guide. The validated retained folder was not overwritten, and reloading it was idempotent. No full `verify_ingestion.py`/scale benchmark was needed for the requested verification-or-reload step; the documented reload was executed.

## Findings, highest impact first, with exact README wording fixes

1. **High: the published catalogue verifier cannot pass the current authenticated API.** The exact command in the linked testing guide exits 1 at `AssertionError: ('/api/actuators/764B00-11300000/A', 401)`. Targeted inspection of the linked script after failure shows that its HTTP helper sends Content-Type only, without login or Authorization; it also defaults to port 8000 independently of API_PORT. Its numeric/reference checks and nested 484-test suite passed before this assertion. The first invocation's HTTP result was on port 8000 and must not be counted as clean-server evidence; the explicit-port rerun below resolves that attribution. Do not describe the overall command as passed because its first JSON block says passed. Proposed README text, with the linked testing guide updated consistently:

   > Known verification failure: `python scripts/verify_catalog_db.py` currently fails on protected HTTP endpoints with 401 because it does not authenticate. Its SQL round-trip checks are separate from that failing HTTP stage. For alternate API ports, pass `--base-url http://127.0.0.1:18000`; API_PORT alone does not configure this script. Until its authenticated probes are repaired, use the Python database suite plus the authenticated API walkthrough for reproduction, and retain this verifier failure as pending.

2. **High: the advertised v6 selfcheck is not a passing gate on this release.** The exact linked command reports 21 failures among 103 scenarios, despite the separate Python suite passing. Differences include question IDs, suggestions, expected products, selected tools and expected public wording. This audit does not decide whether each difference is a stale expectation or a behavioral regression. Proposed README text, with Run locally in the testing guide updated consistently:

   > Current clean-checkout evidence: `SERIES76_TEST_DB=1` with `python -m unittest discover -s tests` passes 484 tests with two skips. The historical v6 selfcheck currently passes 82/103 scenarios and exits nonzero; 21 expectation/behavior differences remain to be reconciled. The archived 103/103 result is historical and is not a passing gate for the current release. No scripted result establishes provider interpretation quality.

3. **High: the linked keyless API walkthrough fails at its first product question.** README links the API recipe, and the wiki index explicitly says that complete-code motor-power question is deterministic; the actual clean server returns 503. A new evaluator cannot reproduce that demonstrated conversation. Replace the walkthrough example in both the README/link target with a verified keyless request, or fix the route separately; proposed README text:

   > With no provider key, first send `hola`, then start a new conversation with `Compare 761A00-11300000/A vs 761B00-11300000/A`; both work without inference. The current question `What is the motor power of 761A00-11300000/A?` requires interpretation and returns 503 when keyless. For a keyless individual product, use authenticated `GET /api/actuators/761A00-11300000/A`.

4. **Medium: isolation knobs exist but the README never identifies them.** A second clone defaults to the same Compose project basename and ports, creating a real risk of addressing an existing stack. Port overrides work; project naming works through standard Compose. Add before startup:

   > For an independent second checkout, add `COMPOSE_PROJECT_NAME=serie76-clean`, `POSTGRES_PORT=55432` and `API_PORT=18000` to its `.env` before running Compose. Use `http://localhost:18000` in HTTP examples and `-PbackendUrl=http://10.0.2.2:18000/` for its emulator build. These names and ports isolate this checkout; keep its database password consistent with its own volume.

5. **Medium: the optional bank dry-run is not copyable in the default keyless configuration.** The prose says configure the model but omits the exact assignment; the displayed command errors immediately with the default blank value. Add before the block:

   > The bank is optional for keyless operation. The dry-run still requires a model ID, but no API key and no inference; run the command below to inspect the supplied bank. Leave the second, vector-loading command unrun until paid inference is authorized.

   Replace its first command with the tested command:

   ```text
   docker compose run --rm --no-deps --entrypoint python -e OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2 -v ./config:/app/config:ro backend scripts/load_example_bank.py --dry-run
   ```

6. **Low: Windows prerequisites are stated but not made verifiable/configurable.** JDK 17 was not active and `adb` was missing from PATH, even though the SDK was installed. The build succeeds on this host's JDK 21, so this is an environment/setup gap, not an APK failure. Add:

   > Before building, run `java -version` and confirm the documented JDK, set `JAVA_HOME` to that installation, and set `ANDROID_HOME` to the SDK folder containing `platforms/android-36`. Add `$env:ANDROID_HOME\platform-tools` to PATH before using `adb`; verify with `adb version`. Android Studio can install SDK Platform 36 through SDK Manager. JDK 17 is the documented validation baseline; a successful build on another JDK does not establish that baseline.

7. **Low: the README omits the first OCR weight download, although its linked guide explains it.** Calling extraction local is accurate after provisioning, but a reader expecting a fully offline first execution will fail without cached weights. Add:

   > The first OCR execution downloads public RapidOCR weights into the clone's `.cache/ocr`; recognition then runs locally. Provision those weights before an offline run. A ready export is stored in a per-document subfolder of `data/processed/new-import`.

8. **Low: the environment table is only the new variables, leaving basic startup settings hard to find.** Its six entries are correct; 26 other `.env.example` variables are not in that table. This is a coverage issue, not a default-value mismatch. Add:

   > This table covers the added embedding/debug settings. `.env.example` is the full configuration template: startup uses `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` and `API_PORT`; Compose also accepts `COMPOSE_PROJECT_NAME`. Chat requires `OPENROUTER_API_KEY` and `OPENROUTER_CHAT_MODEL`. Preserve empty credentials for keyless evaluation; advanced retries, deadlines, tracing and evaluation-only variables are commented in that template.

## APK and remaining validation

APK: `mobile/android/app/build/outputs/apk/debug/app-debug.apk`, 12,499,393 bytes.
SHA-256: `C1BA5CDD18570D5202B2ADB690C40C8196530AD70B273CAC91D8F19A90763DE3`.
The default build still targets emulator port 8000; the documented build override is needed for this audit's port 18000. No APK was installed. Device voice, seven-tap behavior, actual per-answer traces and Android/backend integration were checked as documentation only; coordinator/device acceptance remains pending. Provider availability, model quality, OpenRouter compatibility and paid embedding loading were not tested.

Final isolated stack state: `/ready` was still HTTP 200 with 68 rows and 16 terms after tests (`ready-final.txt`). `docker compose -p serie76-clean down` exited 0, removed only the clean backend/DB containers and clean network, and retained `serie76-clean_postgres_data` (confirmed by `docker volume inspect serie76-clean_postgres_data --format '{{.Name}}'`). No `down -v` or volume deletion was run. The clone, APK, ignored environments/OCR output, report and evidence remain available. Git shows only the new report/evidence as untracked; no tracked source edits or commits were made.



### Test database pinning

To prevent inherited shell settings from reaching any other PostgreSQL instance, test commands used these explicit process overrides in the activated backend environment:

```powershell
$env:PGHOST='127.0.0.1'
$env:PGPORT='55432'
$env:PGDATABASE='series76'
$env:PGUSER='series76'
$env:PGPASSWORD='replace-with-local-password'
$env:OPENROUTER_API_KEY=''
$env:OPENROUTER_CHAT_MODEL=''
$env:GOOGLE_API_KEY=''
$env:EMBEDDING_API_KEY=''
$env:LANGSMITH_TRACING='false'
$env:SERIES76_TEST_DB='1'
python -m unittest discover -s tests
```

The password shown is the newly copied public template placeholder, never a pre-existing credential. A psycopg connection check returned database `series76`, PostgreSQL `17.11`, client port `55432` before the suite. The two skipped tests in the backend environment are not counted as successful execution; the separate OCR-environment geometry/safety commands passed above. The suite emitted LangSmith/process-output warnings but exited zero; no configured provider inference was used.



## Verifier isolation deviation and selfcheck failures

The audit initially ran the exact documented `python scripts/verify_catalog_db.py` after pinning every SQL connection to the clean database. This script independently defaults HTTP to `127.0.0.1:8000`; it made read-only GET probes for readiness, health and the first protected actuator there, whose 401 stopped execution. No restart flag was passed, no existing Docker resources were changed, and no authenticated mutation or provider request occurred. This violates the intended HTTP isolation and is disclosed rather than silently attributed to the clean backend. Inspection was restricted to the cloned, README-linked verifier after the failure; no workaround was borrowed from the original checkout. The corrected invocation used explicit `--base-url http://127.0.0.1:18000` and separate output, preserving both attempts. It independently reproduced the same HTTP 401 and exit 1 on the clean backend after its nested 484-test suite passed with two skips in 193.347 seconds. Thus the authentication failure is confirmed on the isolated system, not inferred from the first attempt.

The selfcheck used the clean SQL connection throughout. Its failing IDs are:

```text
vague_application, more_results, h_24v_ac, h4_any_recommendation,
t6_manual_01, t6_manual_02, t6_manual_03, t6_manual_04,
t6_manual_05, t6_manual_06, t6_manual_07, t6_manual_08,
EC02, EC18, EC21, EC24, EC27, EC30, EC33, EC35, EC40
```

Examples: `EC18: suggestions count differs`; `EC21: question ids differ`; `EC27: tool catalogue_superlative != search_actuators`; `EC30: tool document_limitation != ask_clarification`; `EC40: missing text: Not answered: IP67`. The full 103-case output is retained in `t9-clean-evidence/selfcheck.log`. No source code or README was changed to hide or fix these failures.
