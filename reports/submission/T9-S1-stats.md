# T9-S1: uncertainty and retrieval evaluation

Implemented: two evaluation-only scripts, eight focused unit tests, bilingual explanations, README confidence intervals and three interview answers. Product behavior and retrieval parameters are unchanged. No inference, embedding, paid calls, push or deployment.

## Method and provenance

The method follows the user-provided summary of MINE4101, *Evaluacion avanzada de modelos* (percentile bootstrap, paired bootstrap, exact McNemar, Provost expected value), and NLP notes chapters 4 and 14.10 (precision@k and MRR). This implementation uses the method summary in the task; no page-level quotations or claims of independent verification of the course documents are made.

[Verdicts](../behavior/verdicts.json) are an exact copy of the supplied independent-review JSON, with aggregate counts for rounds 3-8 and paired conversation IDs for rounds 9-10. Their SHA-256 is `582d2a5c1ce48c435ff07652a7575f0f83229b524c548276ba764d66bcad347b`. This task computes uncertainty on those labels; it does not re-review provider answers or perform fresh provider acceptance. Rounds remain separate; turns within a conversation are not independent samples.

[`eval_stats.py`](../../scripts/eval_stats.py) uses only the Python standard library, 10,000 whole-conversation resamples, seed 20261104 and interpolated 2.5th/97.5th percentiles. Aggregate binary counts are expanded to pass/fail observations for marginal intervals only. A/B resamples A-minus-B within each conversation, preserving pairing. McNemar uses twice the smaller exact binomial tail, capped at 1; both paired tests give p=1. Non-significance does not establish equivalence; intervals also do not measure labeling uncertainty, domain shift or repeated model-selection effects. Six one-way discordances (and agreement in every other pair) reach p=0.03125; this is not a power/sample-size recommendation.

Latency p95 about 4 s Flash versus 7.4 s Pro comes from the coordinator's task specification, not the verdict JSON. It is a descriptive selection reason, not a computed statistical test of latency. The illustrative expected-utility table in the wiki is a cost assumption, not measured ROI: the client must assign real costs and outcome probabilities.

[`eval_retrieval.py`](../../scripts/eval_retrieval.py) reads active stored vectors through `local_environment()` and a read-only PostgreSQL transaction; the database query imports no data and makes no embedding call. Exact cosine is computed locally, separately per model, excluding self and exact same text. It evaluates every active example as a query and includes queries with zero relevant neighbors. Runtime is quadratic in bank size (offline diagnostic, not a production/load benchmark). The snapshot contains 649 active examples of `gemini-embedding-2`; dataset versions: {"v7-14e7fbf25214744f": 649}. Its content fingerprint appears below and in [retrieval JSON](../behavior/retrieval.json).

A relevant neighbor has the identical tool, service, enclosure, voltage and torque bound operators; absent fields must agree and scalar minima mean gte. Both interval bounds and strictness matter; torque values/units do not. Non-search codes/terms are outside this deliberately coarse interpretation-pattern metric. Thus related phrases can remain in the bank, labels are not independently re-annotated relevance judgments, and high retrieval scores would not certify correct products. Fifteen queries have no relevant peer. Same-source exclusion and a fresh-query relevance benchmark remain separate future checks.

Precision divides by requested k; fewer returned neighbors leave empty slots counted as misses. MRR is reciprocal first relevant rank, or zero, truncated at k. Coverage is the share receiving any example, not relevant-example coverage. The threshold sweep also reports precision among returned examples to distinguish abstention from ranking quality. The main requested P@1/P@3/P@5/MRR@5 are shown for both no cutoff and current cutoff 0.70; the sweep covers k=1/3/5/8 and thresholds 0.50/0.60/0.70/0.75/0.80/0.85/0.90.

Recommendation: k=5 is a provisional context cap with diminishing MRR gains (0.546 at k=3, 0.563 at k=5, 0.570 at k=8), not an empirically optimal setting. A cutoff of 0.70 retains 98.3% query coverage but leaves precision among returned neighbors at 38.2%, essentially unchanged from no cutoff; this diagnostic does not justify it as a relevance filter. Calibrate with fresh labeled queries and downstream utility before changing production. The round-9 end-to-end comparison provides no statistically distinguishable retrieval advantage.

## Script outputs

Run from the repository root with backend dependencies and the existing local database available:

```text
.venv-chat/Scripts/python.exe scripts/eval_stats.py
```

```text
95% percentile bootstrap; 10,000 resamples; seed 20261104.
round3/rules: 21/45 = 46.7%; CI [31.1, 60.0]%
round4/rules: 24/45 = 53.3%; CI [37.8, 66.7]%
round5/rules: 21/44 = 47.7%; CI [34.1, 61.4]%
round6/rules: 28/43 = 65.1%; CI [51.2, 79.1]%
round7/rules: 24/43 = 55.8%; CI [41.9, 69.8]%
round8/retrieval_on: 25/41 = 61.0%; CI [46.3, 75.6]%
round8/retrieval_off: 26/41 = 63.4%; CI [48.8, 78.0]%
round9_retrieval/retrieval_on: 30/41 = 73.2%; CI [58.5, 85.4]%
round9_retrieval/retrieval_off: 29/41 = 70.7%; CI [56.1, 82.9]%
round10_models/gemini-3.6-flash: 28/41 = 68.3%; CI [53.7, 82.9]%
round10_models/gemini-3.1-pro-preview: 28/41 = 68.3%; CI [53.7, 82.9]%
round9_retrieval (A=retrieval_on, B=retrieval_off): only A=2, only B=1; exact McNemar p=1.000000.
A-B=2.44 percentage points; CI [-4.9, 12.2] points; not significant: the difference is within sampling noise.
At n=41, at least 6 disagreements all favoring one setup (all other pairs agree) are needed for two-sided p < 0.05; this is not a power calculation.
round10_models (A=gemini-3.6-flash, B=gemini-3.1-pro-preview): only A=3, only B=3; exact McNemar p=1.000000.
A-B=0.00 percentage points; CI [-12.2, 12.2] points; not significant: the difference is within sampling noise.
At n=41, at least 6 disagreements all favoring one setup (all other pairs agree) are needed for two-sided p < 0.05; this is not a power calculation.
Failure to reject is not proof of equivalence; aggregate-only rounds have no paired test.
```

