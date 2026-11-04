# T9-A1 Android: voice input and hidden per-answer debug

Date: 2026-11-04 (America/Bogota). Worktree: `C:\Users\nrir\orca\workspaces\serie76-assistant\t9-android`. Branch: `SamuelCharry/t9-android`, based on `release/submission`. Implementation commits: `9dfc488` (voice) and `3e5afbc` (hidden debug, additional regression tests and Android README).

## Implemented

The composer includes a grey, 48 dp microphone target immediately left of the existing round Send button. It uses the existing typography/theme; `Theme.kt`, `FLAG_SECURE`, the 30-second OkHttp connection pool and disabled POST retries are unchanged. T7/T8 contracts and all 51 pre-existing JVM tests remain intact. No backend, catalogue, OCR or database files were changed; no paid inference, secret access, push or device execution was performed.

| Voice state | UI and behavior |
|---|---|
| Idle | Grey microphone, `Voice input` accessibility label; composer remains editable. |
| Permission rationale | First tap without permission explains that speech becomes reviewable text, then requests `RECORD_AUDIO` only after Continue. |
| Permission denied | `Microphone permission is needed for voice input` and Open settings. The recognizer is not created. Revoked permission is handled as the same state. |
| Listening | Accent microphone with subtle pulse, `Stop listening` accessibility label, `Listening…` placeholder when empty; partial results replace the dictated suffix while preserving the existing draft prefix. |
| Finishing | Second tap stops capture and waits up to 15 seconds for final text; another start is disabled until completion. |
| Final | The draft stays in the composer for explicit review and Send; recognition never submits a conversation request. |
| Unavailable | `Voice input isn't available on this device`. |
| No match / timeout | `Didn't catch that — try again`; partial text remains reviewable. Listening is bounded to 60 seconds. |
| Network | `Voice input couldn't connect — try again`. |
| Busy | `Voice input is busy — try again`. |
| Other platform error | `Voice input stopped — try again`. |
| Cancel / lifecycle | Typing, sending, changing thread, leaving chat, opening debug, Activity pause and composable disposal cancel/destroy recognition. Late callbacks are rejected by a generation guard. Nothing captures audio in the background. |
| Sending | Microphone hidden; existing T8 send/progress behavior retained. |

## README-ready: voice decisions

Tap the microphone inside the composer to dictate, then tap it again to stop. Partial speech appears as editable text. Review the final transcript and press Send yourself: voice input never sends automatically. The first use explains and requests microphone permission; denial shows an inline message with a settings shortcut.

