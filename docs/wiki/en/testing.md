# Testing

[Wiki](index.md) · [English](../en/testing.md) · [Español](../es/testing.md)

What each suite proves, and what still requires real-provider acceptance.

A scripted model returns predetermined tool calls; the real tools then execute validation, SQL and rendering. That proves deterministic behavior and persistence, not language understanding. Real-provider cohorts test interpretation separately. No test command below authorizes paid inference.

- [test_reviewed_catalog.py](../../../tests/test_reviewed_catalog.py): Evaluation-only manual reference and exact correction fixtures.
- [test_dynamic_geometry.py](../../../tests/test_dynamic_geometry.py): Novel rows, shifts and table reconstruction.
- [test_pipeline_safety.py](../../../tests/test_pipeline_safety.py): Failure isolation, integrity, guarded reference/network access and bounded ingestion.
- [test_catalog_db.py](../../../tests/test_catalog_db.py): Real SQL filters, scoped measurements, provenance and imports.
- [test_agent_policy.py](../../../tests/test_agent_policy.py): Grounding, codes, contradictions and filter merging.
- [test_agent_scenarios.py](../../../tests/test_agent_scenarios.py): Tool execution against scripted decisions and real catalogue.
- [test_conversations.py](../../../tests/test_conversations.py): API contract, transaction rollback, snapshots and session history.
- [test_auth.py](../../../tests/test_auth.py): Hashed auth, revocation, owner isolation and Android-facing auth contract.
- [test_submission_readiness.py](../../../tests/test_submission_readiness.py): Routing require_parameters, process call guard and idempotent demo users.

## OpenRouter model selection

**OpenRouter acceptance completed on 2026-11-05:** USD 1.17 spent from the USD 10 key. Blind strict review used three independent reviewers per round and shuffled variants per conversation: held-out v10 (41 conversations) + v11 (40), 81 total, including 74 in English. These are measured cohort results, not current price quotes or latency guarantees.

| Model | English | All | p95 / max | Turns > 10 s | USD / 1,000 LLM turns |
|---|---:|---:|---:|---:|---:|
| gemini-3.6-flash | 63/74 | 69/81 | 5.9 / 8.9 s | 0 | 3.0 |
| gpt-6-luna | 61/74 | 67/81 | 4.9 / 12.2 s | 1 | 0.8 |
| deepseek-v4.1-flash | 59/74 | 65/81 | 8.8 / 10.8 s | 2 | 0.8 |
| claude-haiku-5.5 | 50/74 | 55/81 | 3.1 / 8.7 s | 0 | 0.7 |

**Decision rule, fixed before re-measuring:** (1) English quality unless statistically tied, (2) no observed turn over 10 s, (3) cost, (4) licence for production only (DeepSeek has open weights; licence still needs verification). Flash vs Luna: McNemar p = 0.63 (3 vs 1 discordant); Flash vs DeepSeek: p = 0.125; Haiku is significantly worse (p < 0.001). Lack of significance does not establish equivalence.

**Single-model default:** `OPENROUTER_CHAT_MODEL=google/gemini-3.6-flash`, `OPENROUTER_FALLBACK_MODEL=` (disabled), `OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2`. No fallback is configured because each interpreted turn needs one simple tool decision, the measured acceptance recorded 0 provider errors, and `.with_retry(stop_after_attempt=2)` already allows two total attempts for transient failures (503, timeout or connection errors). Flash meets the observed latency rule; the final Flash vs `qwen/qwen3.7-plus` comparison on held-out v12 after the code fixes is pending. v11 is now diagnostic/regression evidence only.

Schema preflight passed for gemini-3.6-flash, gemini-3.8-flash, gpt-6-luna, deepseek-v4.1-flash and gpt-6-sol. claude-haiku-5.5 passes only with `OPENROUTER_REQUIRE_PARAMETERS=false`: OpenRouter does not route `tool_choice=required` to Anthropic with `require_parameters`. claude-sonnet-5.5 rejects `tool_choice=required`. This records the tested routing, not future availability.

