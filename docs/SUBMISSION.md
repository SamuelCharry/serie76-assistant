# Submission audit

Audited 2026-11-06 on `release/submission` against all six pages of the [assessment](assessment-en.pdf). Documentation/source/evidence review only: no inference, private `.env` read, merge, tag or settings change. Historical reports apply to their recorded source versions.

## Requirement-by-requirement checklist

Checklist totals: **47 items — 40 ✅ / 7 ⚠️**. Each row counts as one obligation, including optional features and delivery. ✅ means implemented/evidenced within the stated scope; ⚠️ means missing or weak acceptance evidence. Local tests do not establish device behavior or generalization.

### Backend and data: sections 1–5

| ID | Requirement | Status and evidence |
|---|---|---|
| B01 | Python REST service with FastAPI | ✅ [Application](../backend/app/main.py), [API map](wiki/en/api.md#endpoint-map). |
| B02 | LangChain agent and custom table-query Tool | ✅ [LangChain agent and custom tools](../backend/conversation/agent.py), [design](wiki/en/agent.md): one completed decision per interpreted turn; SQL supplies catalogue values. |
| B03 | Specific retrieval by full Base Part Number | ✅ [T16 steps 5a/5b](../reports/submission/T16-clean-clone.md#command--result): full-code 15 W lookup and comparison from SQL. |
| B04 | Suitable recommendations from requirements | ⚠️ [Paired held-out evaluation and repairs (P2-A)](../reports/submission/P2-A.md): improved 47/46/50 of 60, mean 79.4%; adjudicated integrity 429/438 versus 410/438. About 20% of conversations still fail; repaired source has no new paid measurement. |
| B05 | Ingest electrical PDF into tool data | ✅ [Script](../scripts/ingest.py), [pipeline](../catalog_ingest/), [941/941 primary checks](evidence/ocr.md). |
| B06 | Electrical PDF sole numeric authority; summary for context | ✅ [PDF](../data/raw/series_76_electric_data.pdf), [ingestion](wiki/en/ingestion.md), [provenance/reference exclusion](evidence/ocr.md); full codes, units, N/A and notes preserved. |
| B07 | Multi-turn session_id and follow-up references | ✅ [Store](../backend/conversation/store.py), [tests](../tests/test_conversations.py), [T10 48/48 scripted oracle scenarios](../reports/submission/P1-F.md#verification); natural-language limits remain B04/B10. |
| B08 | History survives restart | ✅ [T16 step 8](../reports/submission/T16-clean-clone.md#command--result): history survived and resumed under same session. |
| B09 | Invalid part numbers and missing data | ✅ [Policy tests](../tests/test_agent_policy.py), [scenarios](../tests/test_agent_scenarios.py), [source N/A checks](evidence/ocr.md). |
| B10 | Ambiguity, impossible requirements, unexpected inputs | ⚠️ [Paired v17 evidence (P2-A)](../reports/submission/P2-A.md): 13/14/10 failed conversations per run; clarification and no-match behavior exist, but intent, requirement retention and references remain imperfect. v16 was development data. |
| B11 | Fixed POST /api/conversation fields | ✅ [API](wiki/en/api.md#endpoint-map), [contracts](../backend/app/contracts.py): `{query,session_id?}` → `{session_id,answer,...}`. |
| B12 | Omitted ID starts new; supplied ID continues | ✅ [API semantics](wiki/en/api.md#endpoint-map), [T16 steps 5a/7/8](../reports/submission/T16-clean-clone.md#command--result). |
| B13 | App response structure, sessions/history routes | ✅ [T8/T9 contract](wiki/en/api.md#t8t9-contract): products/comparisons/debug; suggested session/history names retained. |
| B14 | OpenRouter models, configurable names, explained choices | ✅ [README models](../README.md#models-design-and-limitations), [.env.example](../.env.example): `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_CHAT_MODEL`, `OPENROUTER_EMBEDDING_MODEL`; Flash single chat model, fallback empty. |
| B15 | USD 10 budget | ✅ [Settled evaluation usage](../reports/submission/P2-A.md#spend-and-excluded-attempt): USD 6.170259916, approximately USD 6.17 of 10, including failed attempts and experiments; not a live balance. |
| B16 | Local PostgreSQL; pgvector for vector search | ✅ [Compose](../docker-compose.yml), [database](wiki/en/database.md), [pgvector](wiki/en/operations.md#pgvector): PG17, additive interpretation retrieval. |
| B17 | Technical numbers match tables, never LLM recall | ⚠️ [Full v17 structured audit (P2-A)](../reports/submission/P2-A.md): 0 wrong figures in 18,792 values across both versions; improved integrity 429/438. Correct figures can still refer to the wrong product or requirements; offline repairs do not rescore those runs. |

### Native app: section 6

| ID | Requirement | Status and evidence |
|---|---|---|
| A01 | Native Kotlin/Compose | ✅ [Build](../mobile/android/app/build.gradle.kts), [Screens.kt](../mobile/android/app/src/main/java/com/serie76/assistant/ui/Screens.kt); [T16](../reports/submission/T16-clean-clone.md#command--result): JDK17 debug build, 74 JVM tests. |
| A02 | Three screens: conversations, chat, debug | ✅ [P2-D emulator acceptance](../reports/submission/P2-D.md): 8/8 selected tests passed on Android 15, including conversations/new chat, real keyless card/comparison and seven-tap developer sheet passed; JUnit and UIAutomator XML retained. Debug uses controlled HTTP data; physical-device/visual acceptance remains separate. |
| A03 | List/open saved conversations with context; new chat | ✅ [Repository](../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt), [T8 tests](../reports/submission/T8-android.md). |
| A04 | Chat retains session_id | ✅ [AppViewModel](../mobile/android/app/src/main/java/com/serie76/assistant/ui/AppViewModel.kt), [history contract](wiki/en/api.md#history-and-compatibility). |
| A05 | Clear comparable product data, not paragraphs alone | ✅ [Comparison layout](wiki/en/android.md#t7-questions-suggestions-and-comparisons): cards/tables preserve decimals/notes; device readability remains A02. |
| A06 | No tool names/internal details for end users | ✅ [Executable public-text audit (P2-B)](../reports/submission/P2-B.md): 0 detected production leaks in the recorded scope; [emulator cards/comparison](../reports/submission/P2-D.md) also passed. Detector coverage is finite: v17 blind review found a baseline token missed by automation. |
| A07 | Debug per answer: tools, parameters, returned data | ✅ [Developer debug](wiki/en/android.md#developer-debug), [API trace contract](wiki/en/api.md#t8t9-contract), [T9 tests](../reports/submission/T9-android.md). |
| A08 | Debug hidden; README explains opening | ✅ [README Android](../README.md#android): seven profile taps in three seconds, answer info icon; DEV_DEBUG, token/ownership required. |
| A09 | Loading/errors on every screen | ⚠️ [P2-D](../reports/submission/P2-D.md): 8/8 selected emulator tests passed, covering history/chat connection errors, Retry, responsive editing/navigation and 15-second chat loading passed. Login/debug fault paths were not instrumented here; [T9 local coverage](../reports/submission/T9-android.md) remains separate. |

### Optional features: section 7

| ID | Requirement if implemented | Status and evidence |
|---|---|---|
| O01 | Email/password login returns token; hashed passwords | ✅ [Authentication](wiki/en/android.md#authentication), [auth tests](../tests/test_auth.py): salted PBKDF2 and hashed opaque tokens. |
| O02 | Preloaded test users documented | ✅ [README accounts](../README.md#demo-users-test-only), [T16 provisioning/login](../reports/submission/T16-clean-clone.md#command--result); no password resets. |
| O03 | Login screen, Bearer requests, backend identifies user | ✅ [Authentication.kt](../mobile/android/app/src/main/java/com/serie76/assistant/data/Authentication.kt), [API](wiki/en/api.md#endpoint-map); login adds fourth screen. |
| O04 | Users see/use only their conversations | ✅ [Auth tests](../tests/test_auth.py), [ownership](wiki/en/api.md); sign-up/recovery/OAuth not required. |
| O05 | Voice plus text, documented transcription decisions | ⚠️ [P2-D emulator test](../reports/submission/P2-D.md): 8/8 selected tests passed; injected partial/final transcript reaches the composer, late callbacks are ignored and no auto-send occurs. [Voice decisions](wiki/en/android.md#t9-voice) documented; microphone-button/permission integration and actual recognition remain manual checks. |

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
| S01 | Complete reproducible instructions | ✅ [Linux keyless Quick start CI (P2-C)](../reports/submission/P2-C.md) passed on GitHub; [Windows clean clone (T17)](../reports/submission/T17-final-clean-clone.md) passed all 10 steps at its recorded commit, including history/restart and Android JVM/build. These versioned runs do not establish final-tag or macOS execution; verify final-head CI before delivery. |
| S02 | Reply within one week with accessible repo link | ⚠️ Draft below; owner must grant access, merge/tag/send. Brief received 2026-11-02; owner target 2026-11-08. No email/access change here. |
| S03 | Robust beyond supplied examples | ⚠️ [Independent v17 paired evaluation (P2-A)](../reports/submission/P2-A.md): mean 79.4% versus 61.1%, pass^3 71.7% versus 55%, McNemar p=0.013/0.007/0.002. User-authorized adoption is an exception to the pre-registered no-regression rule, not proof it passed; about 20% of novel conversations still fail. |

## Final metrics and open gaps

The owner authorized adoption of the improved single-model version as an **explicit exception to the pre-registered no-regression rule**; the original integrity-1.0 target also failed. The [decision, exact measurements and repair verification](../reports/submission/P2-A.md) distinguish the measured candidate from the later repaired source. The two new regressions and shared relative-bound defects were repaired and regression-tested in `1dda5f2532169fd435012f965689a4a88c075549`. Its final offline checks passed; the paid quality, integrity and latency figures belong only to `3ede96c`. v17 became regression material during those repairs, and the repaired source has no independent paid evaluation.

| Evidence | Result and boundary |
|---|---|
| New held-out v17, three paired runs | Improved **47/46/50 of 60 (79.4% mean)**; previous **37/35/38 (61.1%)**; pass^3 **71.7% vs 55%** means passing all three repeats |
| Paired significance | Exact McNemar **p=0.013, 0.007, 0.002**; same 60 conversations repeated, not 180 independent cases |
| Integrity | **429/438 vs 410/438** turns; **0 wrong figures in 18,792 checked values** across both versions; correct figures do not imply correct requirements or references |
| Latency | Improved pooled client **p95 6.69 s, max 17.89 s, 3 turns >10 s**; previous **6.06 s, 11.23 s, 1 turn >10 s**; the p95 ≤10 s rule passes |
| Earlier evidence | [v14 32/45](../reports/submission/T14-plan-b.md), [v15 42/60 and rejected SV2 8/60](../reports/submission/SV2-experiment.md); v16 used for development, not independent validation |
| Synthetic ranking | [NDCG@3 0.965 / compliance 1.0](../reports/submission/T11-B-ranking.md); not end-to-end accuracy |
| Selection invariant | [Final SQL eligibility across cards, comparison, ranking and positive prose (P1-F)](../reports/submission/P1-F.md); checks represented requirements and requested shown-set membership |
| Public text | [Executable audit (P2-B)](../reports/submission/P2-B.md): 0 detected production leaks in its recorded scope; baseline v17 blind review exposed a missed token |
| Reproduction | [Linux Quick start CI (P2-C)](../reports/submission/P2-C.md) and [Windows clean clone (T17)](../reports/submission/T17-final-clean-clone.md), at their recorded commits |
| Android | [8/8 emulator tests (P2-D)](../reports/submission/P2-D.md); real keyless routes plus controlled fault/debug/voice input, not real recognition |
| Final offline repair checks | [Repaired source delivery](../reports/submission/P2-A.md#repaired-source-delivery): **797 tests (795 passed, 2 skipped)**; expanded oracle **119/119**; v7 **453/453**, T10 **48/48**, T12 **47/47**, T14 **42/42**; schema **108 enums / 5,520 bytes**; public text and ranking exit 0 |
| Models and spend | Chat `google/gemini-3.6-flash`, no fallback; embeddings `google/gemini-embedding-2`; settled **USD 6.170259916 ≈ USD 6.17 of 10** |

About **20% of novel multi-turn conversations still fail** on average. Two new regressions (withdrawn torque ceiling and second comparison member), plus two shared relative-bound defects, are fixed with tests in the repaired source, separately from the measured candidate. Earlier slow-turn diagnosis found single provider calls rather than application loops; it does not identify the cause of each v17 tail. Historical recorded-model replay remains diagnostic at 28/45, exit 1, and is not a passing required gate.

Remaining checklist warnings are **B04, B10, B17 and S03** (selection/interpretation quality and integrity are imperfect), **A09** (login/debug fault coverage), **O05** (manual voice recognition check), and **S02** (owner delivery actions). No missing mandatory source artifact was identified; partial evidence does not establish universal acceptance.

## Final email draft

Reply to the original email only after merge/tag/evaluator access. Branch/tag wording below is conditional until those owner actions finish.

> Hello,
>
> Thank you for the assessment. My submission is at https://github.com/SamuelCharry/serie76-assistant on branch `main`, tagged `v1.0-submission`.
>
> Please start with the README **Quick start**. TEST ONLY accounts: `demo@series76.test` / `Series76-Demo-1` and `reviewer@series76.test` / `Series76-Demo-2`.
>
> Local OCR passed 941/941 primary checks. Before the final offline repairs, the single-model assistant averaged 79.4% versus 61.1% in three paired runs on 60 unseen multi-turn conversations, with no wrong figures among 18,792 checked values; roughly 20% of conversations still failed. Adoption was an explicit exception to the original no-regression rule, with subsequent repairs passing 797 tests (two skipped) and a 119-case oracle; the repaired source has no new paid score. Synthetic ranking reached NDCG@3 0.965 and compliance 1.0.
>
> Linux keyless Quick start, Windows clean-clone reproduction and 8/8 Android emulator checks passed in the documented runs. Real voice recognition still needs a manual check. Improved-version client latency was p95 6.69 s, with three turns over 10 s. Recorded OpenRouter spend was approximately USD 6.17 of USD 10.
>
> The repository documents reproduction steps, trade-offs, repair evidence and remaining limitations.
>
> Best regards,
> Samuel

## Final owner steps

1. **Verify the delivery commit:** confirm the final repair evidence and required CI checks at the intended commit; distinguish measured v17 source from later offline fixes. Recorded Linux/Windows runs predate final delivery. Manually check microphone permissions/service, real transcript review and Send, login/debug loading/errors and physical-device readability; injected voice is not recognition evidence.
2. **Merge PR #10:** review checks and merge [PR #10](https://github.com/SamuelCharry/serie76-assistant/pull/10) into `main`.
3. **Tag:** create/push `v1.0-submission` at verified merged commit; confirm target.
4. **Evaluator access:** private repository: **Settings → Collaborators**, or make public; verify evaluators can open it.
5. **Send the email:** reply to original assessment; update device results only with evidence and confirm branch/tag exist.
6. **Close issues #1 and #2:** link delivery/acceptance evidence, retaining explicit limitations.

## Documentation validation

Final checks: **1,030 relative links/anchors, 0 broken** with the repository `.venv`; the public-text audit completed through the no-env wrapper in `.venv-chat`: **1,060 responses / 32,236 strings, 0 issues, 0 errors**, exit 0. The initial `.venv` public-text attempt failed with four missing-dependency errors and is not counted as a pass. The final repair report independently records the same passing public-text totals on source `1dda5f2`.

Documentation cleanup inventoried 85 tracked Markdown files, removed the obsolete `.codex/README.md`, consolidated duplicated summaries and retained cited historical evidence. Local path prefixes were neutralized in 13 historical Markdown reports. By coordinator authorization, only the local-home path prefix was redacted in four JSON records: `docs/evidence/data/ocr-summary.json`, `reports/submission/T2-ocr-summary.json`, `reports/submission/p1e-evidence/verification.json` and `reports/submission/t9-r1-evidence/gates.json`; valid JSON and all other values were verified unchanged. P2-A is maintained separately by its owner.

 No inference, `.env` read, code/config/test modification, merge, tag or repository-settings change is part of this documentation task.
