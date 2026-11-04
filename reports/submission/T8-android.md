# T8-W2 Android

Date: 2026-11-04 (America/Bogota). Worktree: `C:\Users\nrir\orca\workspaces\serie76-assistant\t8-android`. Branch: `SamuelCharry/t8-android`. Based on `release/submission`; code commit: `82e4407`.

## Implemented slices and screen states

| Slice | Screen state and behavior |
|---|---|
| Questions | One pinned card pages through all questions with `1/N`, option counts, Back/Next, clickable review lines, Submit and Cancel. Selection stays local until Submit sends exact `answers` and a readable label query. The composer remains dimmed and editable. A 422 `empty_combination` restores review and shows its detail inline. |
| Recommendation | A `Ranked by …` block shows at most three server-provided part numbers, reasons and key values, then `Showing 3 of N` using the actual shown count. No catalogue values are computed on the device. |
| Suggestions | The dashed `Suggestions · optional` chips appear only beneath the latest response and hide while typing. Legacy strings send `query`; object suggestions send their label as `query` plus structured `action`. |
| Comparison | Cards for 3+ models use the server's `key_fields`; `key_fields_reason` appears as the subtitle when present. |
| Deletion | Long-press a drawer conversation, confirm, then the row disappears immediately with `Conversation deleted · Undo`. The active DELETE request waits five seconds; Undo cancels only that pending request. Confirming another deletion commits the earlier one immediately. Clearing the ViewModel also commits a pending deletion. Deleting the open session opens a new chat. A failed DELETE restores its row and shows an error. |
| Progress | During a pending send, the chat reads `Searching the catalog…`, switching to `Still working…` after eight seconds. |
| Developer debug | The debug response shows `latency_ms`, `attempts` and `llm_called` when the backend provides them. |

T7 loading, general error, authentication, history, theme/typography, `FLAG_SECURE`, and the 30-second `ConnectionPool(5, 30 s)` with POST retries disabled remain in place. Legacy messages and plain string suggestions still decode. Android uses only synthetic fixtures for this verification; no paid provider call, backend edit, push or device execution was made.

## Verification

From repository root:

```powershell
.\mobile\android\gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
```

Initial T8 run: exit 0, `BUILD SUCCESSFUL in 1m 27s`; **46 JVM tests, zero failures**, plus successful debug and release assembly. Targeted `T8ContractTest` passed before the full run. Tests cover old/new parsing, question navigation/review, action payloads, optimistic delete and Undo timer, delete failure restoration, and inline 422 handling. `git diff --check` passed. JVM tests and APK assembly do not establish emulator rendering or real backend integration.

Follow-up review fix: a new JVM test first failed because confirming a second deletion canceled the first timer and lost its DELETE. The fix moves the previous deletion into a separate completion scope, keeps its ID hidden during the HTTP request, and restores its row only on failure. `ViewModelStore.clear()` commits the pending deletion through that scope. Three added JVM tests cover two deletes with Undo of only the second, ViewModel clearing, and failure of the first DELETE while the second remains undoable. The requested `.\mobile\android\gradlew.bat -p mobile/android testDebugUnitTest assembleDebug` then passed with **49 JVM tests, zero failures**, and `BUILD SUCCESSFUL in 42s`.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `mobile/android/app/build/outputs/apk/debug/app-debug.apk` | 12,475,719 | `9c40c99d2aea3772adbfc55846585298cee2de2c1687125c66216efdf969b139` |
| `mobile/android/app/build/outputs/apk/release/app-release-unsigned.apk` | 2,116,981 | `503040a5f79b3c12f5a22862bbf148e360d314815037b09e37a6f125497672cb` |

Release output is unsigned. Device review and merged backend acceptance remain for the coordinator.
