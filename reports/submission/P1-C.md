# P1-C — evaluator input robustness

## Implemented

- User-written part numbers are resolved against distinct codes in the active PostgreSQL catalogue. Case, spaces, missing/extra presentation separators, an omitted `/A`, and unique prefixes are normalized only to an existing code. The answer and `assumptions` name the original text and the selected full code. A one-character near match requires confirmation; ambiguous prefixes show at most three real candidates. Unmatched identifiers return not found. No measurement is inferred, and source N/A survives normalization.
- Empty, whitespace-only, non-string and NUL-containing messages receive friendly 422 errors. The existing 4,000-character limit now has a friendly `query_too_long` response. Emoji/punctuation produce catalogue-backed questions; bare numbers and the tested SQL/prompt-injection strings receive a safe prompt. Mixed English/Spanish single-field queries can use the deterministic field route.
- Errors use JSON `{detail, error_code}` without exception bodies. Provider 500 maps to 502 `provider_error`; timeout/deadline to 504 `timeout`/`turn_deadline`; provider 402 to 402 `budget_exhausted`; unavailable database to 503 `database_unavailable`; same-session conflict to 409 `session_busy`; exhausted local capacity to 503 `service_busy`. Existing 503 rate-limit behavior is preserved. Database handling also covers authentication, history and catalogue routes.
- Existing PostgreSQL transaction-scoped advisory locks remain the concurrency mechanism. An overlapping request receives 409, writes nothing and can be retried after the first finishes. This is rejection with ordered retry, not a FIFO queue. Provider and persistence failures roll back the whole turn.
- Added `SERIES76_SKIP_DOTENV=1` for explicitly configured offline processes; this bypasses `.env` access before checking the file. No credential or provider configuration was read from `.env` in this run.
- Removed seven unused imports in backend/scripts and the duplicate path that could complete a model-only missing suffix without user grounding. A failed traced turn no longer dereferences a missing result when preparing optional trace output. A 70-file AST audit found no remaining unused-import candidates and no `print`/`breakpoint` calls outside intentional backend CLIs; intentional script output is retained.

## Regression coverage

`tests/test_p1_robustness.py` contains 35 new offline tests. PostgreSQL tests use rollback-only transactions, except the concurrency test, which creates and removes only its own random user/conversation/messages. Provider errors are synthetic OpenAI-compatible exceptions; no paid inference is used.

| Cases | Checked outcome |
|---|---|
| Lowercase, spaces, missing suffix, extra/missing hyphens, unique prefix | Real SQL product, visible assumption, no provider call |
| Normalized N/A row | Original source status and null measurements retained |
| Wrong digit in body/family, ambiguous prefix | At most three real codes, question, no product |
| Unknown full code | Not found, no products, no provider call |
| Empty, whitespace, 4,001 / 5,000 / 20,000 characters, NUL, wrong JSON type | Friendly 422; no conversation DB work |
| 4,000 characters | Accepted at the boundary |
| Emoji, numbers, SQL injection, prompt injection, mixed language | No HTTP 500 or internal exception text; published figures only |
| Provider 500 / timeout / 402 | Expected status and stable code; unchanged persisted history |
| DB connection/authentication failure; failure after message insertion | Friendly 503; no partial new conversation |
| Two concurrent HTTP messages on one session, then retry | One 409; ordered user/assistant pairs; retry sees the committed previous turn |
| Capacity and explicit offline environment | Stable busy error; dotenv access bypassed |

Coordinator-authorized historical test changes:

1. `test_t7_live_regressions.py::test_explicit_user_prefix_with_unique_sql_match_is_resolved_visibly` replaces the former blanket prohibition on completing explicit prefixes. It now asserts unique SQL resolution and a visible full-code assumption. Ambiguous/model-only-prefix rejection tests remain unchanged.
2. `test_reproduction.py::test_multi_field_request_reaches_model_but_unknown_code_is_keyless` retains the multi-field interpretation case and requires unknown codes to return not found without calling the provider.

Frozen v6/v7/T10/T12/T14 expectations were not edited.

## Final verification

The exact `SERIES76_TEST_DB=1 .venv-model-eval\Scripts\python.exe -m unittest discover -s tests` gate exited **0**: **660 run, 658 passed, 2 optional OCR skips**, in 283.113 seconds. The process used explicit local PostgreSQL connection settings, `SERIES76_SKIP_DOTENV=1`, disabled embeddings/tracing and no provider keys. PowerShell wrapped a harmless LangSmith warning as `NativeCommandError`; the process exit and final unittest summary were successful.

The required `.venv-model-eval\Scripts\python.exe reports/agent_acceptance/run_t14_gates.py` gate exited **0** on the same source:

| Required stage | Result | Exit |
|---|---|---:|
| unittest | 660 run, 658 passed, 2 optional OCR skips; 284.497 seconds | 0 |
| v7 | 453/453 | 0 |
| T10 | 48/48 | 0 |
| T12 | 47/47 | 0 |
| T14 | 42/42 | 0 |
| Tool schema | 5,520 bytes; 108 enum values | 0 |
| Public text | Passed | 0 |
| Ranking | 40 queries; NDCG@3 0.965378; returned compliance 1.0 | 0 |

The runner's explicitly non-gating historical replay remains **28/45**, exit 1; this is not a new live-model score and is not claimed as passing. Focused suites passed: P1 35/35, T7 live regressions 12/12, reproduction 7/7, agent scenarios 46/46. The runner-generated artifacts were copied to a local temporary evidence folder before restoring the tracked historical artifacts; only P1-C source, tests and this report are committed.

Local evidence archive: `C:\Users\nrir\AppData\Local\Temp\series76-p1-c-final-9uc68keu` (direct unittest log plus the complete final runner outputs). All 16 changed Python file hashes matched the runner's final code manifest before archival.

Source identity for the 16 changed Python files: SHA-256 of the sorted JSON map from repository-relative path to file SHA-256 is `08f0cb835581e9ee88a233f5e3a2c101a874335e498d203992f2a8e22dfdaf66`. This covers the 11 backend files, two cleanup scripts and three test files; the report is excluded.

No live-provider, device, load-test or deployment result is claimed. The concurrency evidence covers two simultaneous local HTTP requests with independent PostgreSQL connections; the existing capacity limit is per application process.
