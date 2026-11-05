# T14: Plan B structured interpretation

**Decision: retained.** New held-out v14 passed **32/45 (71.1%)**, above the
precommitted 27/45 threshold. All required gates passed; interpreted-turn
client p95 was **6.17 s**, below 10 s. Production remains on
`google/gemini-3.6-flash`, with no fallback and `google/gemini-embedding-2`.

## Decision fixed before v14

Retain Plan B only if the new held-out v14 reaches **27/45**, every required
offline gate exits zero, and client latency p95 is at most **10 seconds**.
Report individual provider-tail outliers separately. Otherwise revert the Plan B
commits to the e90c397 production behavior with `git revert`, never reset.
No result from v13 establishes generalization: it is diagnostic material now.
v12 was 29/45 and v13 was 23/45 under strict blind review on different cohorts.

## Implemented

- B1: validated `priority` metric/direction/frequency for search and shown-set
  selection. Metrics cover torque, operating time, FLA, motor power, duty,
  cycles and starts; both directions are supported. SQL owns values and code
  owns ordering, missing-value handling and the applied ranking label.
- B2: lookup/search accept `unsupported_requests`. The compact wire uses
  comma-separated labels; canonical validation accepts a list, sanitizes each
  label, caps it at 40 characters and limits the list to eight items. Rendering
  uses a fixed decline sentence. Existing deterministic limitations remain as
  fallback. Spanish torque delivery is no longer shipping.
- B3: `keep` validates filter names, preserves existing state and prevents
  conflicting removal hints from dropping retained fields. Grounding recognizes
  carried values and earlier user evidence, excludes withdrawn/stale values and
  does not let assistant-generated numbers license new requirements.
- Optional catalogue topics use the existing clarification tool. Enclosure
  guidance quotes the summary; supply overviews query SQL. N/A explains source
  absence without substituting a value. Compound/scoped questions no longer
  get an unrelated catalogue-wide statistic.

Four tools, one completed interpretation decision, no new runtime agent, no
extra chat call, no self-correction loop, no fallback model. The historical T10
prompt and variant expectations are unchanged; Plan B guidance is an additive
system section used by production and preflight.

## Oracle and replay method

The initial ideal oracle passed **7/42** before implementation (exit 1).
It covers the v13 failure classes with two new paraphrases per grouped class,
mostly English and some Spanish. See
[baseline](../agent_acceptance/t14_oracle_pre_fix/report.md).
These are diagnostic scripted scenarios, not held-out model evidence.
One Spanish assumption quote was corrected to the words actually present in
its paraphrase; no expected outcome or frozen v7/T10/T12 expectation changed.

Original Flash decisions were recovered read-only from PostgreSQL using all
45 conversations' response `message_id` values. Replay uses the original
queries and raw recorded decisions, not reconstructions from answer text.
Its outcome assertions target the diagnosed failure classes plus the existing
numeric/provenance contract. The pre-fix replay on archived e90c397 passed
**23/45**. This is an automated diagnostic score, not a new blind review.
Old decisions have no Plan B fields. A formerly deterministic turn that newly
requires inference uses an explicit unsupported sentinel, never an invented
Flash decision. These cases must be reported as replay limitations.

The same recorded decisions replay at **28/45** after Plan B. Neither replay
adds inference or demonstrates generalization with the new fields.

## Verification and live validation

All required offline gates passed on source commit
`4906b6254a8568a05326ca776483220c7ccd2a02`:

| Gate | Result |
| --- | --- |
| PostgreSQL-enabled unittest discovery | 615 run, 613 passed, 2 skipped; exit 0 |
| v7 / T10 / T12 / T14 selfchecks | 453/453 / 48/48 / 47/47 / 42/42; all exit 0 |
| Tool schema | 5,520 bytes; 108 enum values; 6 arrays; exit 0 |
| Public text | exit 0 |
| Ranking | NDCG@3 0.965377944025286; returned compliance 1.0; exit 0 |

The code manifest was checked against the final source before paid validation.
The one-call live schema preflight returned **accepted**, and the backend image
was rebuilt from that source. The scratch screening wrapper has an opt-in per-turn usage check
with a USD 0.04 reserve. Starting key usage was USD **1.682915316**; this plan's
stop threshold is USD **2.182915316**, below the USD 2.50 total-key cap.
Usage-check failures stop inference.

