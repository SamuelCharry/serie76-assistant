# T18 — Final-tag clean-clone reproducibility

Executed 2026-11-06 on Windows/PowerShell against a fresh remote clone of **v1.0-submission**, commit `ac56dee476575037037908d2cb4bc8bbd9636a05` (annotated tag object `37b8fcd6f330771fcdf068497da69996b18a501f`). Evaluation used the English README and the API/testing pages it explicitly links. No implementation code or earlier reproduction report was used to supply missing steps.

## Scope and isolation

Clone: `C:\Users\nrir\Desktop\clean-test-tag` (absent before cloning). Compose project `serie76-clean`, PostgreSQL `55432`, API `18000`; fresh volume creation was observed. The existing `serie76-assistant` containers remained on `5432/8000`. A new `.env` was copied from `.env.example`; only the three isolation settings were appended. Both provider credentials were confirmed empty inside the running backend by boolean checks. No paid inference, example-bank vector load, emulator installation, or tag/main modification was performed.

Prerequisites: Git 2.54.0.windows.1, Docker Engine 29.7.2, Python 3.12.10, Microsoft OpenJDK 17.0.21.0.2, SDK Platform 36. JDK 17 was selected from the existing installation at `C:\Users\nrir\Desktop\T16-evidence\jdk17\jdk-17.0.21.0.2+1`; no files from an earlier application checkout or virtual environment were copied. Docker dependency layers, pip downloads and the user Gradle cache were available: this is a clean source/venv/database reproduction, not an empty-machine or cold-cache benchmark.

## Command → result

Commands run from the clone root unless stated otherwise. HTTP examples use the documented alternate port, and `TOKEN` denotes the locally captured login token, never printed. `SID` is the ID returned by the lookup. Shell output was saved locally under `C:\Users\nrir\Desktop\T18-evidence` and summarized below; tokens are absent from the report/logs.

