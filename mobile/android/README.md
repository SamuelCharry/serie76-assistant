# Series 76 Android

This is the Kotlin and Jetpack Compose app. Open this folder in Android Studio and use JDK 17 with SDK Platform 36. It runs on API 26 or later.

From the repository root:

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
```

The emulator connects to the backend at `http://10.0.2.2:8000/` by default. To use another server, build with `-PbackendUrl=https://your-host/`.

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`. The unsigned release APK is at `app/build/outputs/apk/release/app-release-unsigned.apk`. Both paths are relative to this folder.

Sign in to see your conversations. The side menu contains your history, New chat and your profile. Tap the avatar to sign out or choose Light, Dark or System appearance; the app remembers that choice. Product cards and comparisons keep the technical data readable without putting it all in a paragraph. Tokens are encrypted, and each account sees only its own history.

## Voice input

Tap the grey microphone inside the composer, immediately left of Send. On first use, a short explanation precedes Android's microphone permission request. If permission is denied, the composer displays `Microphone permission is needed for voice input` and an **Open settings** button.

While listening, the microphone pulses in the accent colour and an empty composer says `Listening…`. Tap again to stop. Partial recognition updates the draft; final text stays there for review. Voice text is **never sent automatically**. Existing draft text is preserved as a prefix. Typing, leaving the chat, sending, switching conversations or opening debug cancels recognition; callbacks from a cancelled session cannot overwrite subsequent text. The microphone is hidden while sending.

On API 31+, the app prefers `createOnDeviceSpeechRecognizer` when available. Otherwise it uses the device's installed `SpeechRecognizer` service. Language follows the device locale, partial results are enabled, and the fallback requests offline recognition. The fallback service can ignore that preference and use its own network service; this is not a guarantee of offline transcription on every device. No audio is sent to our backend or OpenRouter, and the app requires no speech API key or paid inference integration. See Android's [SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer) and [RecognizerIntent](https://developer.android.com/reference/android/speech/RecognizerIntent) documentation.

Unavailable recognition, no match, network failure and busy service have inline English messages. A stalled session times out after 60 seconds of listening or 15 seconds awaiting the final result. Recognition is cancelled and destroyed when the app pauses or the composable is disposed; it does not run in the background. The app declares `RECORD_AUDIO` and the recognition-service package visibility query.

## Hidden per-answer debug

Open the drawer and tap the **name/email area of the profile card seven times within three seconds**. A toast confirms `Developer mode on`; repeat the gesture to turn it off. This flag persists locally and defaults to off. There is no Developer debug menu item. The avatar still opens the normal profile menu.

Only when developer mode is on, each assistant answer has a small **ⓘ** icon labelled `Debug details`. Tap it to open that answer's bottom sheet. The app lazily requests the existing authenticated `GET /api/messages/{message_id}/debug` endpoint. The backend must have `DEV_DEBUG=true`; HTTP 404 displays `Backend debug is disabled (DEV_DEBUG=false)`. Other failures show a retry action. The gesture is a UI visibility control; backend authentication, ownership and `DEV_DEBUG` remain the access controls.

Start with **Tools called**, **Returned data** and **Execution**. They show the operation, its result and whether the model was called (`llm_called`). Raw parameters are the original recorded arguments; validated parameters are the checked version; merged parameters include requirements carried from earlier turns. Context before/after shows how the conversation changed.

The remaining sections include model, renderer and retrieval details when available. Expand a section to inspect the JSON or use **Copy JSON**. Missing values stay `null`; the app does not fill them in from the visible product card.

Both debug and release variants use this hidden flow. Resumed answers work by their persisted message ID; history does not need to embed debug. No trace is requested simply by loading chat/history or unlocking the mode. When the mode is off, no debug controls or sheet are rendered.

## Verification and limits

[T9](../../reports/submission/T9-android.md) records the earlier JVM tests and builds. [P2-D](../../reports/submission/P2-D.md) adds eight emulator checks, and [T18](../../reports/submission/T18-tag-clean-clone.md) records 126 JVM tests and a debug build from the final tag. These cover different parts of the app; they are not a single end-to-end test with a real model.

The author also confirmed real microphone recognition in the emulator on 2026-11-06. That was a manual check without an additional automated artifact. Physical-device behavior, full permission/error coverage and accessibility still need testing. The shipped app does not use simulated answers.

For SDK and backend setup, see the [English guide](../../docs/wiki/en/android.md) or [Spanish guide](../../docs/wiki/es/android.md). The [API guide](../../docs/wiki/en/api.md) explains authentication.
