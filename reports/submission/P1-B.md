# P1-B — Android resilience and cleanup

Date: 2026-11-05. Scope: `mobile/android/**` and this requested report. No paid inference, backend changes, credentials, catalogue outputs or database volumes were used or changed by this worker.

## Failures corrected

- A failed first send previously entered reconciliation with no way to retry its retained draft. Explicit Retry now works; existing sessions reload before an ambiguous send can be retried. A lost first-turn response displays a duplicate warning and a Check conversations action alongside Retry.
- HTTP 402, 500, 502, 504 and database-unavailable 503 now have distinct, fixed public messages. Client timeouts are distinguished from connectivity failures. Raw error bodies and exception text are never interpolated into these messages. Reading the error code does not consume it before a second classifier needs it.
- Sending retains the exact draft, including surrounding whitespace, until success. Late draft callbacks cannot overwrite a disabled composer. Retry retains structured action/answer/filter arguments; editing the failed text instead submits the new text without stale arguments.
- Retrying a failed later conversation page or earlier history page now keeps the failed offset/cursor and visible items instead of silently refreshing the first page.

## Scenario → behaviour

Every row was exercised for **send, conversation-list load and history load** through `ApiConversationRepository`, real Retrofit/OkHttp and `AppViewModel`. Loading flags remain set while waiting, clear on completion/failure, and feed the existing Compose progress indicators. HTTP work runs outside the ViewModel caller thread. Sending disables the composer; list/history loading leaves draft editing available while history loading disables Send. Failures retain the draft in both state and `SavedStateHandle`.

| Scenario | Public message / waiting behaviour | Recovery |
|---|---|---|
| Real 15 s server body delay | Send: Searching the catalog, then Still working after 8 s; list: Loading conversations; history: Loading messages; successful response clears loading | No duplicate submit; send clears draft only on success; loads preserve it |
| HTTP 500 | The server could not complete the request. Please try again shortly. | Loads: Retry; send: reconciliation policy below |
| HTTP 503 `not_configured` | The assistant is not configured on the server. | Retry after configuration is repaired; no mandatory send reconciliation |
| HTTP 402 `budget_exhausted` | The assistant's service budget has run out. Please contact the administrator and try again later. | Manual Retry after service budget is restored |
| Client read timeout | The server took too long to respond. Please try again shortly. | Loads: Retry; send: reconciliation policy |
| No network / DNS failure | Cannot reach the backend. Check your connection and the backend address. | Retry; failed connection setup does not require send reconciliation |
| Malformed JSON, empty body, missing required fields, JSON null, HTTP 204 | The response could not be loaded. Please try again. | Loads: Retry; send: reconciliation policy |
| HTTP 502 | The assistant's service could not respond. Please try again shortly. | Loads: Retry; send: reconciliation policy |
| HTTP 504 | The assistant's service took too long to respond. Please try again shortly. | Loads: Retry; send: reconciliation policy |
| HTTP 409 | A response is already being prepared. Reload the conversation before sending again. | Reload existing conversation, inspect saved messages, then explicit Retry if still needed |
| HTTP 503 `database_unavailable` | Saved conversations are temporarily unavailable. Please try again shortly. | Loads: Retry; send: reconciliation policy |
| Unknown HTTP status (separate mapper test) | The assistant is unavailable. Check that the backend is running and configured. | Fixed safe fallback, no raw response text |

An ambiguous send means the server may already have saved the turn: 409, server failures, timeout or invalid/lost response. With an existing session, the recovery button first reloads history and never automatically resends; after successful reload it offers Retry. Without a session ID, the UI warns that retry may duplicate a saved first turn and offers Check conversations. Only an explicit Retry submits again. The API has no idempotency token, so manual replay after a lost response cannot guarantee exactly-once delivery. A process-restored first-turn draft also has an explicit recovery path.

## Timeout policy and cleanup

The production client remains at **10 s connect / 70 s read / 75 s total call**, leaving margin above `AGENT_TURN_DEADLINE_S=60`. Connection-failure retry and redirects remain disabled; the existing 5-connection / 30 s pool is unchanged. Tests assert these production values. Timeout integration cases inject a 150 ms read timeout only for the deliberately failing request against MockWebServer `SocketPolicy.NO_RESPONSE`; setup and recovery requests retain production timeouts. These cases do not claim a real 75 s timeout measurement. Offline cases inject `UnknownHostException` inside the OkHttp worker interceptor, without changing the host network.

