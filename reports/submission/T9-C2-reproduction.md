# T9-C2 — Clean-checkout reproduction repairs

Base: `54a0a83936f7185180ed1ec2c73f8998680e5575`, `release/submission`.
Code and regression tests: `6354364` (`fix(repro): restore authenticated and keyless clean-checkout flows`).

The [original clean-clone audit](T9-clean-test.md) is preserved byte-for-byte, including its historical failures. Its SHA-256 is `29a5c73b039c4ec573d8aac5ab3e38ca7caa6ec59613118c8ccba05899dabb93`. This follow-up records repairs and current local checks; it is not a second clean-OS audit.

## Changes by finding

| Finding | Repair |
|---|---|
| 1. Catalogue verifier HTTP 401 and hardcoded port | Login with the README's public TEST ONLY demo account; pass Bearer authorization to HTTP probes without logging the token. Default URL uses process `API_PORT`, then local `.env` configuration, then 8000; explicit `--base-url` wins. Correct obsolete clarification totals: 55 torque candidates / 14 time candidates, empty products and the appropriate service/frequency question. Counts were independently checked against the validated CSV. Unit checks cover login/body/header/error handling and the default port. Existing passwords remain unchanged. |
| 2. Obsolete v6 gate | Both READMEs and testing guides publish the v7 command with 446 scenarios. The v6 section explains that its presentation expectations predate T8 and no longer pass this release; no v6 cases/configuration were edited. |
| 3. Keyless single-field walkthrough | A conservative closed-request recognizer shares the answer planner's metric vocabulary, requires exactly one complete valid catalogue code and uses the existing lookup/rendering path. Additional intent, conditions, multiple fields or ambiguous scopes fall through. Tests compare answer bytes and products against a scripted LLM decision, with provider construction forbidden on the keyless route. Both API/agent guides retain the exact README motor-power query and explain when keys are required. |
| 4. Second-checkout isolation | Both READMEs and operations/Android guides document `COMPOSE_PROJECT_NAME=serie76-clean`, `POSTGRES_PORT=55432`, `API_PORT=18000`, alternate HTTP URLs and emulator `-PbackendUrl=http://10.0.2.2:18000/`. |
| 5. Model-free bank preview | `--dry-run` without a model previews all 649 examples and 100 anchors without DB, credentials or inference, explicitly identifying `input_only` scope. A configured model retains the DB pending-row check. Documentation identifies the bank as optional keyless and gives the actual load command with `OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2`. No real load was run. |
| 6. Verifiable Android prerequisites | Both READMEs and Android guides show JDK 17 / `JAVA_HOME`, SDK / `ANDROID_HOME`, PATH setup, `java -version`, SDK Platform 36 directory verification and `adb version`, for PowerShell and POSIX shells. No mobile source or machine JDK/SDK configuration was changed. |
| 7. Initial OCR provisioning | Both READMEs and ingestion guides identify first-run public RapidOCR weight downloads into `.cache/ocr` and the ready export/manifest in a per-document folder below `data/processed/new-import`. No OCR output was changed. |
| 8. Environment-table scope | Both READMEs distinguish the added embedding/debug settings from the full `.env.example` template and list startup variables; both operations guides also document Compose project naming. |

The coordinator additionally reported a comparison ending in `Comparing … . 1.`. The pre-existing `finish()` substring cleanup for `0 identical fields hidden` also matched the suffix of `10 identical fields hidden`. A bounded zero-count expression now preserves positive counts, and the SQL comparison test requires the complete `10 identical fields hidden.` sentence.

## Verification

Commands run from the repository root using the existing `.venv-chat` Python 3.12 backend environment. Offline gates explicitly disabled chat credentials, embeddings and LangSmith tracing in their process; database suites used `SERIES76_TEST_DB=1`. Normal CLI connection loading was used without inspecting or printing private configuration.

| Gate | Result |
|---|---|
| Full `python -m unittest discover -s tests`, `SERIES76_TEST_DB=1` | 491 tests, 2 optional OCR module skips, exit 0; standalone run 190.042 s, final-state repeat inside the verifier 200.838 s. |
| New reproduction regressions | 7 tests passed, including byte-identical README/scoped field answers, conservative fallback, HTTP authentication and model-free preview. |
| Comparison presentation regressions | 6 tests passed after the coordinator's added fix. |
| Catalogue regressions | 19 tests passed; clarification checks require retained candidate totals and empty products. |
| `python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json` | 446/446 scenarios, no failures, exit 0. |
| `python scripts/check_tool_schemas.py` | Exit 0: arrays 6, bytes 5487, depth 7, enum values 107, forbidden nodes 0, lookup object arrays 0, numeric ranges 0, required 2. |
| `python scripts/verify_catalog_db.py` on port 8000 | Exit 0: 941/941 primary checks, 68 catalogue rows / 869 numeric values / 4 source-N/A rows, full 491-test suite with 2 skips, and all 9 HTTP checks passed. [Final verifier summary](t9-c2-evidence/catalog-summary.json). |
| Coordinator `start_emb.py on build` | Exit 0; rerun after the comparison fix. `/ready` returned HTTP 200. |
| Model-free bank dry-run, local and rebuilt Docker image | Exit 0: 649 examples + 100 anchors = 749 texts, 24 planned batches; no DB check and no inference. Cost is only an input-byte estimate at the configured unit price. |
| `python scripts/check_docs_links.py` | 723 relative links/anchors checked, 0 broken, including the staged audit, follow-up report and HTTP evidence. |

The first authenticated verifier attempt passed its nested 491-test suite (2 skips, 199.583 s) and then exposed stale zero-total expectations for clarification responses, previously masked by HTTP 401. That failed attempt is retained locally as `verify-before-contract-fix.log`; the final verifier result above covers the corrected contract.

Authenticated [HTTP smoke](t9-c2-evidence/http-smoke.json) on the rebuilt stack returned 200 for all three requests:

| Query | Published answer | HTTP wall time | Agent time |
|---|---|---:|---:|
| `What is the motor power of 761A00-11300000/A?` | 15 W, catalogue page 1, existing motor-power caveat preserved | 106.2 ms | 50 ms |
| `FLA of 761A00-11300000/A at 60 Hz` | 1.2 A, catalogue page 1 | 72.1 ms | 30 ms |
| `operating time of 761A00-11300000/A` | 20 s at 50 Hz; 17 s at 60 Hz, catalogue page 1 | 62.2 ms | 24 ms |

Each stored debug trace reports `llm_called=false`, zero attempts, no retrieved examples/concepts and `embedding_ms=0`. These are single local observations, not a load-test SLA. The coordinator's startup script configures a provider; no inference was invoked. The separate regression tests prove behavior with empty chat configuration.

After the comparison rebuild, the authenticated [comparison smoke](t9-c2-evidence/comparison-smoke.json) for `Compare 761A00-11300000/A vs 761B00-11300000/A` returned HTTP 200 with `Comparing 761A00-11300000/A vs 761B00-11300000/A. 10 identical fields hidden.` and zero LLM/embedding calls (42 ms agent time).

Local ignored logs: `reports/submission/t9-c2-evidence/`; verifier outputs: `reports/postgres/`. No paid calls, push, mobile edits, v6 fixture changes, database-volume deletion or password reset. Real-provider interpretation, device integration, JDK 17 execution and a fresh full clean-clone rerun remain outside this repair's verification scope.
