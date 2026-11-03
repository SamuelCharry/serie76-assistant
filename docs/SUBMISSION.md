# Submission checklist

Brief received Monday 2026-11-02; delivery due within one week (Sunday 2026-11-08) by replying to the assessment email with the GitHub link.

## Done and verified

- [x] Single repository with backend, ingestion pipeline, Android app and processed data (`main`, PR #8).
- [x] Clean clone + empty database: `cp .env.example .env`, `docker compose up --build -d`, `/ready` 200, test-only demo login, idempotent restart.
- [x] CI green on GitHub (backend tests on PostgreSQL 17, Android unit tests).
- [x] README (EN/ES), wiki (`docs/wiki/`), evidence (`docs/evidence/`), ADR, AI assistant configuration (`.claude/`, `.codex/`).
- [x] No real keys in the repository; `.env` is ignored.

## Pending

- [ ] OpenRouter acceptance with the provided key (issue #2). Readiness: `python scripts/check_openrouter.py`, then a capped cohort with `config/agent_acceptance_openrouter.json` (safety cap USD 1.00).
- [ ] Update the README status table and `docs/evidence/agent_acceptance.md` with the OpenRouter result.
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
> Summary: a FastAPI backend with a single LangChain tool-calling agent; the LLM only interprets the request, while catalogue values always come from PostgreSQL through typed tools and templates. The electrical PDF is extracted with a local OCR pipeline validated against the source (941/941 checks). The Android app is native Kotlin/Compose with login, saved conversations and a developer debug screen.
>
> I look forward to discussing it.
>
> Best regards,
> Samuel
