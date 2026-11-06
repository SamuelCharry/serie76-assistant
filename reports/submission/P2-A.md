# P2-A — Flash improvement and frozen v17 validation

**User decision: ADOPT the measured candidate as an explicit exception to the original no-regression rule** (coordinator authorization `msg_58183c6ef90c`). The measured candidate improves all three blind comparisons but has confirmed new integrity defects; it did **not** satisfy absolute integrity 1.0 or zero new regressions. Post-decision repairs are offline only and all required final gates passed; they do not change the frozen paid scores.

## Compared systems and independence

- Production configuration throughout: v1, `google/gemini-3.6-flash`, no fallback.
- v17 baseline: `2f28b71`, built in a detached scratch worktree. Measured final: `3ede96cb371c39e4fd6988dc098a47c46dee3a5f`. Main checkout stayed on `release/submission`.
- v16 diagnostic baseline included `79641bc`; measured code lever was `2a99818606827acc45ad3157fdc016074344fd20`. Its score must not be attributed to the later corrected commit.
- v17 first opened after final source freeze and passing offline gates. SHA-256: `12f5bba6c28798062f1eff671e0effda849c94ac5b787bc8bce5a04ccbb10786`. Both frozen-set checksum checks passed; v16 SHA-256: `839ca70286e77afb0a98dc4567ba68240edd88bae03d61ed35733c9aad38e4cf`.
- Independent evaluation scopes were fixed before inspecting v17 responses: [scope freeze](../agent_acceptance/p2/v17_scope_freeze.json), SHA-256 `dbcf01408175812610b66686d636a4a021b9ffa4f20b43d3b444340471137946` (see artifact for authoritative hash).
- Retrieval remained exactly identical before/after all runs: 1,956 examples, 200 anchors, two datasets; 658 Google-embedding examples. Canonical SHA-256 `7c1aca561c181800d8c0790fb6ac65c33ac9a7880406a15f754e308993f478d1`; [read-only verification](../agent_acceptance/p2/retrieval_postrun_check.json).
- Three independent paired blind packs, one per repeat, 60 conversations × two shuffled variants. No answer/card truncation; omitted extra card fields are covered by the full structured audit. Review keys and verdicts are retained in the evidence directory.

## Diagnosis and levers

| v16 run | Source | Blind pass | p95 / max seconds | USD observed delta |
|---|---|---:|---:|---:|
| v16base | 400d5c2 | 34/60 | 6.77 / 12.62 | 0.338064400 |
| v16code | 2a99818 | 54/60 | 6.92 / 16.80 | 0.373012275 |

Both runs completed 60 conversations / 131 turns, all HTTP 200. Discordant counts: baseline-only 3, code-only 23; exact McNemar p=0.00008797645568847656. Structured figures: 2,679 / 2,781 checked, zero mismatches. v16 became development data: the apparent gain is optimistic.

[Recorded classification](../agent_acceptance/p2/classification.json) separates 23 code classes, three interpretation classes and one existing-contract guard using read-only PostgreSQL decisions by message ID. Original examples plus two paraphrases per class formed 81 scenarios; four broad regressions brought the first suite to 85. General fixes address grounded numeric requirements, removals/corrections, identifier masking, categorical replacement, comparison scope, compound requests and presentation counts. Interpretation changes use general tool/prompt guidance; schema stays 108 enums.

Five remaining functional v16code failures yielded 15 additional oracle scenarios. Corrected ordinal resolution and fresh search-domain handling brought the oracle from 87/100 to 100/100. The corrected source received **no additional paid v16 measurement**. Coordinator `msg_e0f26dbb46aa` omitted contrastive-bank and prompt-variant trials: neither lever was loaded, measured or adopted. Their effects are unknown.

Oracle corrections were explicit: the small Explosionproof 220 V models publish 23 s at 50 Hz, not the initial draft's 20 s; numeric nearest examples stay outside positive recommendation items under unchanged T10 contracts. No frozen historical test assertion was changed.

## v17 measurements

Every valid run completed 60 conversations / 146 turns, all HTTP 200, no skips. Six valid runs total 876 turns.

| Run | Blind pass | p95 s | Max s | Turns >10 s | USD observed delta |
|---|---:|---:|---:|---:|---:|
| v17_base1 | 37/60 | 6.61 | 8.02 | 0 | 0.375522975 |
| v17_final1_retry | 47/60 | 8.33 | 17.89 | 3 | 0.390818000 |
| v17_base2 | 35/60 | 6.19 | 11.23 | 1 | 0.401642900 |
| v17_final2 | 46/60 | 5.80 | 8.52 | 0 | 0.402584450 |
| v17_base3 | 38/60 | 5.40 | 7.72 | 0 | 0.388103100 |
| v17_final3 | 50/60 | 5.70 | 9.00 | 0 | 0.388188625 |

Pooled nearest-rank p95: baseline **6.06 s**, final **6.69 s**; maxima 11.23 / 17.89 s; one / three turns above 10 s. These are client measurements, not server-only timings. A brief auxiliary offline public-text selfcheck process was started and stopped during baseline2; it is not a gate result. Subsequent public-text audits read saved outputs only.

