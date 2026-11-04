# T7-W2 Android evidence

Date: 2026-11-03, America/Bogota. Worktree branch: `SamuelCharry/t7-android`; starting revision: `706f778`.

Implemented the fixed additive conversation contract in `mobile/android`. No backend, wiki, theme, credentials, catalogue output or database files were changed. No provider inference, push, merge or emulator execution was performed.

## Verification

From `mobile/android`:

```powershell
.\gradlew.bat testDebugUnitTest assembleDebug
```

Final execution: **exit 0, BUILD SUCCESSFUL in 39s**. **40 JVM tests, zero failures, zero errors, zero skipped**. `assembleDebug` succeeded and generated `app/build/outputs/apk/debug/app-debug.apk` (12,682,786 bytes).

APK SHA-256: `651b23ad07820da15921df666dd2b514dc10b19112210ad0d9c9dde700569d1b`.

| JVM suite | Tests |
|---|---:|
| AppearanceTest | 2 |
| AppViewModelTest | 5 |
| AuthViewModelTest | 4 |
| ContractTest | 4 |
| ConversationPresentationTest | 10 |
| InteractionContractTest | 6 |
| InteractionViewModelTest | 5 |
| QualityContractTest | 4 |

JUnit XML: `mobile/android/app/build/test-results/testDebugUnitTest/`. HTML: `mobile/android/app/build/reports/tests/testDebugUnitTest/index.html` (generated, not committed). `git diff --check` passed. Contract and ViewModel tests were first run against missing implementation and failed as expected; targeted checks then passed, followed by the full suite and APK build.

The keep-alive regression uses the production Retrofit/OkHttp factory and a MockWebServer `DISCONNECT_AT_END` response **without** a `Connection: close` header. It asserts that a socket was initially pooled, waits for the real 30-second pool expiry (35-second deadline), confirms zero pooled sockets, then verifies a successful second POST on a fresh connection and exactly two server requests. `retryOnConnectionFailure(false)` is asserted. This verifies client pool expiry and a closed-server-socket scenario; it does not exercise the real deployment's server timeout.

## Screen states and fixtures

These states are implemented in Compose and their data/state behavior is verified on the JVM. This report does **not** claim pixel, emulator, accessibility-device or real-backend visual acceptance; the task explicitly does not depend on an emulator.

| State | Implemented behavior and fixture evidence |
|---|---|
| Question step | Pinned QUESTION card above the composer, bold prompt, full-width radio rows and step count; options advance locally. `ConversationPresentationTest.questions` contains service, voltage and phase; `InteractionViewModelTest.question` uses two questions. The HTTP question fixture in `InteractionContractTest` verifies ordered IDs, prompts, values and labels in both response and saved message. |
| Review/edit/Submit | All question/answer lines are clickable, returning to the selected question and then review. Submit sends exact option values in `answers` plus the label summary (`On/Off · 220 V · 1 phase`). Pure stepper and ViewModel tests verify no request before Submit and no duplicate submission. Single-question behavior is also covered. |
| Cancel/free text | Cancel sends `Cancel` without `answers` and clears the card immediately. The composer remains visible, dims while a question is open, and activates on touch/focus; free-text send drops the local question and sends no partial answers. ViewModel tests verify both paths. Weighted, vertically scrollable card content reserves room for the composer and card actions when the keyboard appears. |
| Suggestions | Quiet dashed chips beneath only the latest assistant message, label `✦ Suggestions · optional`, maximum three and 48 dp touch targets. Pure and ViewModel fixtures verify hiding while typing, after clearing typed text, while sending, and whenever interaction is present. Explicit empty `suggestions` suppresses the deprecated alias; absent suggestions fall back to `suggested_replies`. |
| Active filters | Horizontal removable tags below the app bar, derived from the latest assistant message and hidden when empty. HTTP fixtures contain `110 V`; the ViewModel fixture contains `>= 70 Nm`. Tests verify `remove_filters`, readable query, invalid local-filter rejection and duplicate-send protection. |
| Two-model comparison | `app/src/test/resources/t7/table.json`: summary, muted assumptions, model code split at its suffix, weighted label/value/value columns with no horizontal scroll, exact decimal text, bold better value with orange arrow, and expandable identical row. Tests verify parsed direction and hidden-row selection/toggle. The layout is implemented for 360 dp through bounded weighted columns; pixel fit was not measured on a device. |
| Three/four-model comparison | `app/src/test/resources/t7/cards.json`: summary and one card per model with its four server-selected key fields in a 2x2 grid; this rendering path has no arrows. HTTP parsing/persistence and pure field mapping are tested; the fourth-model test verifies independent values for model D. |
| Product/comparison lead | `ConversationPresentationTest` verifies that `lead` replaces the full answer only when products or comparison are present and falls back to the answer for legacy messages. Existing product and source-note rendering remains in place. |
| Empty greeting | Server account name is read from the existing authenticated `LocalAccount` used by ProfileMenu. The animated greeting uses only the first name and retains its motion/accessibility behavior; JVM fixtures cover `Samuel Charry`, whitespace-separated names, null and blank fallback to `Hello`. |
| Loading/error/history/auth/debug | Existing loading, error/reconciliation, history pagination, authentication and debug screen wiring remain. Existing JVM suites pass, including duplicate-send blocking, preserved failed draft, history restoration and auth expiry behavior. Debug code compiles in the APK; device instrumentation tests were not run. |
| Legacy messages | `QualityContractTest` and `InteractionContractTest` cover absent additive fields and the previous `a`/`b` values and string better-direction format. Legacy comparisons retain their hidden-count footer without inventing unavailable hidden rows. |