The app prefers Android's `SpeechRecognizer.createOnDeviceSpeechRecognizer` on API 31+ when available, otherwise it uses `createSpeechRecognizer` when the installed recognition service is available. It uses the device locale, enables partial results and requests offline recognition on the fallback. The fallback service may ignore the offline preference and use its own network service, so offline operation is guaranteed only by the on-device recognizer path, not across all devices. No audio is uploaded to this project's backend or OpenRouter, and no speech key or paid inference integration is added. See the official [SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer) and [RecognizerIntent](https://developer.android.com/reference/android/speech/RecognizerIntent) contracts.

The manifest includes `RECORD_AUDIO` and the `android.speech.RecognitionService` package-visibility query. A recognizer is created only for a permitted foreground gesture, and is released after completion/error/cancel and in `onDispose`. Existing typed text is a prefix; interim speech is replaced rather than repeatedly appended. A 4,000-character cap matches the existing composer limit. These choices avoid automatic sends, draft corruption from stale callbacks and unbounded microphone sessions.

## README-ready: hidden debug

Open the drawer and tap the **name/email area of the profile card seven times within three seconds**. A toast says `Developer mode on`; repeat the gesture for `Developer mode off`. The flag defaults to off and persists in local preferences. There is no Developer debug menu entry or unlock hint. Tap the profile avatar to open the existing account/appearance menu; this separate tap target prevents its popup from intercepting the unlock gesture.

With developer mode enabled, every assistant answer has a small 24 dp **ⓘ** control labelled `Debug details`. Tap it for that answer's bottom sheet. Expand sections to see tools called, raw and validated parameters, merged parameters/validation, returned rows/products, `latency_ms`, `attempts`, `llm_called`, and retrieval examples/similarities/concept scores when present. Model, renderer and context fields also appear if provided. Long JSON is vertically scrollable with the sheet, horizontally scrollable within each section, selectable and copyable with Copy JSON. Missing fields stay `null`; the app does not invent or derive debug values from visible catalogue cards.

The sheet lazily calls the existing authenticated `GET /api/messages/{message_id}/debug` endpoint and checks that the returned ID matches the selected answer. Its contract is `{message_id, session_id, tool_calls, debug}`; execution/retrieval fields are read from nested `debug`, with backward compatibility for earlier top-level metrics. Loading is explicit; non-404 failures have Try again. HTTP 404 shows exactly `Backend debug is disabled (DEV_DEBUG=false)`. The endpoint also returns 404 for a missing answer, so the client cannot distinguish those cases from status alone.

Both APK variants now share this hidden flow; obsolete debug-only navigation and the release no-op screen were deleted. When developer mode is off, the icon and sheet are not composed. The unlock is a presentation control, while backend authentication, ownership and `DEV_DEBUG` remain the access controls.

### Resumed conversations

The current history endpoint does not embed traces. The coordinator explicitly directed use of the existing lazy endpoint instead of adding embedded debug or limiting debug to current-session replies. Every resumed assistant message already has a persisted ID, so it can load its saved trace through the same endpoint. This behavior is covered with a synthetic authenticated HTTP fixture; live merged-backend acceptance remains pending. No backend changes are needed in this worktree.

The same instructions are published in [mobile/android/README.md](../../mobile/android/README.md). Root README/wiki updates are outside this worker's allowed scope and remain with the coordinator.

## Initial verification (before the review fix below)

From the repository root:

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease compileDebugAndroidTestKotlin
```

Initial T9 run: exit 0, **BUILD SUCCESSFUL in 1m 48s**. All **69 JVM tests passed, zero failures and errors**: 51 existing tests plus 10 voice tests and 8 developer-debug tests. Both debug and release APKs assembled; release remains unsigned. Instrumentation sources compile, including the adapted per-answer sheet test, but were not executed on a device.

The voice tests use a fake recognizer and cover partial/final text, stop, cancel, stale callbacks after typing/new recognition, permission denial/revocation, unavailable service, errors, empty final results and timeout release. Debug tests cover the seven-tap toggle/reset, sliding timing window and exact boundary, icon gating by mode/role, nested and legacy metrics, raw/validated parameter mapping, retrieval, missing/null values, and the authenticated persisted-answer endpoint. Tests were first run against missing voice/debug contracts and failed, then passed after implementation. `git diff --check` passed. Static review confirmed the retained theme, secure-window flag and connection-pool policy.

| APK path from repository root | SHA-256 |
|---|---|
| `mobile/android/app/build/outputs/apk/debug/app-debug.apk` | `ab8903a69f545524339a8f8ee7abba1844771431185fb802574ae6bde99091a4` |
| `mobile/android/app/build/outputs/apk/release/app-release-unsigned.apk` | `fc81a28a0c01d0b8128d881b0fc31d5ba0673e165232a66a0510aaa61eaabd37` |

## Pending device and integration review

- Exercise recognition with actual installed services/languages, offline and fallback paths, permission denial/settings/revocation, repeated stop/start, rotation and background transitions.
- Review composer spacing, pulse, 48 dp microphone target, hidden unlock, persisted toggle, 24 dp debug control, long JSON scrolling/copying and TalkBack in light/dark mode and enlarged fonts.
- Verify current and resumed answers against the merged backend with `DEV_DEBUG=true/false`, including real retrieval traces. JVM fixtures/builds do not establish device recognition or Android-to-real-LLM acceptance.

No emulator, physical device, live backend or provider was used for these checks.

## Independent-review fix: cancel dictation before conversation reset

The review found that New conversation could clear an unsent draft while its recognizer remained active: `sessionId` stayed `null`, so the previous disposal key did not change. A late partial or final result could therefore restore discarded text. This was a lifecycle bug, not a recognition-quality issue.

The top-bar New conversation and history actions now call `voice.cancel()` before navigation. The composed voice controller also registers a cancellation callback with `AppViewModel`; `newConversation()`, `open(session)` (including reopening the same ID), opening the drawer and clearing the chat ViewModel cancel synchronously, without waiting for recomposition or a changed session ID. The registration is removed at disposal and cannot detach a newer screen's registration. The profile logout action cancels before invoking asynchronous sign-out, so a slow or failed HTTP logout does not leave audio capture running. Auth-driven chat-owner clearing also releases the recognizer.

Three new fake-recognizer ViewModel tests first failed on the unfixed navigation paths: unsent null-to-null reset, same-session open and owner clearing. After the fix, five regressions pass, additionally covering cancellation before logout starts and stale binding disposal. They assert recognizer release, inactive voice state, an empty reset draft and rejection of late recognition callbacks; the null-session test also checks the saved draft. The previous 69 JVM tests still pass, for **74 tests total, zero failures or errors**.

Post-review verification: `./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease` exited 0 with **BUILD SUCCESSFUL in 2m 6s**. `git diff --check` passed. No device, backend or inference calls were used; the device/integration limits above still apply. The APKs below supersede the initial hashes above:

| APK path from repository root | Bytes | SHA-256 |
|---|---:|---|
| `mobile/android/app/build/outputs/apk/debug/app-debug.apk` | 12,784,504 | `98426827f0ee35e939359306fb978330cd932aa773aac5dcea8ed6ce512d96b5` |
| `mobile/android/app/build/outputs/apk/release/app-release-unsigned.apk` | 2,182,633 | `ed8d1d27afb9f40899dc10cacdf04b3107b17ce28a5cc34cf522bd72b7b04d8a` |
