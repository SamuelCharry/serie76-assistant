# T14: Plan B structured interpretation

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

## Verification and live validation

Final gates, v14, cost, latency and adoption decision are pending. No paid
inference has run for this plan at this checkpoint. The scratch screening
wrapper now has an opt-in per-turn usage check with a USD 0.04 reserve before
the smaller of the plan and total-key caps. Usage failures stop inference.

The v13 latency outliers were two of 79 turns: single provider calls of roughly
11–16 seconds, not a code loop. Do not attribute a difference between v13 and
v14 to Plan B causally: the sets differ.

Remaining user steps after final backend validation: emulator test, clean clone
following the README, merge PR #10 and tag `v1.0-submission`, grant evaluator
access, and send the submission email by Sunday 2026-11-08. No merge or email
is authorized as part of this implementation task.