All comparison fixtures are explicitly **synthetic test data**, not catalogue evidence. The app displays server-provided values and does not compute or infer catalogue measurements, comparison winners, questions or option facets.

## Changed files

All paths below are relative to `mobile/android/app/src/`, except this report:

- `main/java/com/serie76/assistant/data/Models.kt`: additive DTOs and legacy comparison decoding.
- `main/java/com/serie76/assistant/data/ConversationRepository.kt`: structured request fields and 30-second connection pool.
- `main/java/com/serie76/assistant/ui/AppViewModel.kt`: question, review, dismissal and structured-send integration.
- `main/java/com/serie76/assistant/ui/ConversationPresentation.kt`: pure question state machine, payload and presentation helpers.
- `main/java/com/serie76/assistant/ui/ConversationControls.kt`: question/review, optional suggestions and filter controls.
- `main/java/com/serie76/assistant/ui/ComparisonPresentation.kt`: comparison table, hidden toggle and model cards.
- `main/java/com/serie76/assistant/ui/Screens.kt`: chat placement, composer activation, lead and account greeting wiring.
- `main/java/com/serie76/assistant/ui/MotionText.kt`: animated personalized greeting.
- `test/java/com/serie76/assistant/InteractionContractTest.kt`: MockWebServer contract, history and pool regression checks.
- `test/java/com/serie76/assistant/ConversationPresentationTest.kt`: state machine and presentation logic.
- `test/java/com/serie76/assistant/InteractionViewModelTest.kt`: integrated local selection/send/history state behavior.
- `test/java/com/serie76/assistant/QualityContractTest.kt`: legacy compatibility and new multi-model behavior.
- `test/java/com/serie76/assistant/AppViewModelTest.kt`: repository test-double signature update.
- `androidTest/java/com/serie76/assistant/ScreenTest.kt`: repository test-double signature update only; not executed.
- `test/resources/t7/table.json` and `test/resources/t7/cards.json`: synthetic HTTP fixtures.
- `reports/submission/T7-android.md`: this report at repository root.

## Remaining integration work

Coordinator merges the Android and backend branches and performs any desired device review and real-backend acceptance. The fixed contract is verified with localhost fixtures; backend integration and provider quality are outside this worker's evidence. Theme.kt, app typography and existing app chrome were preserved; new chrome is English.
