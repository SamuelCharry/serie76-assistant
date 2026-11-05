# T12: oracle-first repairs for Flash v12

Final verification 2026-11-05T20:30:13.189495+00:00; branch release/submission; HEAD `3c1deb5c43196a715671a3f0c601637035913cff` plus the uncommitted source digests in `reports/agent_acceptance/t12_final/code_manifest.json`.

Implemented and locally verified; no inference, no commits, no `.env` reads, no catalogue or PostgreSQL-volume changes. The T11-B files were not edited. v7 and T10 cases remain unchanged, and the default prompt still matches its frozen T10 hash.

## Pre-fix classification

Before backend changes, `reports/agent_acceptance/t12_oracle_pre_fix/report.md` recorded **16 code/contract defects and 0 interpretation-only defects** across the 16 requested V12 conversations; ideal decisions passed **7/47** T12 scenarios, and recorded Flash decisions passed **0/16** original conversations. R22 is one additional code defect. V12-24 and V12-28 also have secondary interpretation errors: removing a corrected bound and removing electrical requirements the user retained. A code failure with an ideal decision takes classification precedence.

The provided results file contains abbreviated debug, so the exact raw decisions were recovered read-only from `series76.messages` using those response message IDs. Replay retains the raw arguments, rather than reconstructing them from answers; deterministic turns bypass the scripted fallback. Baseline and replay evidence are retained under `t12_oracle_pre_fix`.

## Final gates on unchanged code

| Gate | Result | Exit |
|---|---|---|
| Full DB unittest, repo .venv-chat, SERIES76_TEST_DB=1 | 605 run, 603 passed, 2 skipped; 292.764 seconds | 0 |
| v7 frozen scripted cohort | 453/453 scenarios | 0 |
| T10 frozen scripted cohort | 48/48 scenarios, 66/66 turns | 0 |
| T12 oracle | 47/47 scenarios, 87/87 turns | 0 |
| Recorded Flash decision replay | 16/16 conversations, 34/34 turns | 0 |
| check_tool_schemas | 5500 bytes, 108 enum values, 6 arrays, depth 7, zero forbidden nodes | 0 |
| check_public_text, PYTHONPATH=repo root | passed; response scanning also runs per selfcheck turn | 0 |
| git diff --check | passed | 0 |

Schema before/after: **5461 -> 5500 bytes (+39)** and **107 -> 108 enum values (+1)**, within the existing 5522-byte test ceiling and the task's 108-enum ceiling. DC exclusivity is not offered as a model assumption. The two skipped modules are optional OCR/geometry tests requiring `requirements-ingest.lock.txt`, not DB test skips. The new focused regression file contains 22 passing tests, included in the full suite.

## Per-class status

| Class | T12 pass | Status |
|---|---:|---|
| dc_only | 6/6 | fixed and locally verified |
| list | 3/3 | fixed and locally verified |
| negated_hazard | 3/3 | fixed and locally verified |
| supply_overview | 3/3 | fixed and locally verified |
| withdraw_enclosure | 3/3 | fixed and locally verified |
| withdraw_phase | 3/3 | fixed and locally verified |
| correct_range | 3/3 | fixed and locally verified |
| power_objective | 3/3 | fixed and locally verified |
| vac_vdc | 3/3 | fixed and locally verified |
| supply_lookup | 3/3 | fixed and locally verified |
| compound_install | 3/3 | fixed and locally verified |
| compound_stock | 3/3 | fixed and locally verified |
| no_imputation | 3/3 | fixed and locally verified |
| dc_control | 2/2 | fixed and locally verified |
| shared_service | 3/3 | fixed and locally verified |

## Mechanisms

