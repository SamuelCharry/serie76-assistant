# T9-S2: retrieval variants, dense retained

> Update 2026-11-05: this historical report retains its original run scope and numbers; OpenRouter acceptance and bank reload are now completed, with provisional model defaults and pending post-fix held-out v12 documented in [README Models](../../README.md#models-design-and-limitations).

**Decision: keep the existing dense retriever.** None of the tested variants meets the adoption rule on both definitions. No runtime mode, default, threshold, concept classifier, additive-filter policy or tool schema changed; the experimental rankers are used by the offline evaluator only. The existing `EMBEDDINGS_ENABLED` flag still controls retrieval. Since no variant qualifies, no unproven production mode is exposed.

## What the two labels mean

**STRICT:** same tool, service, enclosure, voltage and torque operators, including missing fields and both bounds; torque magnitudes/units are ignored, exactly as in T9-S1.

**PROMPT-USEFUL:** same tool and same set of non-null interpretation argument keys, with equal service/enclosure mappings whenever stated, while other values may differ. This includes labeled control/focus keys and ignores numeric values and torque operator values; it is a template-usefulness definition, not product suitability. For example, otherwise identical on/off requests at 110 V and 220 V can be prompt-useful to each other but are not strict matches. Query labels are used only for scoring, never to rank candidates. Both definitions are label-derived approximations, not fresh independent relevance annotations.

## Protocol and one results table

649 active `gemini-embedding-2` examples, the same original bank as T9-S1; self and exact original-text duplicates are excluded before ranking. Every example is a query, with its stored vector reused, and missing slots count as misses. All variants below use no similarity cutoff, matching the requested S1 baseline. A fixed seed (20261104) selects 129 tuning queries and leaves 520 validation queries; candidates remain the rest of the bank. This split prevents tuning on the validation query labels, but related phrases may remain as neighbors, so it is not an independent generalization test.

Selection: maximize tuning prompt-useful P@5, then strict P@5, then first grid entry on a tie. Adoption additionally requires at least +5 percentage points useful P@5 and +2 points strict P@5 on both all-query and validation scores, with no extra query API call. The 2-point strict margin makes the requested improvement in both definitions explicit. No configuration reaches the required useful margin even before that extra strict check.

| Variant | Strict P@1 | P@3 | P@5 | MRR@5 | Useful P@1 | P@3 | P@5 | MRR@5 | Extra ms/query | Extra API calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A dense | 47.6% | 41.1% | 38.2% | 0.563 | 47.5% | 41.2% | 37.8% | 0.554 | 0.00 | 0 |
| B w=0.02 | 51.8% | 43.4% | 40.1% | 0.598 | 47.5% | 40.8% | 37.8% | 0.552 | 0.42 | 0 |
| C hybrid | 48.5% | 41.2% | 38.1% | 0.572 | 44.1% | 38.1% | 35.6% | 0.534 | 6.77 | 0 |
| D lambda=0.6 | 47.6% | 41.0% | 38.3% | 0.565 | 47.5% | 41.1% | 37.9% | 0.556 | 0.32 | 0 |
| E masked | 43.0% | 40.1% | 37.5% | 0.524 | 48.1% | 43.1% | 39.2% | 0.557 | 0.01 | 0 |
| E+B w=0.02 | 49.8% | 42.5% | 39.1% | 0.572 | 48.7% | 42.9% | 39.0% | 0.558 | 0.34 | 0 |

Times are observed mean **extra local ranking/masking CPU time per query**, excluding provider and SQL latency; they are a single local diagnostic under concurrent test load, not production latency guarantees. Baseline dense computation amortized 30.47 ms/query in the offline exact pairwise implementation. Zero extra API calls means one existing query-embedding call reused, or replaced by a masked-query call for E; no live query latency was measured. Any future E adoption would also need to revalidate concept-anchor classification when changing its query vector. This experiment leaves that classifier untouched.

The untuned split agrees with the decision: useful P@5 is 37.7% for A, 37.7% for B, 35.9% for C, 37.8% for D, 39.2% for E and 39.2% for E+B. The largest whole-bank useful gain is only 1.4 points (E), while strict P@5 falls from 38.2% to 37.5%. B improves strict P@1 but does not improve useful P@5 enough. This is evidence against adding these complexities now, not proof that every possible reranker is useless.

[Machine-readable full metrics, tuning grids and validation scores](../behavior/retrieval-variants.json). Original bank fingerprint before and after the experiment: `badf049f3faab933fafdd2c129c11d5633acb031c901b198bebdca70ff21aa25` (canonical JSON with ASCII escapes); the original S1 fingerprint uses unescaped Unicode. Both checks confirm that original rows/vectors were preserved.

## What each variant actually does

- **A:** exact cosine over stored vectors, stable ID tie-breaks.
- **B:** the existing `policy.colloquial_requirements` and `requirement_coverage.apply` read query text, with no semantic suggestions; extract service, enclosure, voltage, phases and torque operators. Rerank the first 20 dense neighbors with `cosine + w * agreements - w * conflicts`. A field absent from a neighbor neither agrees nor conflicts. Grid `w = 0.02, 0.05, 0.1, 0.2, 0.4`; zero is already A. Selected w=0.02.
- **C:** pure-Python BM25 (k1=1.5, b=0.75), accent folding and domain tokens including on/off, xp, wp, 110v and 24v; query/self exclusions also apply to BM25 document-frequency and length statistics. Combine dense and lexical ranks with `1/(60+rank)` from each list; zero lexical scores cast no vote. No extra dependencies.
- **D:** MMR on the tuning winner among A-C (A), first 20 candidates, lambda grid 0.5/0.6/0.7/0.8/0.9. Min-max normalize the candidate relevance score and penalize maximum original cosine to an already selected example. Select five; lambda=0.6 wins the stated tie-break rule.
- **E:** replace explicit voltage/torque/frequency quantities with `<VOLTAGE>`, `<TORQUE>`, `<FREQ>` before embedding. Original text and labels stay unchanged for self exclusion and scoring; 649 rows collapse to 623 unique masked strings. The same masked vectors serve as leave-one-out queries, so there is no second embedding call per query. Masked-text collisions are intentional and can inflate near-template similarity; they do not prove performance on unseen language.
- **E+B:** the same metadata algorithm and grid over the first 20 masked neighbors, using the original query text for deterministic detection; selected w=0.02.

## Authorized embeddings and preserved data

Google only, `gemini-embedding-2`, 768 dimensions, the exact supplied `with_google.py` wrapper and Google OpenAI-compatible embedding endpoint. No chat/LLM requests or OpenRouter requests. The [Google compatibility documentation](https://ai.google.dev/gemini-api/docs/openai#embeddings) shows the scalar-input embedding route used after diagnosing the adapter response.

There were two unsuccessful 64-text list requests (no usable `data`) and one individual response rejected by the initial strict index check. The compatibility response omits the zero index and token usage; the repaired parser accepts an omitted index only for a single returned embedding and validates all 768 numeric values. It uses one text per request, at most four concurrent requests, no automatic transport retries, durable reservations and checkpoints. Failed reservations are retained, not silently erased.

Final accounting: **623 successful scalar requests, 3 unsuccessful/locally rejected requests, 626 requests total and 752 submitted texts** including failed reservations, approximately the authorized 749 texts. The provider supplied no token usage, so exact tokens and billed USD are **unknown**, not zero; the task's under-USD-0.01 estimate is not a verified invoice. [Compact manifest and failed reservations](../behavior/masked-v1-manifest.json). A completed-cache rerun made zero new requests and left the request count unchanged.

The 649 masked rows are stored separately under model/version `gemini-embedding-2/masked-t9s2-v1`, all **inactive**, with a dataset fingerprint. The original 649 active rows and all 100 original concept anchors remain unchanged. No migration or volume reset was performed. Local vector/checkpoint cache is ignored by Git; vectors remain in the separate PostgreSQL namespace. Rerunning embedding generation against a missing cache is a paid operation requiring explicit authorization; ordinary evaluation reads stored data only.

## Reproduction and gates

```text
python scripts/eval_retrieval.py --definition both --out reports/behavior/retrieval-both.json
python scripts/eval_retrieval_variants.py
```

The first command reports both relevance definitions with the original k/threshold sweep; the second reports all variant results from stored original/masked vectors. Use the backend environment and existing local database. The evaluator loads database settings through `backend.catalog.cli.local_environment()` and never displays credentials.

| Gate | Verified result |
|---|---|
| Full Python suite, real local DB enabled | 524 tests, 2 optional dependency skips, exit 0; 338.839 s |
| Focused ranking/Google-parser/additive replay tests | 9/9 passed, exit 0; 126.700 s |
| v7 selfcheck | 453/453 scenarios, no failures, exit 0 |
| Tool schema unchanged | Exact metrics match the prior T9-R1 baseline: 5487 bytes, 107 enum values, 6 arrays, depth 7, 2 required; forbidden nodes, numeric ranges and lookup object arrays all zero |
| Links/anchors | 761 checked, 0 broken, exit 0 |
| Required backend rebuild | Supplied start_emb.py on build command completed, exit 0 |
| Readiness after rebuild | GET http://127.0.0.1:8000/ready returned HTTP 200 |
| Original bank preservation | Original S1 SHA-256 still 99994b5a7228bd1d57bb5e56931456545e4fa103ca1058cee46b7639c6e45aeb; 649 active original + 649 inactive masked rows; 100 original concept anchors |
| CLI cross-check | Both definitions from eval_retrieval.py exactly match variant A P@1/P@3/P@5; all scripts completed |
| Diff hygiene | git diff --cached --check clean; no production agent/embedding-path/schema/config changes |

The additive test replays all 760 v7 turns in both modes, uses a real PostgreSQL dense-example query and deterministic fake vectors, injects a conflicting example, and asserts that every OFF filter remains equal in ON. Scripted chat decisions and an abstaining concept classifier isolate the example-retrieval effect; it does not prove arbitrary model interpretation or semantic-classifier safety. The full suite also retains the existing classifier/normalizer additive tests.

Executed with `.venv-chat/Scripts/python.exe`: `-m unittest discover -s tests` with `SERIES76_TEST_DB=1`; focused `-m unittest discover -s tests -p test_retrieval*.py -v`; `scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json`; `scripts/check_tool_schemas.py`; `scripts/check_docs_links.py`. In offline gate processes provider keys/model names were cleared and embeddings/tracing disabled; test fixtures locally override retrieval with fakes. Two optional dependency skips and non-fatal tracer callback warnings are recorded, not counted as live-provider evidence.

Required rebuild command, executed exactly:

```text
python <local-scratch>\start_emb.py on build
```

[Ranking code](../../backend/conversation/retrieval_ranking.py), [variant evaluator](../../scripts/eval_retrieval_variants.py), [bounded Google loader](../../scripts/embed_masked_bank.py), [known-answer tests](../../tests/test_retrieval_ranking.py), [v7 additive replay](../../tests/test_retrieval_v7_additive.py).

Remaining: new independent query relevance labels, downstream prompt-quality validation, measured production latency and provider billing confirmation. There is no claim of a live-chat improvement, and no push was performed.

Co-Authored-By: Codex <noreply@openai.com>
