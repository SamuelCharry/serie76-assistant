# Submission checklist

Brief received Monday 2026-11-02; delivery due within one week (Sunday 2026-11-08) by replying to the assessment email with the GitHub link.

## Done and verified

- [x] Single repository with backend, ingestion pipeline, Android app and processed data (initial delivery: `main`, PR #8; current T8/T9 documentation: `release/submission`).
- [x] Clean clone + empty database: `cp .env.example .env`, `docker compose up --build -d`, `/ready` 200, test-only demo login, idempotent restart.
- [x] Historical GitHub CI passed for the initial delivery. T9 updates the pinned pgvector image and checks; a current remote T9 CI run is not established by the local reports.
- [x] README (EN/ES), wiki (`docs/wiki/`), evidence (`docs/evidence/`), ADR, AI assistant configuration (`.claude/`, `.codex/`).
- [x] No real keys in the repository; `.env` is ignored.

## T8/T9 implemented and locally verified

- [x] T8 questions in one review card, declared recommendations, structured actions, owner-scoped deletion and Undo; [backend](../reports/submission/T8-backend.md), [Android](../reports/submission/T8-android.md).
- [x] T8b–T8h answer planner, quantity/filter integrity checks and contextual repairs; [evidence map](wiki/en/testing.md#current-local-evidence).
- [x] T9 additive interpretation examples, provenance/versioning and exclusions, bounded retrieval and keyless fallback; [484 Python tests, 2 optional skips, 446 scripted scenarios](../reports/submission/T9-embeddings.md).
- [x] Pinned pgvector PG17 trixie; backup, matching glibc/collation and preserved existing data recorded in the T9 report; no volume deletion.
- [x] Voice transcript review and hidden per-answer debug in both APK variants; [74 JVM tests and APK assembly](../reports/submission/T9-android.md). Actual device recognition remains pending.
- [x] README EN/ES and wiki document setup/defaults, Docker/API, ingestion outputs, app/backend URL, seven-tap debug, test users, voice fallback, model choice and trade-offs against assessment section 8.
- [x] Strict behavior rounds disclosed: round 9 **30/41 ON (73%) versus 29/41 OFF (71%)**; round 10 retrieval ON after repairs **28/41 (68%)**. Observed held-out quality is **68–73%**, every response in rounds 9–10 under 10 s (p95 3.7–5.1 s), no wrong catalogue numbers in any round; figures do not establish correct intent/filters.
- [x] Four remaining failure classes and engineer confirmation of active filters, service, enclosure and hazardous-area classification before ordering are disclosed in both READMEs.

- [x] Documentation gates: `python scripts/check_docs_links.py` checked 715 relative links/anchors, zero broken; `git diff --check` passed; README PowerShell and POSIX shell blocks parsed, bilingual commands/results matched. No provider calls, app test reruns or separate macOS/Linux runtime execution in this docs task.

## Pending

- [ ] OpenRouter acceptance with the provided key (issue #2). Readiness: `python scripts/check_openrouter.py`, then a capped cohort with `config/agent_acceptance_openrouter.json` (safety cap USD 1.00).
- [ ] After authorized OpenRouter acceptance, update README status and evidence with that actual provider result; do not relabel Google or scripted evidence.
- [ ] After future behavior changes, repeat a fresh frozen held-out cohort with provenance exclusions and independent strict review; preserve the disclosed round 9–10 results.
- [ ] Verify Android on emulator/device against the merged backend: real voice services/permissions, transcript review, questions/actions/deletion and lazy debug for current/resumed answers with DEV_DEBUG true/false.
- [ ] Confirm fresh-clone reproduction and current remote CI for the final commit; macOS/Linux commands are documented, not executed on a separate host by the docs task.
- [ ] Give the evaluators access: the repository is **private**. Either invite their GitHub accounts (Settings > Collaborators) or make it public.
- [ ] Send the email (below) and close issue #1.

## Email draft

> Subject: Series 76 Technical Assistant - submission
>
> Hello,
>
> Please find my submission here: https://github.com/SamuelCharry/serie76-assistant
>
> The README explains how to run everything locally (`docker compose up --build -d`), the test-only demo users, the Android app and the debug screen. Architecture, decisions and trade-offs are in `docs/wiki/en/`, and verification evidence in `docs/evidence/`.
>
> Summary: a FastAPI backend with a single LangChain tool-calling agent; the LLM only interprets the request, while catalogue values always come from PostgreSQL through typed tools and templates. The electrical PDF is extracted with a local OCR pipeline validated against the source (941/941 checks). The Android app is native Kotlin/Compose with login, saved conversations, reviewable voice input and hidden per-answer developer debug. Optional pgvector retrieval supplies interpretation examples only; technical figures remain SQL-rendered.
>
> I look forward to discussing it.
>
> Best regards,
> Samuel
