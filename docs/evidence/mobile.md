# Android verification

The archived auth-v7 record reports 14 JVM tests and 15 Compose tests: 29 distinct cases with no errors or skips. One additional native live test with two accounts made 30 distinct Android cases. Debug and unsigned release APKs built; emulator verification used Android 15/API 35. The HTTP checks covered user isolation and token/history persistence across backend restart using controlled interpretation.

T1 later recorded 15 JVM tests, failures=0, errors=0, skipped=0, and successful debug/release builds. These are separate verification snapshots, not additive unique coverage.

Reproduce from `mobile/android`: `gradlew.bat testDebugUnitTest assembleDebug`. Instrumented checks require an emulator: `gradlew.bat connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest`. The live auth helper is `scripts/verify_android_auth.py`; see [AUTH](../AUTH.md) for prerequisites.

No real OpenRouter or Android-to-real-LLM acceptance is established by these tests. No physical-device or public HTTPS deployment claim is made.

[Exact auth-v7 test list](data/android-tests.json). [Original archive](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/mobile/auth-v7). [T1](../../reports/submission/T1.md).
