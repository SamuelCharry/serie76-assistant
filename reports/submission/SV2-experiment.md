# SV2 experiment: complete conversation state

**Decision: not adopted.** Production v1 passed **42/60 (70%)** frozen v15 conversations; v2 passed **8/60 (13.3%)**. Discordants were **35 for v1 / 1 for v2**, exact two-sided McNemar **p = 1.076841726899147e-9** (approximately 1.1e-9, not zero). v1 remains the release design; [exp/state-v2](https://github.com/SamuelCharry/serie76-assistant/tree/exp/state-v2) preserves the experiment.

## Hypothesis and design

The hypothesis was that letting the model emit the complete next structured state would improve generalization by removing deterministic delta-merging and lexical rules that could override or drop an interpretation. One `set_conversation_state` decision supplied filters, ordered priorities, references, unsupported requests, pending question and site hazard. Omission removed a requirement; code validated the proposal atomically, resolved references against SQL and rendered catalogue facts through templates. Invalid proposals retained the previous state instead of partially applying it.

v2 bypassed v1 intent fast paths, state repair/merge rules and semantic field insertion. Its wire schema shrank from **5,520 bytes / 108 enum values** to **1,509 bytes / 6 enums**. Legal string values still required prompt guidance and application validation: a smaller wire schema did not remove semantic complexity. See the [pre-implementation design](https://github.com/SamuelCharry/serie76-assistant/blob/exp/state-v2/docs/design/state-v2.md) and [implementation report](https://github.com/SamuelCharry/serie76-assistant/blob/exp/state-v2/reports/submission/SV2-implementation.md).

## Pre-registered adoption rule

The coordinator's local plan `<local-home>/.claude/plans/evaluator-experience-p1.md`, section “Experimento paralelo SV2”, dated 2026-11-06, records this rule. The coordinator confirmed it was written before v15 existed and before the A/B run (Orca message `msg_fb0f35dd9d69`). Adoption into `release/submission` required **all** of:

1. v2 passes at least **v1 + 5 conversations** on v15, **or** McNemar p < 0.05 **in v2's favour**.
2. Zero integrity regressions: returned compliance 1.0 and no wrong figures.
3. Client p95 ≤ 10 seconds.
4. All offline suites green in both v1 and v2 modes.
5. Decision before Saturday **2026-11-07 at 18:00**.

Otherwise v2 stays a documented experiment on its branch. The quality condition failed decisively; v2 also failed the offline v7 target. A small p-value favouring v1 is evidence against adoption, not satisfaction of condition 1.

## Paired held-out v15 results

The frozen cohort contained **60 conversations / 131 HTTP turns**. v1 was `503d25e8ec04ad4478d76f87ad60e06d2709b1d1`; v2 was `c8821bc4eb1d647b5475461c76fbde9325f7c593`. Both used `google/gemini-3.6-flash`, disabled fallback and matching embedding/retrieval settings. Catalogue hashes and ordered retrieval-table checksums matched. Frozen dataset SHA-256 `975faf22a484a7fdb10257c68770186d0b1c932c1a2c8bbce932dd179179f1c0` was checked before and after execution.

| Measure | v1 | v2 |
|---|---:|---:|
| Strict conversation passes | 42/60 (70%) | 8/60 (13.3%) |
| LLM turns | 95 | 131 |
| LLM-turn client p50 | 2.86 s | 2.89 s |
| LLM-turn client p95 | 5.11 s | 6.25 s |
| All-HTTP-turn client p95 | 4.59 s | 6.25 s |
| Maximum, all turns | 6.60 s | 7.98 s |
| Turns over 10 s / HTTP errors | 0 / 0 | 0 / 0 |
| Cohort spend, including embeddings | USD 0.320116950 (≈ 0.32) | USD 0.455383500 (≈ 0.46) |

Both passed 7 conversations, only v1 passed 35, only v2 passed 1, and both failed 17. The v2−v1 difference was **−56.67 percentage points**, paired bootstrap interval **[−70.0, −43.33]**. The v2 preflight cost USD 0.002072250; total task spend was **USD 0.777572700**, settled key usage **USD 2.697095241**. These are historical usage deltas, not price forecasts. Client latency excludes the external budget check before each request; runs were sequential, v1 then v2, not repeated performance trials.

## Offline evidence and failure mechanism

v2 passed the **137/137 T10/T12/T14 oracle scenarios**, but frozen v7 was **353/453 (77.92%)**, below the 95% target. Of its 100 failures, 7 were intentional contract differences, 36 presentation/question-format differences and **57 genuine regressions**. Classification did not waive any failed expectation. The experiment runner correctly exited 1. Ideal scripted full-state decisions prove execution under those inputs, not natural-language interpretation.

Live v2 produced validation responses in **93/131 turns across 50/60 conversations**. A direct user-facing text scan found literal internal `state.` or `view.` paths in **51 turns across 37 conversations**. Blind verdict reasons tagged interpretation and usefulness failures in 43 conversations each; tags overlap and are not exhaustive. Provider preflight acceptance had established schema transport compatibility, not that useful proposals would pass application validation.

**Lesson:** strict validation that mostly rejects instead of recovering safely or asking a useful question can preserve a narrow invariant while destroying task completion. Internal validation paths must not become user-facing explanations. v2 spent more and answered less despite its smaller schema; this rejects the evaluated implementation, not every possible complete-state architecture.

## Integrity and subsequent P1-F repair

The full-card audit checked **2,050 fields on 169 v1 cards** and **1,540 fields on 64 v2 cards**, with zero mismatches against the preserved catalogue CSV. This is not zero end-to-end integrity failures: correct catalogue values can still belong to an ineligible product or wrong context. v2 also answered at 60 Hz after a correction to 50 Hz (18 s instead of the applicable 21 s). Its lower product exposure cannot establish stronger semantic integrity.

The subsequent [P1-F audit and repair](P1-F.md) found **four unlabelled technical violations** in original v1 v15: L1-01/3, L4-04/2, L7-01/2 and L7-01/3, plus **two shown-set violations** (L7-03/3, L7-05/4). P1-F adds a final SQL eligibility check across cards, comparisons, rankings and positive product references in prose. Invalid positive selections clear all selection channels and cached lists; informational non-matches require explicit failure labels. The guard checks active requirements, independent quantities and requested shown-set membership. It does not guarantee complete interpretation, correct aggregate scope or installation suitability.

P1-F is implemented and locally verified: **669 tests (667 passed, 2 skipped)**; v7 **453/453**; T10 **48/48**; T12 **47/47**; T14 **42/42**. The original **42/60 remains the pre-fix live score**. No new provider run, rescore, deployment or Android/device validation is claimed. v15 became diagnostic/regression evidence after its failures informed repairs.

## Measurement controls and limits

Three disjoint blind packs each contained 20 conversations with shuffled A/B variants: **one independent reviewer per conversation**, not three votes. All 120 binary variant verdicts were present before unblinding. The pack renderer omitted some measurements on 19 v1 and 45 v2 cards; the separate full-card audit covered those omitted values. No answer exceeded the text limit and no response exceeded the six-card limit.

Matching inputs, frozen hashes, paired scoring and blind variants bound several sources of bias. They do not establish inter-reviewer agreement, eliminate sequential provider effects, or prove generalization beyond this cohort. No post-hoc v2 repairs or scoring changes were applied. P1-F needs a new frozen cohort to measure post-fix live quality; replays and synthetic compliance cannot substitute for it.

The source A/B report and raw evidence remain local under `<local-scratch>/`: `SV2-AB-report.md`, `sv2_ab_ledger.json`, `sv2_ab_provenance.json`, `sv2_ab_audit.json`, `sv2_ab_score_summary.json`, the `behavior/out_v15_v1` and `behavior/out_v15_v2` results and `blind/` verdicts. These are provenance locators, not files included in a fresh repository clone. This report preserves the summary; the experimental branch contains the offline implementation evidence.