The independent v14 author received no code, tests or v12/v13 material. It
produced 45 conversations (41 English, four Spanish), with SHA-256
`d82fd75f22eccb808e00db9ba77f168b371a66ec76a854541e76658cdb9c278c`.
The UTF-8 dataset hash was verified before screening.

Three independent Orca reviewers (`gpt-6-astra`, medium effort) each reviewed
a disjoint pack of 15 conversations against the catalogue CSV: **11/15,
14/15, 7/15**. This is one verdict per conversation, not three votes on each.
The author used `gpt-6-astra`, low effort. Reviewers could not read code,
other packs/verdicts or blind keys. All 45 verdicts were present; the scorer
reported **32/45**, with one model variant. No code or expectation was changed
after seeing v14. [Dataset, rendered packs and verdicts](../agent_acceptance/t14_live/).

| Live measurement | Result |
| --- | --- |
| Conversations / turns / interpreted turns | 45 / 85 / 66 |
| Client p95 on interpreted turns / maximum over all turns | 6.17 s / 9.32 s |
| Turns above 10 s / HTTP errors / skipped turns | 0 / 0 / 0 |
| Screen wrapper spend at its immediate ledger read | USD 0.223350 |
| Final settled key usage | USD 1.919522541 |
| Total Plan B spend, final usage minus starting usage | USD 0.236607225 |

Total spend includes preflight and screening/embedding charges as reflected
in the settled key ledger, rather than treating delayed charges as free.
It is below both the USD 0.50 plan budget and USD 2.50 total-key ceiling.
The final `start_or_model.py` restored Flash successfully; `with_openrouter.py`
with `scripts/check_openrouter.py` verified the final usage without printing
credentials. [Machine-readable live summary](../agent_acceptance/t14_live/summary.json).

## Remaining failures and measurement limits

The reviewers checked all displayed catalogue figures and found **zero
incorrect individual product values, but two incorrect aggregate counts**:
L1-05 omitted five eligible DC-only models (five returned as the eligible count
instead of ten); L7-09 reported 34 Weatherproof models rather than all 38 CSV
entries, excluding four source_NA entries without qualification. Therefore
the earlier zero-numeric-error observation must not be extended to v14.
SQL-derived numbers can still answer the wrong scope.

The 13 failures also include dropped request components, wrong selection
priorities, lost model context and incomplete catalogue-limit explanations.
Two presentation observations remain: L7-05's answer gives the requested
50 Hz time but its card shows only the 60 Hz time; L7-06 repeats a part number.
No post-hoc repairs were made before scoring.
[All failure reasons](../agent_acceptance/t14_live/failure_reasons.json).

The successful scripted oracle does not establish robust interpretation.
The old-decision replay has five unavailable-decision sentinels where the
original route was deterministic: L4-02 turn 3, L6-04 turn 1, L7-08 turns 1–2,
and L7-09 turn 3. Its nonzero exit is explicitly a diagnostic result, not a
passed required gate. Both replay scores and the new-field ideal oracle are
reported separately from the held-out result.

The v13 latency outliers were two of 79 interpreted turns: single provider calls of roughly
11–16 seconds, not a code loop. Do not attribute a difference between v13 and
v14 to Plan B causally: the sets differ.

## Reproduction and source history

Plan B commits, in order: `afe407a` (pre-fix oracle), `606e70e` (structured
interpretation), `6f508e4` (priority replacement), `4906b62` (UI ranking
persistence). No revert was required by the fixed rule.

The local no-provider reproducer requires the existing PostgreSQL catalogue
and running backend container. It reads only DB settings into process memory,
blocks `.env` reads and disables provider credentials. From the repository:

```text
.venv-model-eval\Scripts\python.exe reports/agent_acceptance/run_t14_gates.py
```

This runs unittest discovery with `SERIES76_TEST_DB=1`, the four required
selfchecks, schema/public-text/ranking checks, and the separately reported
diagnostic replay. [Final gate exits](../agent_acceptance/t14_final/summary.json),
[source hashes](../agent_acceptance/t14_final/code_manifest.json), and
[test log](../agent_acceptance/t14_final/unittest.log) preserve the measured
state. The two skipped tests require optional ingestion dependencies; they
are not skipped DB tests. Reproduction is not permission for paid inference.

Remaining user steps after final backend validation: emulator test, clean clone
following the README, merge PR #10 and tag `v1.0-submission`, grant evaluator
access, and send the submission email by Sunday 2026-11-08. No merge or email
is authorized as part of this implementation task.