[Machine-readable statistics](../behavior/stats.json).

```text
.venv-chat/Scripts/python.exe scripts/eval_retrieval.py
```

```text
Stored bank: 649 active examples; sha256=99994b5a7228bd1d57bb5e56931456545e4fa103ca1058cee46b7639c6e45aeb
Exact cosine; self/same text excluded; relevance is tool + search-field pattern, not product correctness.
Precision uses k slots per query; missing slots count as misses. MRR is truncated at k.
Model: gemini-embedding-2; queries=649; no relevant neighbor anywhere=15
threshold  k  precision@k  MRR@k  coverage  mean returned  precision among returned
     none  1       0.4761 0.4761    1.0000           1.00                    0.4761
     none  3       0.4109 0.5455    1.0000           3.00                    0.4109
     none  5       0.3821 0.5627    1.0000           5.00                    0.3821
     none  8       0.3596 0.5701    1.0000           8.00                    0.3596
     0.50  1       0.4746 0.4746    0.9985           1.00                    0.4753
     0.50  3       0.4104 0.5439    0.9985           3.00                    0.4110
     0.50  5       0.3815 0.5612    0.9985           4.99                    0.3821
     0.50  8       0.3588 0.5685    0.9985           7.98                    0.3595
     0.60  1       0.4746 0.4746    0.9985           1.00                    0.4753
     0.60  3       0.4104 0.5439    0.9985           2.99                    0.4121
     0.60  5       0.3809 0.5605    0.9985           4.97                    0.3830
     0.60  8       0.3577 0.5678    0.9985           7.92                    0.3611
     0.70  1       0.4700 0.4700    0.9831           0.98                    0.4781
     0.70  3       0.3929 0.5354    0.9831           2.86                    0.4126
     0.70  5       0.3559 0.5505    0.9831           4.66                    0.3821
     0.70  8       0.3253 0.5572    0.9831           7.24                    0.3593
     0.75  1       0.4468 0.4468    0.9368           0.94                    0.4770
     0.75  3       0.3647 0.5090    0.9368           2.65                    0.4130
     0.75  5       0.3251 0.5218    0.9368           4.21                    0.3862
     0.75  8       0.2918 0.5269    0.9368           6.37                    0.3667
     0.80  1       0.4052 0.4052    0.8320           0.83                    0.4870
     0.80  3       0.3148 0.4466    0.8320           2.22                    0.4254
     0.80  5       0.2718 0.4562    0.8320           3.36                    0.4046
     0.80  8       0.2296 0.4598    0.8320           4.78                    0.3845
     0.85  1       0.3359 0.3359    0.6410           0.64                    0.5240
     0.85  3       0.2255 0.3606    0.6410           1.52                    0.4439
     0.85  5       0.1741 0.3640    0.6410           2.12                    0.4106
     0.85  8       0.1339 0.3653    0.6410           2.79                    0.3840
     0.90  1       0.2234 0.2234    0.3806           0.38                    0.5870
     0.90  3       0.1284 0.2365    0.3806           0.76                    0.5061
     0.90  5       0.0924 0.2382    0.3806           0.98                    0.4732
     0.90  8       0.0690 0.2387    0.3806           1.18                    0.4668
k=5 adds 8.7 MRR points over k=1; k=8 adds 0.7 more. Threshold 0.70 covers 98.3% of queries. k=5 and the threshold remain provisional: this sweep exposes the trade-off, but does not establish an optimum or a downstream quality benefit; validate on fresh queries before changing them.
```

## Verification

| Gate | Result |
|---|---|
| Full Python suite, real local DB enabled | 514 tests, 2 optional dependency skips, exit 0; 221.919 s |
| Focused evaluation tests | 8/8 passed, exit 0; includes the additional second-rank MRR test added after full-suite discovery |
| v7 scripted selfcheck | 453/453 scenarios passed, no failures, exit 0 |
| Markdown relative links/anchors | 751 checked, 0 broken, exit 0 |
| Exact verdict copy | Source/destination SHA-256 matches |
| Whitespace / product scope | git diff --check clean; no backend, Android, catalogue or runtime configuration changes |

Commands: `python -m unittest discover -s tests` with `SERIES76_TEST_DB=1`; `python -m unittest discover -s tests -p test_eval*.py -v`; `python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json`; `python scripts/check_docs_links.py`. All used `.venv-chat/Scripts/python.exe` from the repository root. Provider/embedding keys and model names were cleared and embedding/tracing switches disabled in the gate processes; database settings came from the existing approved local helper. Existing optional OCR/geometric dependency skips and non-fatal tracer callback warnings do not constitute live-provider validation.

Verified locally: computed statistics, stored-vector retrieval, synthetic known-answer ranks, exact p-values, deterministic intervals, DB-enabled Python suite, scripted behavior and local links. Pending: new independent conversations for model/retrieval claims, relevance annotation on fresh queries, a powered prospective comparison and real client costs. No paid inference, database writes by the evaluator, product parameter change or push was performed.

Co-Authored-By: Codex <noreply@openai.com>