| Step | Command / action | Observed result | Status |
|---|---|---|---|
| 0 | `git clone --branch v1.0-submission https://github.com/SamuelCharry/serie76-assistant C:\Users\nrir\Desktop\clean-test-tag`; `git rev-parse HEAD`; `git status --short` | Clone completed at `ac56dee476575037037908d2cb4bc8bbd9636a05`, clean tree. Git's annotated-tag warning was followed by the expected detached checkout, not a failed clone. | PASS |
| 1a | `Copy-Item .env.example .env`; append `COMPOSE_PROJECT_NAME=serie76-clean`, `POSTGRES_PORT=55432`, `API_PORT=18000` | Independent project configuration; provider key left empty. The same isolation variables were set in the startup process. | PASS |
| 1b | `docker compose up -d --build`; `curl.exe -sS http://localhost:18000/ready` | Build/start exit 0; new `serie76-clean_postgres_data` volume; ready HTTP 200, 68 rows, 16 context terms. | PASS |
| 2 | Use the README's retained processed-data route; `docker compose exec -T backend python -m backend.catalog.cli load data/extracted/series76` | Startup loaded 68 rows; explicit reload returned `already_loaded`, import 1, 68 rows, activated true. Fresh OCR was not required or rerun. | PASS |
| 3 | `docker compose -p serie76-clean logs backend --tail 25` | Startup reported `migrated`, catalogue/glossary loaded, and `Test-only demo users: 2 created; existing accounts unchanged`. | PASS |
| 4 | Write documented demo credentials to `login.json`; `curl.exe -sS http://localhost:18000/api/auth/login -H "Content-Type: application/json" --data-binary "@login.json"` | Login returned a token and user `demo@series76.test`; token held only in memory. | PASS |
| 5a | Write `{"query":"What is the motor power of 761A00-11300000/A?"}` to `query.json`; `curl.exe -sS http://localhost:18000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@query.json"` | Answer: motor power **15 W**, full code and catalogue page 1; session ID returned. | PASS |
| 5b | Same POST with `{"query":"Compare 761A00-11300000/A and 761B00-11300000/A","session_id":"SID"}` | Both complete codes compared; on/off torque 80/100 Nm, modulating torque 65/70 Nm, 10 identical fields hidden. | PASS |
| 6 | Same POST with `{"query":"I need an actuator for an outdoor valve"}` and curl `-w '\nHTTP %{http_code}\n'` | HTTP **503**, `error_code: not_configured`, documented administrator message. | PASS |
| 7 | `curl.exe -sS http://localhost:18000/api/sessions -H "Authorization: Bearer TOKEN"`; GET `/api/sessions/SID/messages` | Test session listed; four chronological messages after lookup/comparison. The completed rerun listed two sessions because the first capture had already created one. | PASS |
| 8 | `docker compose -p serie76-clean restart backend`; wait for `/ready`; repeat messages GET and lookup POST with the same `SID` | Saved four-message JSON identical before/after restart, same token accepted; resumed same session and obtained six messages plus 15 W answer. | PASS |
| 9a | `python -m venv .venv`; `.\.venv\Scripts\Activate.ps1`; `pip install -r requirements-dev.txt` | New Python 3.12 environment; install exit 0. | PASS |
| 9b | `$env:SERIES76_TEST_DB='1'`; `python -m unittest discover -s tests` | Exit 0; **797 tests in 408.039 s**, OK, 2 skipped (795 passed). | PASS |
| 9c | `python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json` | Exit 0; **453/453** scenarios, no failures. | PASS |
| 9d | `python scripts/check_tool_schemas.py` | Exit 0; 5,520 bytes, 108 enum values, 0 forbidden nodes. | PASS |
| 9e | `$env:API_PORT='18000'`; `python scripts/verify_catalog_db.py` | Exit 0; SQL/reference **941/941** primary checks plus 272/272 context checks, internal 797-test unittest stage and authenticated HTTP checks passed; final status `passed`. | PASS |
| 10 | Select JDK 17 with `JAVA_HOME`, set `ANDROID_HOME` and PATH as documented; `java -version`; `Test-Path "$env:ANDROID_HOME\platforms\android-36"`; `adb version`; `./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug` | JDK 17 verified; platform exists; Gradle exit 0, **BUILD SUCCESSFUL in 2m 52s**, 45 tasks executed. JUnit XML: **126 tests, 0 failures, 0 errors, 0 skipped**. APK assembled, not installed. | PASS |
| Cleanup | `docker compose -p serie76-clean down`; attempted exact-path validation and `Remove-Item -LiteralPath ... -Recurse -Force` | Compose down exited 0; only the original stack remained running; clean-project volume retained. Automatic approval review rejected recursive clone deletion as blocked by policy. Per task instructions, the clone remains at `C:\Users\nrir\Desktop\clean-test-tag` for coordinator deletion. | PASS teardown / BLOCKED folder deletion |

For backend tests, `API_PORT=18000` and `POSTGRES_PORT=55432` were set in the process, and inherited `PGHOST`, `PGPORT`, `PGDATABASE` were confirmed absent; the documented local environment helper uses the clone's configuration. Provider keys were empty for this process as well. Only the README's current v7 gates and its linked database-enabled unittest procedure were run; historical gates, paid acceptance and optional OCR regeneration are outside this task.

## Findings and limits

**All ten requested steps passed. No README ambiguity, wrong instruction, missing implementation knowledge, or code defect was found in this bounded route.** The explicit README links supplied API syntax and local-test setup. No documentation repair was needed; S01 is updated solely to add final-tag evidence.

A harness-only interruption occurred on the first persistence capture: Windows PowerShell with `ErrorActionPreference=Stop` treated Docker's normal restart progress on stderr as `NativeCommandError`. The backend restarted successfully; repeating the capture without converting native stderr into a terminating exception completed persistence verification. This preference is not part of the README, so it is not a documentation or product finding. pip's upgrade notice and Gradle's native-library stripping warning were also nonfatal.

No README/source fixes were applied. This evidence branch changes only this report and the S01 evidence row in `docs/SUBMISSION.md`. The immutable submission tag remains unchanged. This run establishes keyless Windows reproduction, not paid interpretation, physical-device behavior, new OCR-layout accuracy, or macOS execution.

## Post-run cleanup status

The cleanup row above records the original test-run outcome. A subsequent read-only check on 2026-11-06 confirmed that `C:\Users\nrir\Desktop\clean-test-tag` no longer exists. Folder cleanup is therefore no longer pending. This update does not claim a new volume or running-service verification.
