# P2-D — Android device acceptance

## Current evidence

**Final selected suite: 8 passed, 0 failed, 0 errors, 0 skipped** on 2026-11-06,
`Series76_API35`, Android 15/API 35, serial `emulator-5554`. JUnit records
106.033 seconds; Gradle completed successfully in 2m 12s (71 actionable tasks).
[Final JUnit](../../mobile/android/app/src/androidTest/evidence/P2-D/final-eight-tests.xml)
and [18 UiAutomator XML + 18 Compose trees](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies)
are committed evidence. All XML parsed successfully; a scan of the artifacts
found no OpenRouter-key, Bearer-token or JSON access-token patterns.

Phase 1 started from `release/submission` at `4c196ee`; the final test run used
the Android source at repository HEAD `e6ed20f` plus this task's test/dependency
changes. Concurrent backend work is not part of this Android acceptance commit.
`mobile/android/gradlew.bat -p mobile/android assembleDebugAndroidTest` **passed**
(52 actionable tasks; 1m 9s) before coordinator approval. No emulator commands
were performed before the explicit Phase 2 GO.

Source: [P2DeviceAcceptanceTest.kt](../../mobile/android/app/src/androidTest/java/com/serie76/assistant/P2DeviceAcceptanceTest.kt).
Only androidTest dependencies were added to the app build: MockWebServer 4.12.0
and UiAutomator 2.3.0. No application source or credentials were changed.

| Test | Boundary | Device result |
| --- | --- | --- |
| `demoLoginConversationsAndNewChat` | Real demo login, real saved-list HTTP/SQL, new empty chat | PASS |
| `keylessProductCardHasFiguresWithoutInternalNames` | Real deterministic single-field lookup; complete code, 15 W, tested internal-name denylist absent, debug icon hidden | PASS |
| `keylessTwoCodeComparisonHasTableWithoutInternalNames` | Real deterministic two-code lookup; three-column table and visible numeric row, tested internal-name denylist absent | PASS |
| `sevenProfileTapsUnlockAnswerToolsParametersAndData` | Real profile gesture and sheet; controlled HTTP answer/trace; six taps insufficient, seven unlock | PASS |
| `closedPortShowsFriendlyErrorRetryAndResponsiveNavigation` | Real refused local socket; history/chat error and Retry; editing/navigation responsive | PASS |
| `fifteenSecondResponseKeepsVisibleLoadingUntilCompletion` | MockWebServer delays body 15 real seconds; initial and prolonged loading, disabled Send, eventual answer | PASS |
| `deleteUndoRestoresConversationWithoutBackendDelete` | Real confirmation/Undo UI and repository transport; no DELETE after original five-second window | PASS |
| `fakeVoiceTranscriptReachesComposerAndNeverAutoSends` | Fake recognizer through production VoiceController/AppViewModel into real ChatScreen composer; partial/final/late callbacks and zero sends | PASS |

## Reproduction

Use emulator-5554 only, with the backend running at `http://10.0.2.2:8000/`.
Select these classes so unrelated historical screenshot tests do not clear
`FLAG_SECURE` or read an old private live-auth configuration:

```powershell
$env:ANDROID_SERIAL = 'emulator-5554'
$env:MSYS_NO_PATHCONV = '1'
.\mobile\android\gradlew.bat -p mobile/android connectedDebugAndroidTest '-Pandroid.testInstrumentationRunnerArguments.class=com.serie76.assistant.P2LiveDeviceAcceptanceTest,com.serie76.assistant.P2ControlledDeviceAcceptanceTest'
```

JUnit output is generated under
`mobile/android/app/build/outputs/androidTest-results/connected/debug/`.
Each checkpoint writes a UiAutomator hierarchy XML using
`UiDevice.dumpWindowHierarchy` and a Compose semantics text file under the app's
cache, then exports through MediaStore into
`/sdcard/Download/Series76-P2-D/run-<timestamp>/`. Public Downloads survive
Gradle's APK uninstallation; app-scoped files do not. This exporter requires
API 29+, while the application's minimum API remains unchanged.
This is hierarchy evidence, not a screenshot;
the host retains `FLAG_SECURE`. Collect these only after execution and record
their final repository paths. The login dump is taken before credentials
are entered. The live bearer uses an in-memory TokenStore and is never logged.

The collected run directory was `run-1793976967204`; `adb pull` recovered 36
files (711,835 bytes). PowerShell used `MSYS_NO_PATHCONV=1` and an explicit
`adb -s emulator-5554` throughout. UiDevice uses the same UIAutomator hierarchy
mechanism without starting a competing shell automation session during a test.

