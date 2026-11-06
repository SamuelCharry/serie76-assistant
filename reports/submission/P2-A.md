# P2-A - Final Flash improvement loop

Status: Phase 2 candidate passes required offline gates; Phase 3 measurement pending. No P2-A lever adopted and no final validation claimed.

## Frozen protocol

- Production: v1, `google/gemini-3.6-flash`, fallback disabled.
- v16 is diagnostic after the initial run; use it for defect classification and lever selection only.
- v17 stays unopened until Phase 4; compare three baseline runs at frozen commit `2f28b71` with three runs of the final candidate.
- Adopt only if mean final pass count is at least baseline, integrity is 1.0 with zero wrong figures, p95 is at most 10 seconds, and every required gate exits zero.
- Rejected P2-A source changes are reverted with Git; preserved catalogue output and PostgreSQL volumes must remain intact.

## Budget

| Item | USD |
|---|---:|
| Initial confirmed key usage | 2.697095241 |
| Hard total key ceiling | 7.60 |
| Phases 1-3 allowance | 1.60 |
| Phases 1-3 absolute stop | 4.297095241 |
| Phase 4 allowance | 2.40 |

Only the authorized scratch wrappers handle provider credentials. The screening runner checks usage before each turn and stops 0.04 USD below its configured ceiling. No provider inference beyond the authorized evaluation is performed.

## Phase 1 evidence

- `git pull --ff-only`: already up to date; source commit `400d5c2` includes `79641bc`.
- Backend rebuilt from that source; active model Flash and fallback empty verified without exposing credentials.
- `sha256sum -c heldout_v16.sha256`: OK, using Git for Windows' SHA-256 executable.
- Offline tool schema: 5,520 bytes, 108 enum values, zero forbidden nodes.
- Baseline retrieval snapshot saved in scratch before changes: 1,956 examples, 200 anchors, two dataset metadata rows; 658 examples use `google/gemini-embedding-2`.
- Run `v16base`: completed; 60 conversations / 131 turns, all HTTP 200, exit 0, 382 seconds wall time.
- Client latency: p95 **6.77 s** (nearest-rank), maximum **12.62 s**, two turns above 10 s.
- Exact spend: **USD 0.338064400**; confirmed total key usage **USD 3.035159641**; phases 1-3 allowance remaining **USD 1.261935600**.
- Recovered **131/131 recorded traces** by message ID using a read-only PostgreSQL transaction with rollback.
- Prepared `blind/pack_v16base_1.md`, `blind/pack_v16base_2.md`, and `blind/pack_v16base_3.md`, 20 conversations each.
- Blind verdicts complete: **34/60 (56.7%)**, partitions **12/20, 13/20, 9/20**, no missing conversations.
- CSV audit checked **2,679 structured values**, zero mismatches; 11 eligibility flags across seven turns plus one invented-filter turn and five layout flags require independent interpretation/adjudication. These flags are not a claim that all are positive-selection violations (one is a clearly disclosed N/A lookup).
- Scratch ledger: `p2a_ledger.json`; metrics: `p2a_v16base_metrics.json`; decisions: `p2a_v16base_recorded_traces.json`.

## Remaining work

Oracle classification and regressions; measured code/bank/prompt levers on v16; paired 3-by-3 v17 validation; final gates, decision, production rebuild and push.

## Phase 2 diagnostic evidence

- [Classification](../agent_acceptance/p2/classification.json): 27 classes (23 code, three interpretation, one existing-contract regression guard), each tied to a recorded message ID and the actual model decision or deterministic route.
- [Oracle scenarios](../../config/agent_acceptance_cases_p2.json): 81 cases, original representative plus two new paraphrases per class. Ideal decisions test deterministic behavior; they do not prove Flash interpretation.
- Initial oracle draft before repairs: **20/81 passed, 61 failed** (including three subsequently corrected numeric-alternative expectations). After repairs: **81/81 passed**; four further tests cover all catalogue identifiers, cross-dimension numeric grounding, ambiguous unitless corrections and range-add/remove lifecycle, for **85/85** total in the P2 suite.
- Oracle fixture correction: the first draft mistakenly expected 20 s at 50 Hz for the two small Explosionproof 220 V models. Independent CSV verification establishes 23 s at 50 Hz and 20 s at 60 Hz; the final oracle expects 23 s. The original baseline omitted the entire requested field, so this correction does not change its failure classification.
- General repairs cover identifier masking, inclusive/range bounds, directional withdrawals, one-dimension elliptical corrections, number-word quantities, categorical grounding/replacement, relative searches, global objective changes, shared presentation counts, explicit equal comparison fields, supported/unsupported request composition and stated unit-count arithmetic.
- Interpretation guidance retains compared codes, searches for published alternatives, uses the supported N/A topic and distinguishes requested booking/certification actions from unrelated document attributes. No per-phrase interpretation rules or new schema enums.
- Tool schema remains **5,520 bytes / 108 enum values**.
- Required full gates remain pending. The first long unittest run was interrupted during diagnosis; a second diagnostic process with recurring faulthandler dumps ended with native Windows status 0xC0000005. The ordinary T14 runner is being used to determine reproducibility; neither interrupted execution counts as a passing gate.

- Existing-contract correction: numeric nearest examples remain in prose/context with explicit failure reasons, excluded from positive recommendation items. The initial P2 oracle incorrectly required recommendation items; that proposed behavior failed three unchanged T10 cases and was discarded. No frozen expectations were edited.
- Targeted regression suites after correction: routes **15/15**, wording **8/8**, short references **2/2**; final P2 oracle **85/85**, all exit zero. A fresh complete gate run is active.

- Subsequent wrapper credit check before further inference: total **USD 3.058293541**, an unattributed shared-key increase of **USD 0.023133900**. No additional P2-A paid run occurred; coordinator notified, and the original absolute ceilings remain unchanged.

## Candidate offline gates

- Required unittest gate: **763 tests**, **0 failures**, **2 skipped**, exit **0**, 430.358 s. Executed through the existing no-environment-file wrapper with `SERIES76_TEST_DB=1`; it captures only PostgreSQL settings and removes provider keys.
- `run_t14_gates.py`: exit **0**; v7 **453/453**, T10 **48/48**, T12 and T14 selfchecks, schema, public text and ranking all exit **0**.
- Public-text audit: **1,060 responses / 32,396 strings**, **0 issues / 0 errors**.
- P2 oracle: **85/85**, exit **0**. Runtime hashes match the passing oracle; no source edits followed it.
- Historical recorded-model replay: **28/45**, exit **1**; the existing runner deliberately excludes this diagnostic from its final exit rule. It is not reported as a passing gate.
- Exact logs, exit codes and source manifest: [candidate gates](../agent_acceptance/p2/gates_code/summary.json). Complete regenerated raw gate outputs are archived as `SCRATCH/p2a_candidate_gates`; historical tracked T14 artifacts are preserved.