| Pair | Baseline-only pass | Final-only pass | Exact McNemar p |
|---|---:|---:|---:|
| 1 | 2 | 12 | 0.012939453125 |
| 2 | 2 | 13 | 0.00738525390625 |
| 3 | 1 | 13 | 0.0018310546875 |

Three-repeat summary (`pass^k` means all k selected repetitions succeed, not pass@k):

| Measure | Baseline | Measured final |
|---|---:|---:|
| Pass counts | 37, 35, 38 | 47, 46, 50 |
| Mean pass count /60 | 36.6667 | 47.6667 |
| pass^1 | 61.1111% | 79.4444% |
| pass^2 | 57.7778% | 75.5556% |
| pass^3 | 55.0000% | 71.6667% |
| Conversations passing all three | 33/60 | 43/60 |

Mean improvement: **11 conversations / 60 (+18.3333 percentage points)**. The mean-quality condition passes. Exact statistics and definitions: [paired results](../agent_acceptance/p2/v17_paired_stats.json).

## Integrity and limits of automation

The full structured audit checks **18,792 values**, zero wrong figures (baseline 9,858; final 8,934). Correct numbers do not imply correct requirements or references.

Manual adjudication finds baseline **28/438** failing turns (compliance **0.9360730594**) and final **9/438** (compliance **0.9794520548**). Per-run final failures: 3, 4, 2. [Exact locations and adjudication](../agent_acceptance/p2/v17_integrity_adjudication.json).

| Repeat | Baseline failure turns | Baseline compliance | Final failure turns | Final compliance |
|---|---:|---:|---:|---:|
| 1 | 9/146 | 0.938356 | 3/146 | 0.979452 |
| 2 | 10/146 | 0.931507 | 4/146 | 0.972603 |
| 3 | 9/146 | 0.938356 | 2/146 | 0.986301 |
| All | 28/438 | 0.936073 | 9/438 | 0.979452 |


- Shared L2-10: all three runs in both arms recommend the same 300 Nm reference after asking for a strictly stronger model.
- Shared L7-06: all three runs in both arms incorrectly introduce a 1100 Nm minimum instead of strictly exceeding the 500 Nm reference.
- **New final regression:** all three final runs retain the explicitly withdrawn 1100 Nm ceiling; all three baselines remove it. Baseline also wrongly drops phase, which final preserves; aggregate improvement does not erase the new ceiling defect.
- **New final regression:** pair2 L3-06 returns the first comparison member after requesting the second. Both publish equal currents, so numeric-only checks miss the wrong identity.
- L7-09 stale earlier floors without a positive selection are reported as quality/state defects, not newly invented limits or false positive recommendations.

Stored public-text automation scans 876 responses / 25,113 strings with zero detected issues, but blind review finds baseline `mintorquenm` leakage that the detector misses. The automated zero is not a zero-leakage guarantee. Empty recommendation-layout flags follow the existing zero-result contract and are retained separately.

## Gates and decision protocol

Measured final source passed: full unittest **778 tests, zero failures, two skips**, exit 0 (429.442 s); P2 oracle **100/100**, exit 0; T14 runner exit 0 with v7/T10/T12/T14/schema/public-text/ranking all exit 0. Schema: **5,520 bytes / 108 enums**. [Gate evidence](../agent_acceptance/p2/gates_final/summary.json).

Historical recorded-model replay is **28/45, exit 1**. The unchanged T14 runner excludes this diagnostic from its success rule; it is not claimed green. Earlier interrupted/debug gate attempts do not count as passes.

Original pre-registered adoption rule: mean final ≥ mean baseline, integrity 1.0 / zero wrong figures, p95 ≤10 s, all required gates green; otherwise git revert. After pair1, coordinator `msg_57477ea7c31c` interpreted integrity as no regression versus baseline, while requiring explicit shared-defect counts. New field-level regressions are nevertheless present. Any adoption therefore requires an explicitly documented user decision, not a claim that the original rule passed.

Coordinator `msg_65ebb490be5d` requires user confirmation after pair3 and defines subsequent scope: if adopted, repair the two new regressions plus the two shared relative-bound defects offline, with final-boundary invariants/paraphrases and all gates including expanded P2 green; if rejected, git revert P2 source, preserve P2 oracle as historical expected-failure evidence, then add only strict-relative invariant repair and pass original full/T14 gates. **No new paid run.** Any repaired production head must be distinguished from this measured commit.

## Spend and excluded attempt