gpt-6-sol was tested on v10 only: 37/41 vs Flash 38/41, p = 1.0, at USD 7.5 per 1,000 LLM turns. gemini-3.8-flash was excluded by latency: p95 16.4 s and seven turns over 10 s.

OpenRouter `google/gemini-embedding-2` produced vectors identical to Google's in the comparison (cosine 1.00000, 768 dimensions). Retrieval filters by model name, so the bank was reloaded under `google/gemini-embedding-2` using the README loader: 658 examples + 100 anchors, about USD 0.0015. Matching vectors do not make differently named banks interchangeable.

## T10 oracle suite: model vs code defects

In v11 the three best models failed the same nine conversations. The coordinator traced those shared failures to deterministic code after the model decision. The T10 suite scripts the ideal LLM decision: **8/48 before fixes, 48/48 after**, as reported by the coordinator, not re-run by this documentation task. It isolates bound corrections, AC/DC grounding, objective persistence, reference operations, compound out-of-scope parts, every/all, overview paraphrases, hazard suitability, ranking labels and empty interpretation.

```text
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_t10.json --config config/agent_acceptance_t10.json
```

Run from the repository root in the backend Python environment with the catalogue available. This is a scripted code regression check, not paid model inference or proof of language understanding. Method references: IC-DST (EMNLP 2022) for add/replace/remove state deltas; Dataflow (TACL 2020) for reference operations. See [state semantics](agent.md#state-deltas-and-reference-operations-t10). v11 is now diagnostic/regression only; generalization claims require a new held-out v12 after the fixes. Earlier Google rounds below are historical and are not pooled with this OpenRouter selection.

## How we know a difference is real

A 95% bootstrap interval describes variation from resampling these conversations; it does not cover reviewer bias or guarantee performance on new domains.
McNemar compares paired pass/fail outcomes: **only the conversations where the two setups disagree count**.
We resample whole conversations 10,000 times with seed 20261104, use percentile intervals and a two-sided exact McNemar test.

| Setup | Strict pass | 95% CI | Paired McNemar p |
|---|---:|---:|---:|
| Round 9 retrieval ON | 30/41 (73.2%) | 58.5–85.4% | 1.000 vs OFF |
| Round 9 retrieval OFF | 29/41 (70.7%) | 56.1–82.9% | same comparison |
| Round 10 Flash | 28/41 (68.3%) | 53.7–82.9% | 1.000 vs Pro |
| Round 10 Pro | 28/41 (68.3%) | 53.7–82.9% | same comparison |

ON/OFF has 2 vs 1 discordant pairs; ON−OFF is +2.44 percentage points (95% CI −4.9 to +12.2). Flash/Pro has 3 vs 3; Flash−Pro is 0 points (−12.2 to +12.2).
The honest result is **about 70% strict pass**, with wide uncertainty: neither comparison is statistically distinguishable at n=41; this does not prove equivalence. Flash is chosen for the large observed latency advantage, p95 about **4 s vs 7.4 s** (coordinator-supplied observations, not a latency significance test).
At n=41, six disagreements all favoring one setup, with all other pairs agreeing, give p=0.03125; five give p=0.0625. This is a best-case discordance count, not a sample-size/power calculation.
[Script and complete round results](../../../reports/submission/T9-S1-stats.md); [verdicts](../../../reports/behavior/verdicts.json), [stats JSON](../../../reports/behavior/stats.json). Rounds 3–8 have aggregate intervals only; no invented pairing or pooling across rounds.

### Retriever diagnostic

Leave-one-out on **649 active stored examples**, with no new embeddings, excludes self and exact duplicate text. Relevance requires the same tool, service, enclosure, voltage and torque operators, including missing fields; torque values/units and non-search codes/terms are deliberately outside this pattern metric. P@k is relevant neighbors divided by k (empty slots miss); MRR@5 averages 1/rank of the first relevant neighbor, or zero. Coverage means at least one returned example, not at least one relevant example.

| Cosine cutoff | P@1 | P@3 | P@5 | MRR@5 | Coverage |
|---|---:|---:|---:|---:|---:|
| None | 47.6% | 41.1% | 38.2% | 0.563 | 100% |
| Current 0.70 | 47.0% | 39.3% | 35.6% | 0.551 | 98.3% |

Unfiltered MRR rises from 0.476/0.546/0.563/0.570 at k=1/3/5/8: k=5 is a provisional context cap with diminishing gains, not a proven optimum. At 0.70, precision among returned neighbors is still 38.2%; this snapshot does **not** justify the threshold as a relevance filter. The [full sweep](../../../reports/behavior/retrieval.json) exposes the coverage trade-off. Fifteen queries have no relevant peer; related phrases can remain across the split, and the coarse labels cannot certify correct recommendations. Validate on fresh labeled queries before tuning; production settings are unchanged.

### Improving retrieval

We compared five approaches on the same 649-example leave-one-out bank. **Strict** requires the same tool, service, enclosure, voltage and torque operators; **prompt-useful** requires the same tool and set of non-null argument fields, with service/enclosure mappings preserved while other values may differ. A fixed seed selects 129 queries for tuning and 520 for validation within this bank. This is not a fresh-conversation test.

| Variant | Strict P@1 / P@3 / P@5 | Strict MRR@5 | Useful P@1 / P@3 / P@5 | Useful MRR@5 | Extra ms/query | Extra API calls |
|---|---|---:|---|---:|---:|---:|
| A: dense | 47.6 / 41.1 / 38.2% | 0.563 | 47.5 / 41.2 / 37.8% | 0.554 | 0 | 0 |
| B: metadata, w=0.02 | 51.8 / 43.4 / 40.1% | 0.598 | 47.5 / 40.8 / 37.8% | 0.552 | 0.42 | 0 |
| C: BM25 + dense, RRF 60 | 48.5 / 41.2 / 38.1% | 0.572 | 44.1 / 38.1 / 35.6% | 0.534 | 6.77 | 0 |
| D: MMR on A, λ=0.6 | 47.6 / 41.0 / 38.3% | 0.565 | 47.5 / 41.1 / 37.9% | 0.556 | 0.32 | 0 |
| E: masked quantities | 43.0 / 40.1 / 37.5% | 0.524 | 48.1 / 43.1 / 39.2% | 0.557 | 0.01 | 0 |
| E + B, w=0.02 | 49.8 / 42.5 / 39.1% | 0.572 | 48.7 / 42.9 / 39.0% | 0.558 | 0.34 | 0 |

All precision values are percentages; no cosine cutoff is applied, matching the original baseline. Times are measured local ranking/masking overhead, excluding DB/provider latency; zero extra API calls means reusing/replacing the existing query embedding, not a free retrieval service. Grids: w=0.02/0.05/0.1/0.2/0.4 and λ=0.5–0.9. **Keep dense:** no variant improves useful P@5 by the required 5 points while also improving strict P@5; the best useful gain is only 1.4 points and loses strict precision. The validation split reaches the same decision. No runtime/config default changed and the masked dataset stays inactive; the v7 scripted replay with actual dense SQL retrieval preserves every OFF filter when ON. [Full experiment, limits and Google usage ledger](../../../reports/submission/T9-S2-retrieval.md).

### Impact and why integrity comes first

Provost's expected-value idea is to weight each outcome's benefit/cost by its probability, rather than treating every error equally. The following assumptions are **illustrative relative units**, not measured money or client-approved values; the client must set real costs and we have not estimated a financial return.

| Outcome | Illustrative relative benefit/cost | Reason |
|---|---:|---|
| Correct recommendation | +1 | Saves an engineer's manual table lookup |
| Clarification question | −0.1 | Small extra interaction cost |
| Integrity error: wrong enclosure or service | −100 | Potentially very costly wrong selection |

Expected utility would be `P(correct) × 1 − P(clarification) × 0.1 − P(integrity error) × 100`; strict pass rates do not estimate those separate probabilities. This is why the design trades some convenience for verification and confirmation.

## Behavior evaluation

T8/T9 rounds use held-out sets frozen before reading answers, six personas and strict independent review of complete conversations. This table and the model comparison were supplied by the coordinator for this delivery; linked reports document subsequent repairs and local verification. Their scripted replays are not new provider measurements.

Rounds overlap in method but not in conversations. Rounds 1–2 used a looser review and are not pooled with this table. ON/OFF compares the same cases within each round; changing rounds changes the set and does not isolate a causal code improvement. Strict review considers interpretation, requirement retention/coverage, context safety and usefulness as well as figures.

| Round | Config | Strict pass |
|---|---|---|
| 3 | rules | 21/45 (47 %) |
| 4 | rules | 24/45 (53 %) |
| 5 | rules | 21/44 (48 %) |
| 6 | rules | 28/43 (65 %) |
| 7 | rules | 24/43 (56 %) |
| 8 | ON / OFF | 25/41 (61 %) / 26/41 (63 %) |
| 9 | ON / OFF | 30/41 (73 %) / 29/41 (71 %) |
| 10 | retrieval ON, after round-9 fixes | 28/41 (68 %) |

Round 9 differs by **one conversation** (73% versus 71%); round 8 favored OFF. Round 10, retrieval ON after round-nine fixes, scored **28/41 (68%)**. Observed quality on unseen held-out conversations is therefore **68–73% strict pass (rounds 9–10)**, not demonstrated causal improvement or statistical superiority for embeddings. Every response in those two rounds was under **10 s**, with **3.7–5.1 s p95**. The coordinator's review reports no wrong catalogue numbers in any round.

Historical pre-T10 cohorts showed four failure classes: paraphrased or Spanish service/enclosure cues can be missed and become clarifying questions; mid-conversation retractions or added bounds are sometimes not merged; site-hazard judgment can err both ways, so the assistant asks for confirmation and always shows the enclosure; and some single-field or out-of-scope questions receive more detail than asked. Engineers must confirm **active filters, service, enclosure and hazardous-area classification before ordering**. T9 records 6/7 ON/OFF integrity failures in round 9: integrity includes requirements/selection, not just figures. Round 10 is live evidence after the fixes; OpenRouter results are documented above; offline tests do not extend that acceptance.


### Turn-level and everyday-use view

An independent reviewer re-scored round 10 (`gemini-3.6-flash`, retrieval ON): the same 41 unseen conversations, containing 68 turns. These supplied results are another view of the recorded answers, not a new provider run; intervals below are Wilson 95% intervals.

| Measure | Result | Wilson 95% interval/bound |
|---|---:|---:|
| Correct turns | 56/68 = 82.4% | 71.6–89.6% |
| Integrity failures | 7/68 = 10.3% | 5.1–19.8% |
| Shape failures | 4/68 = 5.9% | Not supplied |
| Memory failures | 1/68 = 1.5% | Not supplied |
| TYPICAL conversations fully correct | 18/19 = 94.7% | 75.4–99.1% |
| ADVERSARIAL conversations fully correct | 12/22 = 54.5% | 34.7–73.1% |
| Wrong catalogue numbers | 0/491 checked values | Error ≤0.78%; accuracy ≥99.2% |

**TYPICAL** means a part-number lookup or follow-up, a clear requirement in catalogue terms (abbreviations allowed), a comparison or recommendation, or a simple correction. **ADVERSARIAL** means a paraphrase-only requirement, a misspelled or mixed-language requirement, an implied hazard or safe-site judgment, out-of-scope or injection, a rephrase request, or a mid-conversation retraction.

Every integrity failure was an unapplied constraint, never a wrong number; five of seven involved paraphrased or Spanish service wording. All replies took under 10 s, with a maximum of **5.03 s**. The numeric accuracy bound uses the review's sampling assumptions; it is not a guarantee for new conversations.

The turn-level review accepted a few borderline turns, giving **30/41 conversations** versus the earlier stricter **28/41 (68.3%)**; report both because the scoring standard differs.

### Model selection

OpenAI-compatible client, measured through Google; this historical selection predates the OpenRouter acceptance above. On the same **44 conversations**, `gemini-3.6-flash` scored **21/44**, `gemini-3.8-flash` **25/44**, and `gemini-3.1-pro` **28/44**. Pro had **7.1 s p95**, including an **11 s** turn. After round 6, 3.6 Flash was retained: **28/43** versus 3.8 Flash's **26/43**. This is a quality/latency decision on these sets, not a universal model ranking. Embeddings use `gemini-embedding-2`; OpenRouter ID `google/gemini-embedding-2`, whose OpenRouter compatibility was subsequently checked as documented above.

### Provenance and evaluation leakage

The v7 bank stores phrasings/interpretations and every source ID, never evaluated answers or catalogue figures as knowledge. Use a fresh set or `EMBEDDING_EXCLUDE_SOURCES` to exclude all held-out associations before distance ranking/LIMIT. Immutable versions/manifests prevent silent label replacement; conflicts deactivate rows and historical provenance survives. Once a failed case enters the replay/bank, it becomes regression/calibration and cannot count again as unseen acceptance. Round-nine replay retains queries/decisions and hashes and is not loaded into the bank. [T9 details](../../../reports/submission/T9-embeddings.md).

### Current local evidence

[T8](../../../reports/submission/T8-backend.md), [T8b](../../../reports/submission/T8b-backend.md), [T8c](../../../reports/submission/T8c-backend.md), [T8d](../../../reports/submission/T8d-backend.md), [T8e](../../../reports/submission/T8e-backend.md), [T8f](../../../reports/submission/T8f-backend.md), [T8g](../../../reports/submission/T8g-backend.md) and [T8h](../../../reports/submission/T8h-backend.md) record deterministic evolution, not pooled model acceptance.

[T9 embeddings](../../../reports/submission/T9-embeddings.md): **484 Python tests, 2 optional skips; 446 scripted scenarios without failures**, 41 conversations per mode/138 total replay turns, local SQL, schema and scanner. [T8 Android](../../../reports/submission/T8-android.md): 51 JVM; [T9 Android](../../../reports/submission/T9-android.md): **74 JVM and debug/release APKs**, without device or actual voice execution. These are report results, not suites rerun by the documentation task. The following T7/v6 sections are historical; those cohorts can overlap and must not be pooled with T8/T9.


## Run locally

Start Compose from the [README](../../../README.md); then create and activate a Python 3.12 environment from the repository root. Run only the block for your shell:

```sh
# macOS/Linux
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
SERIES76_TEST_DB=1 python -m unittest discover -s tests
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
python -m unittest discover -s tests
```

Current offline gate: **v7, 453/453 scripted scenarios**. In the activated backend Python environment, after Compose startup:

```text
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
python scripts/check_tool_schemas.py
python scripts/verify_catalog_db.py
```

The seven T9-R1 scenarios cover recommendations after comparisons and shown lists, new requirements, Spanish intent, ties and no qualifying model. The [recommendation report](../../../reports/submission/T9-R1-recommendation.md) records the three complete probe answers; [regression tests](../../../tests/test_shown_recommendation.py) assert their exact text and reject invalid or unseen winners. Replay safety checks use the validated CSV independently of the SQL ranking implementation.

The catalogue verifier logs in with the public TEST ONLY demo account and sends its Bearer token to protected endpoints. It defaults to `http://127.0.0.1:${API_PORT:-8000}`, using process `API_PORT` before the local template setting; `--base-url http://127.0.0.1:18000` overrides it explicitly. Its SQL, full database test suite and HTTP stages must all pass for exit 0. Existing demo passwords are never reset.

The v6 selfcheck is historical: its presentation expectations predate T8 and it no longer passes this release. Its files and archived 103/103 result are preserved, not the current gate. Scripted checks do not establish provider interpretation quality.

## PostgreSQL connection

Tests connect to Compose service `db` through host loopback `127.0.0.1:5432`, not Docker hostname `db`. The connection helper `backend.catalog.cli.local_environment()` reads the repository-root .env without printing it: PGHOST defaults to 127.0.0.1; POSTGRES_PORT → PGPORT (default 5432), POSTGRES_DB → PGDATABASE (default series76), POSTGRES_USER → PGUSER (default series76), POSTGRES_PASSWORD → PGPASSWORD. Existing process PG* values take precedence. Use the same local values that initialized the Compose volume; changing .env does not reset its password. CI supplies PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD directly in the workflow. Without SERIES76_TEST_DB=1 the database tests skip.

In the activated backend environment:

```sh
python scripts/verify_catalog_db.py
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
```

OCR uses a second environment: follow [ingestion setup](ingestion.md#rerun), then run these commands with that OCR environment active:

```sh
python -m unittest discover -s tests -p test_dynamic_geometry.py
python -m unittest discover -s tests -p test_pipeline_safety.py
python scripts/verify_ingestion.py
```

Android (Windows; on macOS/Linux substitute `sh mobile/android/gradlew` for the .bat wrapper):

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
./mobile/android/gradlew.bat -p mobile/android connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest
```

Instrumented tests require a running emulator. The excluded live-auth helper needs its own explicit test-account setup; see [`verify_android_auth.py`](../../../scripts/verify_android_auth.py). [`verify_mobile_backend.py`](../../../scripts/verify_mobile_backend.py) exercises controlled HTTP/restart paths; neither establishes real-model understanding. Preserve the DB volume. An offline selfcheck validates expectations, not model quality.

## T7 / v6 offline acceptance

Historical section: v6 presentation expectations predate T8 and no longer pass this release; run v7 above. The v6 cases/configuration remain unchanged.

[v6 cases](../../../config/agent_acceptance_cases_v6.json) retain all 63 v5 scenarios and add the 40 EC scenarios from the [edge-case specification](../../evaluation/edge-case-suite.es.md). Historical v5 files remain unchanged; v6 records approved presentation changes and exploratory policies. Expectations use the validated CSV; scripted decisions stay out of real-model prompts.

[Backend evidence](../../../reports/submission/T7-backend.md): 202 Python tests, 2 optional OCR/geometry module skips; 103/103 selfcheck scenarios; six mutation checks; keyless rebuild and `/ready` 200. [Android evidence](../../../reports/submission/T7-android.md): 40 JVM tests and debug APK build, not device visual acceptance. These are recorded worker results, not a claim that this documentation edit reran the suites.

With PostgreSQL running and the backend Python environment active:

```sh
python -m unittest discover -s tests -p test_acceptance_v6.py -v
python scripts/check_tool_schemas.py
```

The independent CSV oracle checks values, N/A, scopes, full candidate sets, units/winners and public interaction shape. Corruption tests first accept a valid result, then require failure for `gt → gte`, N/A → zero, wrong unit, dropped requirement, substituted code (even with the same numeric value), and a dropped upper range bound. This tests whether the scorer catches these specific faults; it does not prove universal detection or real-model comprehension. [Scorer](../../../scripts/acceptance_contract.py), [mutations](../../../tests/test_acceptance_v6.py), [captured examples](../../../reports/submission/T7-scenarios.json).

Before a live cohort, run the offline schema gate below; only with explicit paid-call authorization run the one-call live preflight. Freeze code/cases/catalogue/config, count every transport attempt in the ledger, and keep provider failure separate from semantic failure. The USD 1.00 v6 configuration cap is not permission to spend. Production retries are bounded by the shared deadline; the schema preflight itself never retries.

**v6 real-model result (coordinator, Google `gemini-3.6-flash`, 2026-11-03):** 102/103 scenarios passed after fixes, across cohorts `v6` (all 103: 88 passed, 9 failed, 6 provider-only), `v6b` (15 reruns after code fixes: 10 passed) and `v6c` (4 reruns: 4 passed). Remaining: `t6_manual_03`, an accepted interpretation difference (a new outdoor search after "at least 70 Nm" was read as a refinement that keeps 70 Nm and asks for the service). Integrity failures (numbers, units, N/A, operators, codes): 0. Usage-based cost: USD 0.1837 (v6 + v6b + v6c); OpenRouter calls: 0. Every live rerun used a new cohort; recorded results were never edited. Evidence: `reports/agent_acceptance/v6*/summary.json` (local, git-ignored) and [T7-v6-repair.md](../../../reports/submission/T7-v6-repair.md), [T7-v6b-repair.md](../../../reports/submission/T7-v6b-repair.md).

## Real-model evidence

[Agent cohorts v1–v4](../../evidence/agent_acceptance.md), production A+ client through Google OpenAI-compatible API, zero OpenRouter calls:

| Cohort | Passed/scenarios | Quality failures | Provider-only failures |
|---|---:|---:|---:|
| v1 | 25/27 | 2 | 0 |
| v2 | 38/43 | 2 | 3 |
| v3 | 46/51 | 3 | 2 |
| v4 | 50/55 | 1 | 4 |

Cohorts overlap: never add them as independent samples. v4 strict power-limit correction is not rechecked with a real model; four provider-error cases remained unevaluated. Initial native-Google model selection used a separate frozen development corpus and historical [model comparison](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval). It suggested Gemini 3.6 Flash on qualitative technical fidelity; it does not validate availability, pricing or routing today.

Method: freeze corpus/code/config/catalogue hashes before inference; keep expected arguments out of prompts; score tool/arguments, extra filters, SQL facts and authorized clarifications. Record token usage, latency and provider errors independently. Reserve budget before calls, retain reservations for unknown usage, use one controller. Historical cohort settings are not the T7 transport retry policy. Restore archived experiments in a separate checkout for reproduction; paid runs require explicit approval. The [A–E comparison](../../evidence/architecture_comparison.md) is inconclusive, not a ranking.

## CI

[CI workflow](../../../.github/workflows/ci.yml) provisions PostgreSQL, installs backend dev dependencies, migrates, loads catalogue/glossary and runs unittest; Android runs JVM tests on JDK 17. It does not run paid inference, full OCR inference or emulator instrumented tests. Workflow presence is implementation evidence, not proof of the latest remote CI run. This task runs local checks only.

## Tool-schema preflight before any cohort

Run `python scripts/check_tool_schemas.py` offline first. It builds the real four production tools without a database or credentials and prints compact bytes, enum values, arrays, required fields, depth, numeric range keywords and lookup object arrays. Offline guards cap enums/arrays/required/depth at the pre-T6 counts (108/6/5/7) and reject numeric ranges, nullable unions/references and object arrays in get_actuator. Byte size alone did not predict the provider's cumulative schema limit.

Only after explicit paid-call approval, run `python scripts/check_tool_schemas.py --live` with OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL and optional OPENROUTER_BASE_URL already in the process environment. It never loads .env or prints the key, provider response or exception body; it sends exactly one request with all four tools and the production system/glossary prompt, disables tracing, performs no tool/SQL execution and has no retries. A 400 or other failure exits non-zero: stop before the cohort. A successful preflight checks schema acceptance only, not conversation quality. Re-run after any tool-schema change; the OpenRouter preflight results above record the tested schema, and do not cover later schema changes.

Where: [preflight script](../../../scripts/check_tool_schemas.py), [complexity/one-call tests](../../../tests/test_tool_schema_budget.py), [metadata-only readiness script](../../../scripts/check_openrouter.py).

## Where in the code

- [tests/test_agent_scenarios.py](../../../tests/test_agent_scenarios.py#L1)
- [scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L1)
- [scripts/verify_ingestion.py](../../../scripts/verify_ingestion.py#L1)

## Known limits

No automatic test establishes arbitrary-language correctness or heterogeneous OCR accuracy. Local DB tests may create scoped test records or rollback transactions. Post-fix held-out v12 and the full Android → real model → SQL → Android path remain pending.
