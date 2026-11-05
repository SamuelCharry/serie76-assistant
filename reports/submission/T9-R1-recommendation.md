# T9-R1 - Recommendations over the shown set

Base: `20d1b3d`, branch `release/submission`.
Code and tests: `fd43ce8` (`fix(agent): recommend within the shown catalogue set`).

## Repair

- Common English/Spanish recommendation questions resolve directly against `on_screen`, with the previous comparison as a fallback. The model may signal selection intent and priority through existing tools; it cannot introduce a replacement set or unsupported numeric requirements.
- Active filters and same-turn requirements pass through the existing normalizer, quantity coverage guard, bound merge and validation. SQL rows failing any requirement are excluded before sorting, with measured values and units in the explanation. Strict bounds, frequency scope, torque ranges and rate ranges are retained.
- Ranking uses the requested current, operating time, torque, power, duty or cycles priority. Otherwise it retains the declared default or active ranking preference. Ties name the next stable ranking key. Reasons reuse the comparison direction table and show up to three advantages plus the eligible runner-up's main trade-off.
- A separate post-condition reloads selected SQL rows and verifies shown-set membership, all requirements and agreement between the verdict and the first recommendation item. Deliberately corrupted winners and an eligible but unseen code are rejected in tests.
- If no shown model qualifies, the payload has zero recommendation items. The nearest is named as failing, using fewest failed constraints followed by normalized numeric distance and part number; requirements are never relaxed silently.
- Selection advice such as `which should I buy?` no longer receives the order-placement limitation. Explicit price, order or delivery requests retain their limitations. Unspecified torque and unresolved supply choices are stated as assumptions, not invented requirements.
- The earlier `6354364` comparison cleanup fix is preserved: zero hidden fields are removed as a whole count, so `10 identical fields hidden.` survives. Both the dedicated presentation suite and the pair probe assert this sentence.

No mobile files, v6 fixtures, private configuration, provider inference or PostgreSQL volumes were changed. Common selection wording is deterministic; unusual wording may still need the model to signal intent. Spanish input is recognized; public output follows the application's existing English presentation contract.

## Scripted probe answers

These are complete response strings asserted byte-for-byte against the fixture by `tests/test_shown_recommendation.py`, using actual PostgreSQL catalogue rows and forbidding model construction on each recommendation turn. They are scripted verification, not a claim of live provider interpretation.

### R-A

Compare 761A00-11300000/A vs 761B00-11300000/A -> which one do you recommend and why?

```text
I recommend 761A00-11300000/A: Weatherproof; FLA at 50 Hz 1.1 A. Ranked by lowest FLA, then shortest operating time, then part number. Versus 761B00-11300000/A: FLA at 50 Hz: 1.1 A vs 1.2 A; FLA at 60 Hz: 1.2 A vs 1.3 A; Operating time at 50 Hz: 20 s vs 23 s. Choose 761B00-11300000/A only if its On/Off torque advantage (880 in-lb / 100 Nm vs 700 in-lb / 80 Nm) matters more than the stated priority. Assumes no torque requirement; tell me the torque you need.
Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
```

### R-B

on/off 220 V weatherproof at least 150 Nm -> compare the top 2 -> which is better for me?

```text
I recommend 762A00-11320000/A: On/Off torque 150 Nm; meets Weatherproof, On/Off service, 220 V, torque ≥ 150 Nm. Ranked by closest torque at or above 150 Nm, then lowest FLA, then shortest operating time, then part number. Versus 762B00-11320000/A: FLA at 50 Hz: 1 A vs 1.1 A; FLA at 60 Hz: 1 A vs 1.1 A; Operating time at 50 Hz: 21 s vs 29 s. Choose 762B00-11320000/A only if its On/Off torque advantage (1750 in-lb / 200 Nm vs 1330 in-lb / 150 Nm) matters more than the stated priority. Assumes no preference on phase count; tell me if that matters.
```

### R-C

Compare 762A00-11320000/A vs 763A00-11320000/A vs 764A00-11320000/A -> I need at least 200 Nm on/off and low current, which should I buy?

```text
I recommend 763A00-11320000/A: Weatherproof; FLA at 50 Hz 1.3 A; meets On/Off service, torque ≥ 200 Nm. Ranked by lowest FLA, then shortest operating time, then part number. Versus 764A00-11320000/A: FLA at 50 Hz: 1.3 A vs 3 A; FLA at 60 Hz: 1.3 A vs 3.2 A; Operating time at 50 Hz: 29 s vs 33 s. Choose 764A00-11320000/A only if its On/Off torque advantage (6650 in-lb / 750 Nm vs 2650 in-lb / 300 Nm) matters more than the stated priority.
762A00-11320000/A is out: On/Off torque 150 Nm < 200 Nm.
Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
```

## Verification

The full Python suite uses `SERIES76_TEST_DB=1`; offline processes explicitly disable provider credentials, embeddings and tracing. Seven replay scenarios cover the three probes, Spanish selection, shown-list low power, a priority tie and no eligible model; the replay checks recommendations against the independent validated-CSV eligibility oracle.

| Gate | Result |
|---|---|
| Full Python suite | 507 tests, 2 optional OCR module skips, exit 0; 205.510 s on the final code. |
| New recommendation regressions | 16 tests passed, including exact probe strings, Spanish intent, list scope, ties, no match, strict/frequency bounds, retained torque ceiling, cycle range, SQL eligibility, corrupted/unseen winners and buying advice. |
| v7 selfcheck | 453/453 scenarios, 760 turns, exit 0; all seven T9-R1 additions passed. |
| Public-text scanner | Zero findings across the replay's 760 checked turns; independent rescan of 89 retained response payloads also found zero issues. |
| Offline schema | Exit 0; arrays 6, bytes 5487, depth 7, enum values 107, required 2; forbidden nodes, numeric ranges and lookup object arrays all zero. Identical to the baseline budget. |
| Relative-link checker | 734 links/anchors checked, 0 broken, exit 0. |
| Coordinator rebuild / readiness | Exact `start_emb.py on build` command completed with exit 0; `http://127.0.0.1:8000/ready` returned HTTP 200. |
| Keyless example-bank dry-run | 658 examples + 100 anchors = 758 texts, 24 planned batches; model null, input-only scope, no inference. |

The [focused replay evidence](t9-r1-evidence/recommendation-replay.json) includes all seven new scenarios and their rendered payloads. The three probe recommendation turns took 62, 44 and 55 ms respectively in this scripted HTTP replay; all seven took 34-62 ms. These are local observations, not production latency guarantees. Exact expected strings are also retained in the [fixture](../../tests/fixtures/shown_recommendation_answers.json).

[Machine-readable gate summary](t9-r1-evidence/gates.json). The rebuild used the coordinator-provided script without changing private configuration; readiness verification made no inference call. No live provider acceptance or device work was performed.
