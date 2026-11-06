# Series 76 Android

Native Kotlin + Jetpack Compose app. Open this directory in Android Studio with JDK 17 and SDK Platform 36; minimum device API is 26.

From the repository root:

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
```

Default backend: `http://10.0.2.2:8000/` for the Android emulator. Override with `-PbackendUrl=https://your-host/` and rebuild. Debug APK: `app/build/outputs/apk/debug/app-debug.apk`; unsigned release APK: `app/build/outputs/apk/release/app-release-unsigned.apk` (paths relative to this directory).

Sign in to access your saved conversations. The drawer contains history, New chat and your profile. Tap the profile avatar to open Sign out and Appearance (Light, Dark or System); the appearance preference persists. The app retains Rethink Sans, the Konecto background, outlined composer, question review, optional suggestions, catalogue cards and comparison layouts. Tokens remain encrypted and history remains scoped to the authenticated account.

## Voice input

Tap the grey microphone inside the composer, immediately left of Send. On first use, a short explanation precedes Android's microphone permission request. If permission is denied, the composer displays `Microphone permission is needed for voice input` and an **Open settings** button.

While listening, the microphone pulses in the accent colour and an empty composer says `Listening…`. Tap again to stop. Partial recognition updates the draft; final text stays there for review. Voice text is **never sent automatically**. Existing draft text is preserved as a prefix. Typing, leaving the chat, sending, switching conversations or opening debug cancels recognition; callbacks from a cancelled session cannot overwrite subsequent text. The microphone is hidden while sending.

On API 31+, the app prefers `createOnDeviceSpeechRecognizer` when available. Otherwise it uses the device's installed `SpeechRecognizer` service. Language follows the device locale, partial results are enabled, and the fallback requests offline recognition. The fallback service can ignore that preference and use its own network service; this is not a guarantee of offline transcription on every device. No audio is sent to our backend or OpenRouter, and the app requires no speech API key or paid inference integration. See Android's [SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer) and [RecognizerIntent](https://developer.android.com/reference/android/speech/RecognizerIntent) documentation.

Unavailable recognition, no match, network failure and busy service have inline English messages. A stalled session times out after 60 seconds of listening or 15 seconds awaiting the final result. Recognition is cancelled and destroyed when the app pauses or the composable is disposed; it does not run in the background. The app declares `RECORD_AUDIO` and the recognition-service package visibility query.

## Hidden per-answer debug

Open the drawer and tap the **name/email area of the profile card seven times within three seconds**. A toast confirms `Developer mode on`; repeat the gesture to turn it off. This flag persists locally and defaults to off. There is no Developer debug menu item. The avatar still opens the normal profile menu.

Only when developer mode is on, each assistant answer has a small **ⓘ** icon labelled `Debug details`. Tap it to open that answer's bottom sheet. The app lazily requests the existing authenticated `GET /api/messages/{message_id}/debug` endpoint. The backend must have `DEV_DEBUG=true`; HTTP 404 displays `Backend debug is disabled (DEV_DEBUG=false)`. Other failures show a retry action. The gesture is a UI visibility control; backend authentication, ownership and `DEV_DEBUG` remain the access controls.

Collapsible sections show tool names, raw and validated parameters, merged parameters/validation when present, returned data, `latency_ms`, `attempts`, `llm_called`, and optional retrieval examples/similarities/concept scores. Additional model, renderer and context fields are retained when returned. Expand a section to scroll/select its JSON or use **Copy JSON**. Missing raw arguments or metrics stay `null`, rather than being inferred from other data.

Both debug and release variants use this hidden flow. Resumed answers work by their persisted message ID; history does not need to embed debug. No trace is requested simply by loading chat/history or unlocking the mode. When the mode is off, no debug controls or sheet are rendered.

## Verification and limits

[T9 report](../../reports/submission/T9-android.md) records JVM tests, APK builds and outstanding device checks. These local checks do not establish microphone quality, platform permission UI, accessibility rendering or Android-to-real-model acceptance. There are no simulated answers in the shipped app.

SDK, backend, device and authentication setup: [English wiki](../../docs/wiki/en/android.md) · [Spanish wiki](../../docs/wiki/es/android.md) · [Authentication](../../docs/wiki/en/api.md). The voice and hidden-debug instructions above supersede older wiki descriptions until those pages are updated.
