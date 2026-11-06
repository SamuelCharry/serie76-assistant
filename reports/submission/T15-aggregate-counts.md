# T15: Aggregate counts audit — 2026-11-05

## Verdicts against the questions actually asked

The retained [v14 dataset](../agent_acceptance/t14_live/heldout_v14.json),
packs, reviewer verdicts and failure reasons are unchanged. This audit uses
[catalog.csv](../../data/extracted/series76/catalog.csv), SHA-256
`7fc3f2086668fe7fcab62f4b2d7e0d1d2a31e7737a316ddf51d441ce2ee38d83`.
The electrical PDF remains the catalogue's source authority.

### L1-05: reviewer correct; the report's DC-only description was misleading

Exact question: “List the explosionproof units that accept a 24 V DC supply,
including dual AC/DC units.” The answer began “5 actuators meet:
Explosionproof, AC/DC, 24 V.” Its active filters also said AC/DC and its ranked
list total was 5. See [pack 1](../agent_acceptance/t14_live/pack_v14or_1.md)
and [verdict 1](../agent_acceptance/t14_live/verdicts_v14or_1.json).

The requested scope is Explosionproof AND 24 V AND compatible with DC, with
no service restriction. It includes both of these five-row CSV groups:

| Supply | CSV table / rows | Complete part numbers |
| --- | --- | --- |
| DC | p3_t2 / 1–5 | 761X30-11370000/A, 761Y30-11370000/A, 762X30-11370000/A, 762Y30-11370000/A, 763X30-11370000/A |
| AC/DC | p3_t1 / 1–5 | 761X30-11380000/A, 761Y30-11380000/A, 762X30-11380000/A, 762Y30-11380000/A, 763X30-11380000/A |

All ten have reported data. Five is correct for the incorrectly narrowed AC/DC
filter, but wrong for the user's requested eligibility scope. The neighboring
L1-06 explicitly requests DC-only and correctly returns five; these requests
must not be conflated.

### L7-09: wrong route plus an unqualified published-data subtotal

The exact turns and answers in [pack 3](../agent_acceptance/t14_live/pack_v14or_3.md) are:

1. “Show the on/off torque and enclosure for 761Y30-11380000/A.” →
   “Published enclosures: Explosionproof (30 models), Weatherproof (34 models).”
2. “Would it accept DC power?” → “Which shown model do you mean?”
3. “Does accepting DC mean it is a DC-only model?” →
   “24 V AC/DC, 24 V DC, 110 V AC 1-phase, 220 V AC 1-phase, 220 V AC 3-phase”.

No turn asks for a catalogue count. The initial aggregate is irrelevant to the
named model; its CSV record is Explosionproof, 24 V AC/DC, On/Off torque 80 Nm
(700 in-lb). The catalogue has 38 Weatherproof entries: 34 `reported` and four
`source_NA`. Thus 34 is a correct published-data subtotal, not the total listed
Weatherproof inventory, and the original wording did not disclose that boundary.
The [reviewer](../agent_acceptance/t14_live/verdicts_v14or_3.json) correctly
flagged the omission; it is a scope/presentation defect rather than wrong arithmetic.

The four N/A entries are 761A00-11330C00/A, 761B00-11330C00/A,
762A00-11330C00/A and 762B00-11330C00/A, table p2_t1 rows 1–4.
All are Weatherproof, 220 V AC three-phase. Their missing performance values
cannot establish eligibility for numeric requirements.

## Implemented and tested without inference

- Explicit DC compatibility with included dual-rated units maps to the existing
  SQL DC-compatible filter; DC-only and dual-only remain separate.
- Search aggregates share a scope renderer: applied filters (or whole catalogue)
  plus the published-electrical-data boundary. SQL supplies the counts.
- SQL separately counts source-N/A entries under known categorical filters.
  The answer names that scope and says performance eligibility is unverified;
  it never describes these rows as satisfying an unknown numeric threshold.
- Enclosure/voltage/service overviews and direct model counts disclose published
  versus N/A entries. An explicit complete part number cannot trigger a
  catalogue-wide answer. Combined metric/enclosure lookups retain the enclosure.
- [Ten tests](../../tests/test_t15_aggregate_counts.py) include CSV oracles,
  original prompts and paraphrases, deliberately narrowed scripted decisions,
  a transaction-rolled-back SQL mutation, and a guard checking each aggregate
  sentence for scope and publication status, including numeric constraints.
  Existing aggregate wording expectations
  were updated to the explicit scoped wording; frozen acceptance cases are unchanged.

These are deterministic regression results, not fresh provider interpretation
evidence. The historical v14 result stays 32/45; T15 does not rescore it or
claim that all follow-up failures in L7-09 are resolved.

## Final gates

The required command completed at **2026-11-05 23:13 UTC**, with runner exit
**0** and all eight required gates at exit **0**, on the final code:

| Gate | Result |
| --- | --- |
| PostgreSQL-enabled unittest discovery | 625 run, 623 passed, 2 skipped |
| v7 / T10 / T12 / T14 selfchecks | 453/453 / 48/48 / 47/47 / 42/42 |
| Tool schema | 5,520 bytes; 108 enum values |
| Public text | exit 0 |
| Ranking | NDCG@3 0.965377944025286; returned compliance 1.0 |

The separate old-decision replay remains **28/45, exit 1**; it is diagnostic,
not one of the required gates, and does not establish provider generalization.
All **188** source hashes in the completed runner manifest were checked against
the working files before committing, with no mismatch. No source or test was
changed after this final run began.

[Gate exits](../agent_acceptance/t15_final/summary.json),
[counts and metrics](../agent_acceptance/t15_final/metrics.json),
[source manifest](../agent_acceptance/t15_final/code_manifest.json) and
[unittest log](../agent_acceptance/t15_final/unittest.log) retain the evidence.
The runner's logs were archived under `t15_final`; historical T14 outputs were
restored unchanged after archival. The ten new T15 tests are part of discovery.
