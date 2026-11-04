# T7 v6 failure review and repair

Review basis: the nine failed scenarios and six provider-only scenarios in the immutable `reports/agent_acceptance/v6/results.jsonl`, the approved T7 contract, the [EC suite](../../docs/evaluation/edge-case-suite.es.md), and the validated CSV. No inference is authorized or performed by this repair. Recorded cohort: 88/103 passed, 9 failed, 6 provider-only; USD 0.1587; latency p50 2.6 s / p95 10.0 s. Those historical verdicts remain unchanged.

## Per-case classification

| Scenario | Classification | Observed decision and outcome | Action |
|---|---|---|---|
| hd_joke | (a) interpretation | `search_actuators({limit:1})` for “Tell me a joke about valves”; empty search asks service/supply | Explicit prompt distinction between catalogue requests and jokes even when they mention valves; live verification still required |
| EC04 | (a) safely intercepted; (c) overstrict expectation | Turn 1 compares A/B; turn 2 resends both codes with LRA focus, but `ambiguous_singular_reference` returns which_product with no products or comparison | Score the required clarification outcome, regardless of selected tool; explicitly reject products or a repeated comparison |
| EC05 | (a) malformed model arguments; (b) missing recovery guard | Raw arguments contain two full codes plus `761A00-11300` and `761B00-11300`; partial-code handling aborts the comparison | Recover only a unique full code explicitly present in the current query; never complete a user prefix from SQL |
| EC30 | (c) overstrict expectation | `ask_clarification(unsupported)` produces the approved price/weighting limitation, but expectation required internal field requirements | Keep limitation assertions and require no products/comparison/interaction; remove the arbitrary field requirement |
| EC33 | (a) neighbouring term selected; (b) relevance guard too broad | `explain_terms(weatherproof)` quotes Weatherproof because generic “general” and “use” overlap its definition; IP67 is still admitted absent | Unknown-rating requests require an explicitly named known term before quoting a related definition; otherwise route to term_not_in_summary |
| EC35 | (a) truncated model argument; (b) missing recovery guard | Raw part number is `761A00-11300` although query contains the full code; limitation is correct but product missing | Same grounded-code guard as EC05; preserve purchase/delivery limitation |
| EC36 | (b) grounding policy | Model correctly supplies on_off, 110 V and torque >= 50 Nm; validation removes service as ungrounded | Add the explicit Spanish full-open/full-close phrase to the service lexicon; prompt still requests a quoted assumption for informal wording |
| EC38 | (b) combined-call normalization | Merged raw terms become `[f,l,a,fla]`; max-three validation rejects the whole factual request | Split comma-separated text by commas, normalize glossary identities and deduplicate before validation |
| EC40 | (a) extra/alias terms; (b) same normalization bug | Merged terms become characters plus fla/lra/duty_cycle/weatherproof; validation rejects all parts | Normalize SQL glossary aliases, retain the three requested known terms, name IP67 as unanswered, render comparison and equal current values |

Here A/B mean the complete catalogue codes `761A00-11300000/A` and `761B00-11300000/A`. All failed turns were reviewed with query, raw/validated arguments, validation/override trace and full answer; the two-turn EC04 includes its successful first turn.

## Why the prefix appeared

The recorded EC05 and EC35 `raw_parameters.part_numbers` already contain the truncated strings before canonical validation and lookup. `codes_in_text` matches the full eight-character suffix plus `/A`; the regression checks it returns exactly A and B for EC05. Neither it nor lookup creates those prefixes. The visible evidence places the bad strings in model-supplied tool arguments; the old trace cannot distinguish the provider from its adapter any further.

The code defect is that one model-only prefix forced the existing partial-code branch even when the user had already written the unique full code. The guard uses only full codes in the current query, records `model_prefix_replaced_from_explicit_code`, and deduplicates the result. An explicit user prefix, unmatched model prefix, or ambiguous prefix still asks for the complete identity. SQL exact lookup/comparison never receives an incomplete code. New traces retain original `model_calls` before multi-call normalization as well as raw and validated parameters.

## Expectation changes, justified before editing

**EC04 turn 2, recorded answer:**

> Which of the previously listed actuators do you mean? Please give its complete part number.

The suite literally requires asking which product without picking one or re-comparing both. The recorded result has empty products and null comparison, satisfying that requirement. A/B are distinct rows in the CSV; nothing resolves the pronoun. Requiring `ask_clarification` and its internal field was an implementation constraint, not the suite criterion. Replace those two checks with clarification=which_product plus no products, no comparison and no interaction options. New negative checks reject both picking a product and re-comparing.