| Surface/checkpoint | XML evidence (same directory also contains its semantics text) |
| --- | --- |
| Login, before credentials | [live-login.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/live-login.xml); two additional captures from the other live tests |
| Conversations | [live-conversations.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/live-conversations.xml) |
| New chat | [live-new-chat.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/live-new-chat.xml) |
| Product card | [live-product-card.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/live-product-card.xml) |
| Comparison table | [live-comparison.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/live-comparison.xml) |
| Developer unlock | [controlled-developer-unlocked.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-developer-unlocked.xml) |
| Debug tools | [controlled-debug-tools.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-debug-tools.xml) |
| Debug parameters | [controlled-debug-parameters.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-debug-parameters.xml) |
| Debug returned data | [controlled-debug-data.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-debug-data.xml) |
| History connection error | [controlled-history-error.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-history-error.xml) |
| Chat connection error | [controlled-chat-error.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-chat-error.xml) |
| Delayed request | [controlled-loading.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-loading.xml) |
| Delayed request completed | [controlled-loading-complete.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-loading-complete.xml) |
| Delete confirmation | [controlled-delete-confirmation.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-delete-confirmation.xml) |
| Undo completed | [controlled-delete-undone.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-delete-undone.xml) |
| Voice transcript awaiting Send | [controlled-voice-review.xml](../../mobile/android/app/src/androidTest/evidence/P2-D/hierarchies/controlled-voice-review.xml) |

## Boundaries and pending checks

- The test host mounts production LoginScreen/AuthViewModel/SeriesApp with the
  real Retrofit repository. It uses isolated in-memory auth instead of reading
  or replacing the user's Android Keystore session; it does not validate
  process recreation or persistent authentication.
- Live queries are allowlisted to `What is the motor power of 761A00-11300000/A?`
  and `Compare 761A00-11300000/A and 761B00-11300000/A`. Source inspection of
  `single_field_code`, `fast_path_codes` and the deterministic branch in
  `backend/conversation/agent.py` establishes their zero-model route for the
  validated catalogue. No general-language, paid, or provider test is included.
- Live cleanup removes only session IDs returned to this test and revokes only
  its own temporary login. Other demo history and existing passwords are preserved.
- Developer sheet transport is controlled. It does not establish the live
  server's `DEV_DEBUG` configuration or real trace authorization.
- Voice injection uses the existing VoiceController constructor seam. The
  actual microphone button's hardwired Android recognizer factory, permission
  dialog, service availability, and real recognition remain manual checks.
- Mock data proves UI/transport behavior, not catalogue correctness. Real-model
  interpretation, physical-device readability and recognition remain pending.
- A02 now records emulator coverage of the three surfaces. A09 records verified
  history/chat connection errors and chat loading; login/debug fault paths were
  not instrumented here and remain a coverage boundary. O05 retains pending
  real-recognition status despite the passing injected-voice test.

## Failed attempts and repairs

1. After GO, the first command found no connected device. No emulator process
   was running, so the existing `Series76_API35` AVD was started headlessly on
   port 5554 without a wipe. No test ran in this first command.
2. The first instrumented attempt stopped during login: signal 9 terminated the
   process and logcat showed an APK update immediately afterwards. No app
   exception was captured; the interruption was reported to the coordinator.
   [Original failed JUnit](../../mobile/android/app/src/androidTest/evidence/P2-D/attempt-1-process-exit.xml)
   is preserved. A concurrent package update is consistent with the log, but
   its origin was not established.
3. The next complete run passed six tests. Delete/Undo and debug failed in
   `dump()` because `onRoot()` expected one Compose root while dialogs exposed
   two. [Original 6/8 JUnit](../../mobile/android/app/src/androidTest/evidence/P2-D/attempt-2-eight-tests.xml)
   is preserved. The helper was corrected to dump every root; functional
   assertions were retained. [Both targeted retests passed](../../mobile/android/app/src/androidTest/evidence/P2-D/attempt-3-dialog-retest.xml).
4. Gradle removed app-scoped evidence when uninstalling the APK. The test-only
   export was moved to public MediaStore Downloads, then the full selected
   suite was rerun: **8/8 passed**, with all 36 artifacts collected after exit.
   No backend-restart retry was needed and no production code was changed.

Final test-source SHA-256:
`CA727E599B4A1662B49AEAB5A88940C7CD036AB955EC27B0BE668123DE548340`.