- `dc_only` is an additive boolean requirement enforced by SQL, the independent integrity postcondition, the CSV oracle and saved conversation state. Plain DC still accepts AC/DC; exclusive DC excludes it and states that rule. Empty exclusive searches clear stale choices and explain why no list/comparison/recommendation exists; a fresh search can replace the empty set.
- Explicit withdrawal of an enclosure restriction has no replacement enclosure, even if the user supplies non-hazardous site context. Generic site correction such as "forget explosionproof, it is a normal area" retains the existing T10/v7 weatherproof interpretation. EN/ES regression controls cover both. Withdrawn phase questions stay suppressed until a fresh value is supplied.
- Corrected bounds replace their old direction; added bounds compose with retained limits. Repeating a previously grounded bound in Flash arguments is recognized as carried state rather than rejected as a new unsupported quantity. Explicitly retained requirements cannot be erased by Flash removal arguments.
- Wattage/watts share motor-power grounding, rendering and ranking. Lists of qualified models no longer trigger an accidental duty superlative. VAC/VDC ground supply type, negated hazards cannot produce an affirmative explosionproof explanation, and Spanish supply-type questions return SQL supply facts.
- Independent compound-request limitations cover stock/availability, mounting dimensions and installation while answering supported quantities. Cross-model filling of N/A is explicitly declined; no values are transferred.
- R22 combines confirmed shared torque/duty with one requested service's starts/cycles, matching SQL COALESCE semantics. Specific service values take precedence, rates never come from another service, shared values need provenance confirmation, and strict/missing-value failures remain failures. All seven R22 products now pass independently checked SQL/integrity conditions; a starts threshold of 1201 rejects all seven.

## Oracle maintenance

No v7/T10 expectations were changed. T12 numeric-state comparison normalizes JSON numeric strings; its R22 count assertion checks the full SQL eligibility set and total, not a display page of three/five items. These are scorer corrections: pre-fix R22 still had total zero after integrity rejection, so its baseline diagnosis is unchanged. The existing CSV contract oracle gained the independent DC-only predicate; it does not call production filtering.

## Files changed

- `backend/catalog/models.py`
- `backend/catalog/repository.py`
- `backend/conversation/agent.py`
- `backend/conversation/answer_planner.py`
- `backend/conversation/catalogue_answers.py`
- `backend/conversation/integrity.py`
- `backend/conversation/policy.py`
- `backend/conversation/requirement_coverage.py`
- `backend/conversation/shown_recommendation.py`
- `backend/conversation/tool_wire.py`
- `scripts/acceptance_contract.py`
- `scripts/agent_acceptance.py`
- `config/agent_acceptance_cases_t12.json`
- `config/agent_acceptance_t12.json`
- `scripts/t12_oracle.py`
- `tests/test_t12_regressions.py`

Reports and local reproducer: `reports/agent_acceptance/t12_oracle_pre_fix/report.md`, `reports/agent_acceptance/t12_final/`, `reports/agent_acceptance/run_t12_no_env.py`, and this report. The wrapper retrieves only DB connection fields from the existing backend container into process memory, clears provider credentials, disables embeddings, patches the .env loader before imports and installs a Python audit hook rejecting `.env` access. No secrets are printed.

## Reproduction

```powershell
.venv-chat/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py tests
.venv-chat/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_t12.json --config config/agent_acceptance_t12.json --cohort t12_final
.venv-chat/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py scripts/check_tool_schemas.py
$env:PYTHONPATH=(Get-Location).Path
.venv-chat/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py scripts/check_public_text.py
```

## Risks and pending verification

- v12 is diagnostic material, not a new held-out validation set; successful replay proves code can repair these recorded decisions, not that a new Flash run will interpret unseen requests correctly.
- No paid/provider calls or device integration were run. A newly authored held-out Flash cohort remains externally pending and needs separate inference authorization.
- Deterministic language rules use bounded EN/ES vocabulary. Explicit filter withdrawal versus an affirmative site correction is a deliberate compatibility distinction, documented and tested rather than treated as universally unambiguous language.
- The complete T11-B ranking evaluation was not rerun or overwritten; only its R22 defect was independently verified here. Its R39 ranking-policy disagreement remains outside this task.
- Earlier development gates detected a frozen-prompt hash conflict and a six-byte schema overrun. Both were corrected without changing the frozen prompt or widening budgets; only the all-zero final gates above establish this handoff.