**EC30, recorded answer:**

> The supplied catalogue has no prices. I cannot calculate a weighted overall score involving price; I can compare published torque, operating time, current and motor power.

The EC30 criterion permits limiting the comparison to available magnitudes or asking priorities; it prohibits invented prices and weighted scores. The CSV has no price/ordering/utility-score columns, and this answer supplies no price or score and explicitly refuses a weighted price score. Therefore internal `field=unsupported` is acceptable instead of requirements. Keep the no-prices/weighted limitation assertions and reject products, comparison, clarification and interaction; no numerical expectation changes. Negative checks reject missing limitations and a supplied score. Both changes were approved by the coordinator subject to these exact outcome checks.

## Verification

Initial red run: eight regression tests, six reproduced failures (two failures and four errors); two safety controls already passed. Both expectation regression tests also failed against the old assertions before changes. Final results all exit 0:

```powershell
$env:SERIES76_TEST_DB='1'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
# Ran 212 tests in 29.999s; OK (skipped=2)

.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_t7_live_regressions.py -v
# Ran 8 tests; OK

.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json
# {"selfcheck":"ok","scenarios":103,"failing":[]}

.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_acceptance_v6.py -v
# Ran 6 tests; OK

.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_acceptance_v6_outcomes.py -v
# Ran 2 tests; OK

.venv-model-eval/Scripts/python.exe scripts/check_tool_schemas.py
# {"arrays":6,"bytes":4131,"depth":7,"enum_values":83,"forbidden_nodes":0,"get_actuator_object_arrays":0,"numeric_ranges":0,"required":3}
```

The two skips remain optional OCR/geometry modules. The first full run caught a new trace exposing arbitrary undeclared model fields; an allowlist fixed it and the unchanged privacy regression passed before the final full green run. Existing LangSmith exception-test warnings remain non-failing. The coordinator explicitly approved the standard test helper loading PostgreSQL connection settings internally; no `.env`/`.cache` inspection, key printing, credential extraction from containers or helper patching was performed.

CSV checks confirmed A FLA at 60 Hz = 1.2 A and LRA = 1.4 A; B FLA = 1.3 A and LRA = 1.4 A. A/B On/Off torque is 80/100 Nm. No price/cost/score/weight columns exist. The corpus still contains exactly the same 103 queries; only EC04 turn 2 and EC30 assertions changed.

The backend alone was rebuilt from a shell with model/tracing credential variables removed, using the existing temporary Compose override with explicit empty API keys/models and tracing disabled:

```powershell
docker compose -f docker-compose.yml -f "$env:TEMP/t7-keyless-compose.yml" up -d --build backend
# exit 0; database remained running, backend recreated
Invoke-WebRequest -UseBasicParsing http://localhost:8000/ready
# HTTP 200; status ready; catalog rows 68; context_terms 16
```

No volumes were deleted, no mobile/catalogue/OCR/applied migration files changed, and no paid calls or live preflight ran. `git diff --check` passed; the documentation checker passed 557 links/anchors, zero broken.

One existing test assertion changes from generic “does not define that term” to named “does not define 'IP67'”: the guard now identifies the unsupported rating explicitly. No other historical test expectations are intentionally changed.

Commits: `5c7a389` fixes code grounding, glossary normalization, traces and minimal prompt/tool wording; `02baf60` fixes the two outcome expectations, adds their negative checks and retains original model-call arguments in future acceptance traces. Both carry the required Codex coauthor trailer. This report is committed separately.

Recorded cohort files were not edited or rescored in place; SHA-256 at handoff:

| File | SHA-256 |
|---|---|
| results.jsonl | `4698308cae8c6b52585452897c0acd25f5efecd83f9a5f90ee8595f558e40da9` |
| ledger.jsonl | `7f922044d3875a46d666643caf2e233f45909d37919f02be7cfe944126f2ebd5` |
| summary.json | `34d87eadbe378bb67b24c6ee96b86b5c5e258cf316c925465d33161e0f550a94` |

## Live rerun list

Read from the recorded statuses, not inferred from names:

- Failed: `hd_joke`, `EC04`, `EC05`, `EC30`, `EC33`, `EC35`, `EC36`, `EC38`, `EC40`.
- Provider-only: `exact_noncanonical`, `exact_unknown`, `followup_ambiguous_it`, `h_prompt_leak`, `t6_manual_03`, `EC10`.

The coordinator must run all 15 complete scenarios, including earlier turns in multi-turn cases. Offline scripted checks cannot establish that the prompt changes correct real-model interpretation.
