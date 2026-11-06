# T11-B: oracle-filter recommendation ranking

The new evaluation detects a retrieval false negative even though all returned
recommendations comply with their hard requirements. **R22 loses all seven valid
candidates in `integrity.satisfies`**. No backend behavior was changed to improve
these measurements.

## Visible depth and execution scope

The user sees **k = 3 recommendation items**. `SearchInput.limit` defaults to 5 in
`backend/conversation/agent.py:218`, but `ranking.recommendation` slices `ordered[:3]`
in `backend/conversation/ranking.py:201`. Android independently uses
`recommendation.items.take(3)` and displays at most three in
`mobile/android/app/src/main/java/com/serie76/assistant/ui/Screens.kt:322`.
The raw SQL `SearchFilters.limit=20` is a third, unrelated default. **k=5 below is
additional backend ranking depth, not five cards visible in Android.**

Level 1 supplies gold filters and an objective directly: canonical wire arguments,
the real agent `SearchInput` validator, real PostgreSQL `search_actuators`, the
production integrity postcondition and production `ranking.rank`. These are the
deterministic components called by `Turn.search`; this evaluator does not execute
its language interpretation, question flow or UI rendering. It retrieves the
whole collection before ranking, so a SQL page cannot silently truncate the
candidate pool. No LLM/embedding/provider inference is used.

## Collection and independent judgments

- 68 CSV products, including all four `source_NA` entries; 40 authored plant
  requests (36 English, four Spanish); **2,720 product-query judgments**.
- CSV and active PostgreSQL exports were compared across every CSV field before
  scoring. A mismatch aborts the evaluation. Input and backend source SHA-256
  digests are retained in [the full JSON result](T11-B-ranking.json).
- Only `data/extracted/series76/catalog.csv` and the supplied glossary are judgment
  evidence. `scripts/ranking_judgments.py` imports no backend modules and receives
  neither backend output nor rankings.
- Grade 0 means a hard requirement fails or its value is unpublished. Grade 3
  includes all ties on a stated objective; without an objective it minimizes
  adequate torque and then FLA. Other compliant products get grade 1 for torque
  above twice the minimum, an unpublished objective, or an objective more than
  twice as poor as the optimum (below half the maximum for a torque objective);
  otherwise grade 2. Objective winners take precedence over oversizing penalties.
- The factor-two policy is an explicit evaluation judgment, not a catalogue
  safety standard or independently collected human annotation. Shared torque and
  duty use the CSV's published shared columns; electrical values use the requested
  frequency or the unqualified DC columns. No missing value is imputed.
- 39 queries have at least one compliant product. R36 is infeasible in this
  collection and remains in the published 40-query denominator.

## Metrics

Binary relevance means grade >= 1. Standard P@k divides hits by k, recall divides
by the complete relevant set, and AP@k sums precision at relevant positions up to
k divided by the **complete** relevant set (not `min(R,k)`). Full AP uses the full
returned ranking; MAP is the macro mean. NDCG uses `(2^grade - 1)/log2(rank+1)` and
the ideal ordering of all 68 judgments. Missing positions have zero gain. Queries
with no relevant products receive R/AP/NDCG=0 by explicit convention.

These are the formulas in Manning, Raghavan & Schuetze (2008), *Introduction to
Information Retrieval*, [sections 8.3](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)
and [8.4](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html).

All 40 queries, macro averages:

| Depth | Compliance among returned top-k | Standard P@k | R@k | MAP@k | NDCG@k |
|---|---:|---:|---:|---:|---:|
| 3, visible | 1.0000 | 0.9083 | 0.4966 | 0.4966 | 0.9404 |
| 5, additional depth | 1.0000 | 0.8550 | 0.7193 | 0.7193 | 0.9451 |

**Full-ranking MAP: 0.9500.** Binary AP@k equals recall here because every returned
item is compliant; graded NDCG is the useful measure of ordering quality.

The compliance rate is `hits/returned` on the top-k subset, undefined for an empty
list. Its mean covers **38 nonempty queries**, not 40 successful retrievals.
There are zero returned grade-0 products. Standard P@k is intentionally not
relabeled as 1.0: three nonempty lists have fewer than three items and nine have
fewer than five. R22 is unexpectedly empty; R36 correctly has no matching item.
An empty list cannot pass by being assigned perfect precision.

