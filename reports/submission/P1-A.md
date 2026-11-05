# P1-A: evaluator quick start

Date: 2026-11-05. Branch: `release/submission`.

## Changes

Both README files now put all seven setup steps within the first 23 lines: requirements, environment copy/key setup, Compose startup, readiness URL, two visible TEST ONLY accounts, platform-specific one-line Android build/install and the seven-tap debug gesture. Architecture and assessment history follow the quick start. Existing detailed sections and anchors remain available.

The environment template retains its keyless defaults, empty API keys and local database password placeholder. Comments explain keyless startup, preserving existing configuration, opting into debug and the retained T14 model choice. No runtime defaults changed.

## Verification

| Check | Evidence |
|---|---|
| README structure and seed consistency | Python AST read of `backend/auth/cli.py`: both README files contain all 7 numbered steps and both seed email/password pairs within their first 25 lines |
| Template credentials | All 4 API-key variables empty; database password is the existing local placeholder |
| Compose configuration | `docker compose --env-file .env.example config --quiet`: exit 0; `config --services`: `db`, `backend` |
| Startup sequence | Read `docker/entrypoint.sh`: migrations, retained catalogue, glossary, idempotent demo provisioning, then Uvicorn on port 8000 |
| Readiness and debug | Read `/ready` implementation, `ProfileMenu.kt`, `DebugDetails.kt` and answer debug UI: database readiness and 7 taps within 3000 ms match the instructions |
| Android command | `./mobile/android/gradlew.bat -p mobile/android :app:installDebug -PbackendUrl=http://10.0.2.2:8000/ --dry-run --offline`: exit 0, BUILD SUCCESSFUL; task graph includes packaging and installDebug |
| Android prerequisites | `app/build.gradle.kts`: compileSdk 36, minSdk 26, Java/Kotlin target 17, backendUrl property and debug variant; both wrapper files exist |
| Documentation links | `.venv/Scripts/python.exe scripts/check_docs_links.py`: 819 relative links/anchors checked, 0 broken |
| Whitespace | `git diff --check`: exit 0 |

## Limits

The Gradle dry-run used the host's JDK 21; it proves task/property resolution, not a JDK 17 build or an emulator installation. It reported existing Kotlin jvmTarget deprecation and SDK XML-version warnings. A fresh Docker startup, emulator UI/debug flow and live-provider interpretation were not rerun for this documentation change; the coordinator's clean-clone and Android gates remain separate. No paid inference, private `.env` or credential-cache reads, password resets or database-volume operations were performed. Compose validation explicitly selected the public example file.
