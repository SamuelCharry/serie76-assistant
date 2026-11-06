# Submission audit

Audited 2026-11-06 on `release/submission` against all six pages of the [assessment](assessment-en.pdf). Documentation/source/evidence review only: no inference, private `.env` read, merge, tag or settings change. Historical reports apply to their recorded source versions.

## Requirement-by-requirement checklist

Checklist totals: **47 items — 37 ✅ / 10 ⚠️**. Each row counts as one obligation, including optional features and delivery. ✅ means implemented/evidenced within the stated scope; ⚠️ means missing or weak acceptance evidence. Local tests do not establish device behavior or generalization.

### Backend and data: sections 1–5

| ID | Requirement | Status and evidence |
|---|---|---|
| B01 | Python REST service with FastAPI | ✅ [Application](../backend/app/main.py), [API map](wiki/en/api.md#endpoint-map). |
| B02 | LangChain agent and custom table-query Tool | ✅ [StructuredTool construction](../backend/conversation/agent.py#L285), `bind_tools` at line 370; [design](wiki/en/agent.md). |
| B03 | Specific retrieval by full Base Part Number | ✅ [T16 steps 5a/5b](../reports/submission/T16-clean-clone.md#command--result): full-code 15 W lookup and comparison from SQL. |
| B04 | Suitable recommendations from requirements | ⚠️ [Ranking](../backend/conversation/ranking.py) implemented; [P1-F scan](../reports/submission/P1-F.md#full-original-v15-scan) found four technical and two shown-set violations, locally repaired; interpretation remains imperfect. |
| B05 | Ingest electrical PDF into tool data | ✅ [Script](../scripts/ingest.py), [pipeline](../catalog_ingest/), [941/941 primary checks](evidence/ocr.md). |
| B06 | Electrical PDF sole numeric authority; summary for context | ✅ [PDF](../data/raw/series_76_electric_data.pdf), [ingestion](wiki/en/ingestion.md), [provenance/reference exclusion](evidence/ocr.md); full codes, units, N/A and notes preserved. |
| B07 | Multi-turn session_id and follow-up references | ✅ [Store](../backend/conversation/store.py), [tests](../tests/test_conversations.py), [T10 48/48 scripted oracle scenarios](../reports/submission/P1-F.md#verification); natural-language limits remain B04/B10. |
| B08 | History survives restart | ✅ [T16 step 8](../reports/submission/T16-clean-clone.md#command--result): history survived and resumed under same session. |
| B09 | Invalid part numbers and missing data | ✅ [Policy tests](../tests/test_agent_policy.py), [scenarios](../tests/test_agent_scenarios.py), [source N/A checks](evidence/ocr.md). |
| B10 | Ambiguity, impossible requirements, unexpected inputs | ⚠️ Clarification/no-match implemented; [v14](../reports/submission/T14-plan-b.md) failed 13/45, [v15 v1](../reports/submission/SV2-experiment.md#paired-held-out-v15-results) failed 18/60 before P1-F; intent, omitted requirements and aggregate scope remain limits. |
| B11 | Fixed POST /api/conversation fields | ✅ [API](wiki/en/api.md#endpoint-map), [contracts](../backend/app/contracts.py): `{query,session_id?}` → `{session_id,answer,...}`. |
| B12 | Omitted ID starts new; supplied ID continues | ✅ [API semantics](wiki/en/api.md#endpoint-map), [T16 steps 5a/7/8](../reports/submission/T16-clean-clone.md#command--result). |
| B13 | App response structure, sessions/history routes | ✅ [T8/T9 contract](wiki/en/api.md#t8t9-contract): products/comparisons/debug; suggested session/history names retained. |
| B14 | OpenRouter models, configurable names, explained choices | ✅ [README models](../README.md#models-design-and-limitations), [.env.example](../.env.example): `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_CHAT_MODEL`, `OPENROUTER_EMBEDDING_MODEL`; Flash single chat model, fallback empty. |
| B15 | USD 10 budget | ✅ [Settled usage](../reports/submission/SV2-experiment.md#paired-held-out-v15-results): USD 2.697095241, about USD 2.70/10; historical, not live balance. |
| B16 | Local PostgreSQL; pgvector for vector search | ✅ [Compose](../docker-compose.yml), [database](wiki/en/database.md), [pgvector](wiki/en/operations.md#pgvector): PG17, additive interpretation retrieval. |
| B17 | Technical numbers match tables, never LLM recall | ⚠️ [OCR](evidence/ocr.md) 941/941; [v15 audit](../reports/submission/SV2-experiment.md#integrity-and-subsequent-p1-f-repair) zero mismatches in 2,050 v1 card fields, but product/context can be wrong; [T15 aggregate repairs](../reports/submission/T15-aggregate-counts.md) are offline evidence. |

### Native app: section 6

| ID | Requirement | Status and evidence |
|---|---|---|
| A01 | Native Kotlin/Compose | ✅ [Build](../mobile/android/app/build.gradle.kts), [Screens.kt](../mobile/android/app/src/main/java/com/serie76/assistant/ui/Screens.kt); [T16](../reports/submission/T16-clean-clone.md#command--result): JDK17 debug build, 74 JVM tests. |
| A02 | Three screens: conversations, chat, debug | ✅ [P2-D emulator acceptance](../reports/submission/P2-D.md): Android 15 conversations/new chat, real keyless card/comparison and seven-tap developer sheet passed; JUnit and UIAutomator XML retained. Debug uses controlled HTTP data; physical-device/visual acceptance remains separate. |
| A03 | List/open saved conversations with context; new chat | ✅ [Repository](../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt), [T8 tests](../reports/submission/T8-android.md). |
| A04 | Chat retains session_id | ✅ [AppViewModel](../mobile/android/app/src/main/java/com/serie76/assistant/ui/AppViewModel.kt), [history contract](wiki/en/api.md#history-and-compatibility). |
| A05 | Clear comparable product data, not paragraphs alone | ✅ [Comparison layout](wiki/en/android.md#t7-questions-suggestions-and-comparisons): cards/tables preserve decimals/notes; device readability remains A02. |
| A06 | No tool names/internal details for end users | ⚠️ Public rendering and hidden debug implemented; [P1-F verification](../reports/submission/P1-F.md#verification) says standalone public-text command is import-only, not an audit. [SV2 leakage](../reports/submission/SV2-experiment.md#offline-evidence-and-failure-mechanism) belongs to rejected experiment. |
| A07 | Debug per answer: tools, parameters, returned data | ✅ [Developer debug](wiki/en/android.md#developer-debug), [API trace contract](wiki/en/api.md#t8t9-contract), [T9 tests](../reports/submission/T9-android.md). |
| A08 | Debug hidden; README explains opening | ✅ [README Android](../README.md#android): seven profile taps in three seconds, answer info icon; DEV_DEBUG, token/ownership required. |
| A09 | Loading/errors on every screen | ⚠️ [P2-D](../reports/submission/P2-D.md): emulator history/chat connection errors, Retry, responsive editing/navigation and 15-second chat loading passed. Login/debug fault paths were not instrumented here; [T9 local coverage](../reports/submission/T9-android.md) remains separate. |

### Optional features: section 7

| ID | Requirement if implemented | Status and evidence |
|---|---|---|
| O01 | Email/password login returns token; hashed passwords | ✅ [Authentication](wiki/en/android.md#authentication), [auth tests](../tests/test_auth.py): salted PBKDF2 and hashed opaque tokens. |
| O02 | Preloaded test users documented | ✅ [README accounts](../README.md#demo-users-test-only), [T16 provisioning/login](../reports/submission/T16-clean-clone.md#command--result); no password resets. |
| O03 | Login screen, Bearer requests, backend identifies user | ✅ [Authentication.kt](../mobile/android/app/src/main/java/com/serie76/assistant/data/Authentication.kt), [API](wiki/en/api.md#endpoint-map); login adds fourth screen. |
| O04 | Users see/use only their conversations | ✅ [Auth tests](../tests/test_auth.py), [ownership](wiki/en/api.md); sign-up/recovery/OAuth not required. |
| O05 | Voice plus text, documented transcription decisions | ⚠️ [P2-D emulator test](../reports/submission/P2-D.md): injected partial/final transcript reaches the composer, late callbacks are ignored and no auto-send occurs. [Voice decisions](wiki/en/android.md#t9-voice) documented; microphone-button/permission integration and actual recognition remain manual checks. |

### Deliverables/submission: sections 3, 8–9

| ID | Requirement | Status and evidence |
|---|---|---|
| D01 | Single GitHub repo, all backend/app source | ✅ [Repository](https://github.com/SamuelCharry/serie76-assistant), [backend](../backend/), [Android](../mobile/android/); access remains S02. |
| D02 | Python, Docker, Android Studio prerequisites | ✅ [Quick start](../README.md#quick-start), [Python environment](wiki/en/testing.md#run-locally), [T16 versions](../reports/submission/T16-clean-clone.md). |
| D03 | Ingestion script/pipeline delivered | ✅ [ingest.py](../scripts/ingest.py), [catalog_ingest](../catalog_ingest/). |
| D04 | Processed data or regeneration instructions | ✅ [Validated data](../data/extracted/series76/), [README ingestion](../README.md#ingestion); Docker load or per-document OCR output. |
| D05 | Dockerfile and compose start backend/database | ✅ [Dockerfile](../Dockerfile), [Compose](../docker-compose.yml), [T16 startup](../reports/submission/T16-clean-clone.md#command--result). |
| D06 | .env.example placeholders without real keys | ✅ [.env.example](../.env.example): empty API/tracing keys, local DB placeholder; private `.env` not read. |
| D07 | README requirements and environment variables | ✅ [Quick start](../README.md#quick-start), [Setup](../README.md#setup-and-backend), [Spanish](../README.es.md#setup-y-backend). |
| D08 | README Docker build/run and API access | ✅ [Setup/backend](../README.md#setup-and-backend), linked [API examples](wiki/en/api.md#curl). |
| D09 | README ingestion command/output location | ✅ [Ingestion](../README.md#ingestion), [Spanish](../README.es.md#ingestión). |
| D10 | README app build/run, backend URL, debug | ✅ [Android](../README.md#android), [Quick start](../README.md#quick-start): JDK17/SDK36, emulator 10.0.2.2, USB reverse, seven taps. |
| D11 | README design/architecture/trade-offs | ✅ [Models/design/limits](../README.md#models-design-and-limitations), [patterns](wiki/en/patterns.md): single decision, SQL, additive retrieval, rejected SV2. |
| D12 | README optional test users/voice decisions | ✅ [Accounts](../README.md#demo-users-test-only), [voice](../README.md#android). |
| D13 | Real assistant configuration directory | ✅ [.claude](../.claude/), [guide](../.claude/README.md), [instructions](../.claude/CLAUDE.md). |
| S01 | Complete reproducible instructions | ✅ [T17](../reports/submission/T17-final-clean-clone.md) reproduced final source `a048489` (P1-F) from GitHub on Windows, fresh isolated DB and empty key: all 10 steps passed, 669 Python tests (667 passed, 2 skipped), v7 453/453, catalogue/HTTP verifier, history/restart and 126 JVM tests/debug build; one API sample corrected. Stack cleaned up; clone folders deferred by policy. Final tag, device and separate macOS/Linux execution remain unverified. |
| S02 | Reply within one week with accessible repo link | ⚠️ Draft below; owner must grant access, merge/tag/send. Brief received 2026-11-02; owner target 2026-11-08. No email/access change here. |
| S03 | Robust beyond supplied examples | ⚠️ [P1-F](../reports/submission/P1-F.md#verification): 669 tests, 1,280 seeded combinations, 108 entry-route calls; [v15](../reports/submission/SV2-experiment.md) remains 42/60 before fixes. Fresh held-out validation pending. |

## Final metrics and open gaps

- **Live:** v14 **32/45**, v15 v1 **42/60**, before P1-F; different cohorts are not causal evidence. [T14](../reports/submission/T14-plan-b.md), [SV2 results](../reports/submission/SV2-experiment.md#paired-held-out-v15-results).
- **Ranking:** NDCG@3 **0.965378**, returned-item compliance **1.0**, 40 synthetic queries / 2,720 judgments, not all live conversations. [P1-F gates](../reports/submission/P1-F.md#verification).
- **P1-F invariant:** final SQL eligibility across cards, comparisons, rankings and positive prose, plus requested shown-set membership; invalid selections clear all channels, informational failures require labels. Checks represented requirements, not perfect interpretation, aggregate scope or installation suitability. [Enforcement](../reports/submission/P1-F.md#final-enforcement).
- **Offline:** 669 tests: 667 passed, 2 skipped; v7 453/453; T10 48/48; T12 47/47; T14 42/42. Historical v13 replay is still 28/45, exit 1, excluded from gate as diagnostic. No new provider run/deployment claim. [Verification](../reports/submission/P1-F.md#verification).
- **Model/spend:** single chat model Flash, `google/gemini-3.6-flash`, fallback disabled; embeddings `google/gemini-embedding-2`. SV2 **not adopted**, 8/60 versus v1 42/60. Settled total **USD 2.697095241**, about **USD 2.70 of 10**, includes experiment. [Evidence](../reports/submission/SV2-experiment.md).

Code/behavior gaps reported without code changes: remaining intent/requirement/aggregate-scope failures; public-text command is import-only, not an independent leakage audit. App state/voice tests do not replace integrated device acceptance. No missing mandatory source artifact identified; three-screen layout interpretation and final-version reproduction remain review risks. Historical reports do not establish current remote CI.

## Final email draft

Reply to the original email only after merge/tag/evaluator access. Branch/tag wording below is conditional until those owner actions finish.

> Hello,
>
> Thank you for the assessment. My submission is at https://github.com/SamuelCharry/serie76-assistant on branch `main`, tagged `v1.0-submission`.
>
> Please start with the README **Quick start**. TEST ONLY accounts: `demo@series76.test` / `Series76-Demo-1` and `reviewer@series76.test` / `Series76-Demo-2`.
>
> Highlights:
> - Local OCR passed 941/941 primary checks; PostgreSQL supplies technical values.
> - The single Flash/LangChain agent scored 32/45 on v14 and 42/60 on v15 before the final integrity repair; interpretation errors remain.
> - Synthetic ranking achieved NDCG@3 0.965 and compliance 1.0, not an end-to-end accuracy guarantee.
> - After the final SQL eligibility repair, 667 Python tests passed with 2 skips, plus 453/453 scripted scenarios; no new post-fix live acceptance is claimed.
> - Native Android includes saved conversations, comparisons, login, hidden debug and reviewable voice; 74 JVM tests and a debug build passed, while integrated device/voice acceptance remains pending in the documented evidence.
>
> Recorded OpenRouter spend was approximately USD 2.70 of USD 10, including the state-v2 experiment, which was not adopted. Reproduction steps, trade-offs and remaining limits are documented.
>
> Best regards,
> Samuel

## Final owner steps

1. **Emulator test:** rebuild backend/app from submission source; test both users, new/resumed chats, comparison, loading/errors, voice permission/service failures, transcript review and hidden debug with DEV_DEBUG true/false. Record results; verify final-source reproduction and CI. Paid flows require budget authorization.
2. **Merge PR #10:** review checks and merge [PR #10](https://github.com/SamuelCharry/serie76-assistant/pull/10) into `main`.
3. **Tag:** create/push `v1.0-submission` at verified merged commit; confirm target.
4. **Evaluator access:** private repository: **Settings → Collaborators**, or make public; verify evaluators can open it.
5. **Send the email:** reply to original assessment; update device results only with evidence and confirm branch/tag exist.
6. **Close issues #1 and #2:** link delivery/acceptance evidence, retaining explicit limitations.

## Documentation validation

Verified with `.venv/Scripts/python.exe scripts/check_docs_links.py`: **960 relative links/anchors, 0 broken**; `git diff --check` passed. Documentation only; no backend/app/OCR/provider suites rerun during this audit.