Removed unused direct dependencies `androidx.compose.material:material-icons-core` and `androidx.compose.ui:ui-tooling-preview`: no imports, icon usages or preview annotations were present. Retained `ui-tooling` for debug inspection and all dependencies used by runtime/test code. Removed an unused local variable from question selection. Source scans found no test `Log.*`, `println`, `System.out` calls or commented-out implementation blocks to delete; explanatory comments remain.

## Validation

Final validation completed on Microsoft OpenJDK 17.0.21.0.2, Android SDK 36:

```powershell
$env:JAVA_HOME='<local-home>\Desktop\T16-evidence\jdk17\jdk-17.0.21.0.2+1'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
java -version
.\mobile\android\gradlew.bat -p mobile/android testDebugUnitTest assembleDebug --no-daemon --max-workers=2
git diff --check -- mobile/android reports/submission/P1-B.md
```

The first run on the default JDK 21 lost its Gradle daemon before results and is not passing evidence. A bounded JDK 21 retry passed 119 tests (74 existing + 45 parameterized scenarios) and assembled debug. The final JDK 17 run passed **126 JVM tests, zero failures/errors/skips** (74 existing + 45 scenario cases + seven recovery-policy tests), and **assembleDebug passed**, exit 0, in 2m 34s. `git diff --check` passed. Existing compiler warnings about the Kotlin `jvmTarget` DSL and SDK XML metadata remain; they did not fail the build.

Evidence is generated under `mobile/android/app/build/test-results/testDebugUnitTest/` and `mobile/android/app/build/outputs/apk/debug/app-debug.apk`; build outputs are intentionally not committed. The two new suites are `ResilienceTest` (45 cases) and `RecoveryStateTest` (seven cases).

The gate validates JVM repository/ViewModel behaviour and APK compilation. Physical-device rendering, accessibility layout, actual radio loss, voice and Android-to-live-backend behaviour were not exercised; no such acceptance is claimed.

## CI timeout-fixture correction

Ubuntu runs `42137036228` and `42137043570` failed the `sessions: timeout` case despite the initial local pass. The old fixture raced a 150 ms read timeout against a successful response body delayed by 500 ms: if the reader was scheduled late enough, the body could already be available. It also imposed the short timeout on setup and recovery requests, making unrelated successful requests sensitive to runner scheduling.

The corrected fixture uses `SocketPolicy.NO_RESPONSE`, so the timeout request can never receive a successful body. An OkHttp interceptor applies the injected 150 ms read timeout only while the target request is deliberately failing; the recovery path uses the unchanged production timeout. All 45 scenario cases and their existing assertions remain, including the exact timeout message, loading state, retained draft and successful explicit Retry. No production source or CI workflow changed.

That first correction passed three forced local gates (126 tests each, 2m 35s / 2m 32s / 2m 29s) but still failed on Ubuntu. Full JVM exception logging was therefore enabled in the Android Gradle build. Run `42140000883`, job `127637657745`, identified the exact failure: **the timeout message assertion passed; the subsequent `assertNull(sessionsError)` failed with the connectivity message after Retry**. A local pass alone did not close this cross-platform failure.

The fixture now binds MockWebServer and its Retrofit URL explicitly to **127.0.0.1**. A hostname such as `localhost` can yield both IPv4 and IPv6 routes; after a connection's first exchange fails, OkHttp can postpone that route and select another address where the single-address server is not listening. Pinning the literal loopback address makes the successful recovery route deterministic while preserving disabled automatic connection retries.

Final repeat validation: **three consecutive JDK 17 executions passed, each with 126 tests, zero failures/errors/skips and assembleDebug successful**, using `:app:cleanTestDebugUnitTest testDebugUnitTest assembleDebug --no-build-cache --no-daemon --max-workers=2`. Durations were **1m 44s / 1m 36s / 1m 36s**. Cleaning only the JVM test results and disabling the build cache forces a new full test execution each time; unchanged compilation tasks can remain up-to-date. Post-push GitHub `android` check verification is recorded in the coordinator handoff.