Sensitivity view excluding only the infeasible R36 (39 queries):

| Depth | Compliance among returned top-k | Standard P@k | R@k | MAP@k | NDCG@k |
|---|---:|---:|---:|---:|---:|
| 3 | 1.0000 | 0.9316 | 0.5093 | 0.5093 | 0.9645 |
| 5 | 1.0000 | 0.8769 | 0.7378 | 0.7378 | 0.9694 |

Full-ranking MAP for these 39 feasible queries is **0.9744**. These figures are a
diagnostic for this synthetic collection, not a population estimate or a measure
of real-model parsing accuracy.

## Three lowest-scoring queries

1. **T11-R22, NDCG@3/@5 = 0/0.** Weatherproof, 220 V three-phase AC, modulating,
   60 Hz, torque >=300 Nm and starts >=1,200/h; maximize torque. SQL returns seven
   valid products and the postcondition rejects all seven. In the hydrated
   `763A00-11330C00/A`, the `shared` service row contains 300 Nm and 70% duty but no
   starts; the `modulating` row contains 1,200 starts/h but no torque.
   `integrity.satisfies` requires both values in one service row. The CSV publishes
   both, and SQL correctly combines shared torque with service-specific starts.
   This is a candidate-loss bug, not unsafe returned data or an LLM mistake.
2. **T11-R36, NDCG@3/@5 = 0/0.** Explosionproof, 24 V DC, on/off, torque >=400 Nm;
   minimize motor power. The largest published on/off torque for that supply is
   240 Nm. Both gold and SQL have zero matches. The zeros reflect the declared
   empty-relevance convention, **not a ranking failure**; the feasible-only table
   removes this case transparently.
3. **T11-R39, NDCG@3 = 0.6151 and @5 = 0.8051.** Weatherproof, 220 V three-phase
   AC, on/off at 60 Hz, torque <=800 Nm, no stated objective. Backend order is
   800, 600, 500, 300 Nm; the independent default selects 300 Nm, then lower FLA.
   Grades are `[2,2,2,3]`, so the best-fit product is fourth and absent from the
   three-item card. This is an explicit policy disagreement: the backend prefers
   the closest value below an upper bound, while this task specifies the smallest
   adequate torque. All four products comply with the hard maximum.

## Verification and reproduction

Implemented: config, independent judge, real-DB evaluator, metric tests, complete
machine-readable judgments/results and this report. No commits, catalogue edits,
volume changes or inference calls were made; `.env` was never read.

- 12 hand-computed metric/judgment tests pass, including AP's full-set denominator,
  exponential-gain NDCG, incomplete lists, ties, duplicates, no relevant documents,
  strict numeric bounds, shared service data and unpublished values.
- v7 scripted selfcheck: **453/453 pass**, exit 0.
- Full DB unittest with `SERIES76_TEST_DB=1`, repo `.venv-chat`: **583 tests run,
  OK, 2 optional ingestion-dependency skips**, 279.861 seconds, exit 0. All 12 new
  tests are included. Final console evidence: `reports/t11-ranking/unittest-clean.log`;
  selfcheck evidence: `reports/t11-ranking/selfcheck.log`.
- New ranking evaluation: **exit 1 by design**, because it detects unexpected
  empty results for R22; zero hard-compliance violations. Do not describe this
  evaluator as a clean acceptance gate.

With the PostgreSQL process environment already provisioned (no `.env` loader):

```powershell
.\.venv-chat\Scripts\python.exe scripts/eval_ranking.py
.\.venv-chat\Scripts\python.exe -m unittest discover -s tests -p test_ranking_eval.py -v
```

For the full existing DB suite and selfcheck, their `local_environment()` helpers
normally read `.env`. This run patched that helper to a no-op **before test/script
imports**, used the existing container's DB-only settings in process memory, and
installed a Python audit hook that rejects attempts to open `.env`. The wrapper
and console logs are retained locally under `reports/t11-ranking/`; no provider
credentials were requested or printed. The repo `.venv-chat` was used because
`.venv` lacks `langchain_core`.

Pending outside this measurement task: fix and independently verify the R22
shared-service postcondition; decide whether the backend upper-bound preference
or the stipulated default relevance policy should change for R39. Real-model
interpretation and Android/device behavior were not evaluated.