- Initial total key usage: **USD 2.697095241**; latest settled total: **USD 6.170259916**; global hard cap **USD 7.60**.
- Phases 1–3 measured spend: **USD 0.711076675**, within USD 1.60 allowance. Contrastive-bank/prompt trials omitted by coordinator.
- Phase4 start: **USD 3.441210316**. Coordinator `msg_60a30c38901c` transferred USD 0.45 unused earlier allowance: phase4 budget **USD 2.85**, absolute stop **USD 6.291210316**. Settled phase usage delta **USD 2.729049600**.
- Six valid v17 runs: **USD 2.346860050**. Excluded incomplete attempt `v17_final1`: **USD 0.357069350**, 135/146 server turns, internal exit1, no complete client artifact; excluded before candidate-response inspection. No success or latency reconstructed from partial SQL logs.
- Total observed P2-A run-boundary spend including that failed attempt: **USD 3.415006075**. Shared-key/delayed boundary differences total **USD 0.058158600**: 0.023133900 confirmed user emulator usage; 0.009904500 + 0.014875400 + 0.010244800 unattributed/delayed settlement. These still count against the hard ceiling.
- Harness recovery preserved stderr, propagated internal errors, checkpointed each turn and retried metadata checks while failing closed. Offline failure injection made zero provider calls. No model request/prompt/question/timer change. [Recovery evidence](../agent_acceptance/p2/phase4_harness_recovery.json); [exact phase ledger](../agent_acceptance/p2/phase4_ledger.json).

Raw runs, isolated images and worktree remain in `<local scratch>`. No credentials were printed and no PostgreSQL volume was removed. The repaired source passed all required final gates; the rebuilt Flash backend is ready. Source and evidence are delivered on `release/submission`.

## Authorized post-decision repair (offline only)

The user accepted the measured mean **47.67 vs 36.67**, pass^3 **71.7% vs 55%**, and integrity **429/438 vs 410/438**, while explicitly accepting an exception for the two new regressions. The measured source remains **3ede96c**; the repaired source is **`1dda5f2532169fd435012f965689a4a88c075549`** and receives no new paid score.

- Written singular ordinals override conflicting model reference selectors. The final response boundary independently checks the requested displayed identity, even when both models publish equal measurements.
- Numbers naming withdrawn limits are excluded from new quantity evidence. Directional removal prunes only the requested side in state and the independent quantity ledger; affirmative retained requirements remain intact.
- Relative torque and operating-time requests derive strict thresholds from SQL, exclude the reference itself and intersect separately written requirements. The final boundary independently re-derives these obligations from the prior display and SQL; unsupported or stale selections fail closed across output routes.
- Added **15 scenario regressions**, each class with three formulations, plus **four route-independent invariant tests** covering equal references, wrong ordinal identity, and withdrawn/invented bounds. Read-only recorded traces anchor the repairs by message ID: [post-decision classification](../agent_acceptance/p2/postdecision_classification.json).
- Expanded P2 oracle: **119/119, exit 0** on the repaired source before the full gate run. Full DB unittest **797 tests, zero failures, two existing skips (461.868 s)** and the T14 runner both exit 0; no paid/provider request and no Android code change.

Two incomplete post-decision full-suite attempts were intentionally stopped after additional boundary review found unit-scope and informational-route bypass cases; neither counts as a passing gate. The final uninterrupted gate run uses the same source as the passing 119-test oracle. Repaired behavior is scripted-decision / real-SQL evidence; there is no new paid Flash score or repaired-head latency estimate.

A completed 797-test repair attempt exposed one unchanged T10 reference-state regression (missing carried service); that was repaired, and the 15 targeted T10 route tests plus the 119-test P2 suite pass. Its failed log is preserved; the subsequent fresh complete full/T14 run passed on that corrected source.

For the repaired head, v17 is now regression/development evidence rather than an unseen holdout. Independent real-Flash validation of that repaired head remains unmeasured under the explicit no-more-paid-runs instruction; the paid quality, integrity and latency figures belong only to 3ede96c.


## Repaired source delivery

Repair commit: **`1dda5f2532169fd435012f965689a4a88c075549`**. The pre-run, post-run and current source manifests match; the 119-test P2 oracle uses the same source. [Final gate summary](../agent_acceptance/p2/gates_repaired/status.json) and [scripted decisions with read-only SQL](../agent_acceptance/p2/postdecision_examples.json).

All required exits are 0: full DB unittest (797 tests, two existing skips), v7 (453 scenarios), T10 (48), T12 (47), T14 (42), schema (108 enums / 5,520 bytes), public text and ranking. The public-text scanner reports `TOTAL responses=1060 strings=32236 issues=0 errors=0`; this retains the previously stated detector limitation. Historical replay remains diagnostic: **28/45, exit 1**, excluded by the unchanged runner, not claimed as a passing gate.

The backend was rebuilt and restarted using the approved Flash wrapper; `/ready` returns HTTP 200. Verification matched **74** source files in the running container to the repaired checkout, with Flash, empty fallback and default prompt variant. [Runtime evidence](../agent_acceptance/p2/repaired_runtime.json). The v1 architecture and PostgreSQL volume are preserved; no Android files changed.

Final metadata-only usage check: **USD 6.170259916**, unchanged after offline repairs. No additional inference was purchased. The user-approved adoption exception remains the decision; neither passing offline gates nor readiness substitutes for an unperformed paid evaluation of this repaired head.

Run-context disclosure: a brief auxiliary offline public-text selfcheck overlapped baseline repeat 2 and was stopped; it is not counted as a gate. Subsequent v17 response audits used stored outputs only. The recorded client latencies remain the observed values, with that local-workload limitation disclosed.
