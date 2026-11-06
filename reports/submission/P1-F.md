# P1-F — final product eligibility guard (v15 diagnostic)

Status: implemented and locally verified; both requested gates exit 0 on identical source.
No paid inference, provider metadata calls, `.env` reads, catalogue changes, or
volume removal. Baseline: `release/submission` at `503d25e8ec04ad4478d76f87ad60e06d2709b1d1`;
`git pull --ff-only` reported up to date. The original frozen v15 files were not edited.

## Recorded failures and causes

Recovered **131/131** response traces by `message_id` from `series76.messages`,
inside `SET TRANSACTION READ ONLY` with rollback. The compact recorded-decision
fixture is [p1_f_recorded_decisions.json](../../tests/fixtures/p1_f_recorded_decisions.json).
It distinguishes actual Flash decisions from deterministic turns; a missing model
decision is never replaced with an invented Flash interpretation.

| Case | Message | Root cause | Repaired behavior |
|---|---|---|---|
| L1-01, turn 3 | `646aed8b-dc9a-4fb8-ba50-19a4bb8e9b10` | **Deterministic `metric_verdict`, no Flash call on this turn.** It ranked the comparison before applying the new 100 Nm minimum. Frequency 50 Hz lived in lookup focus, while the metric route read only filters and chose the minimum time at 60 Hz. The final guard covered structured shown recommendations, not this card/prose route. | Applies the bound before ranking, carries the comparison's service/frequency, recommends `762A00-11300000/A` at **21 s / 50 Hz**, and excludes the 80 Nm model. |
| L4-04, turn 2 | `0f49f513-d7d4-4144-8642-0822dde7b265` | Flash recorded `ask_clarification(field=requirements)`. Repeated-question handling called `unresolved()`, which rendered the cached ranked list as “best matches” without applying the new upper bound or checking eligibility. Its stored filter still said `>=300 Nm`. Separately, “Make that” was absent from the correction vocabulary. | An explicit changed quantity triggers the existing search/merge path even after a clarification decision. “Make that at most 300 Nm” replaces the old bound, keeps supply/service/enclosure, and excludes the 500 Nm item. |

Neither case was a conversion between Nm and in-lb. The published product values
were correct; the selection and state handling were wrong. The two initial
comparison decisions in L1-01 and the L4-04 clarification decision are replayed
unchanged in the oracle tests, with three paraphrases for each failing request.

## Final enforcement

Every `_turn` response goes through `finish()`. Its last operation now invokes
[response_integrity.enforce](../../backend/conversation/response_integrity.py),
after all renderer changes. It collects cards, comparison models, recommendation
items, and codes in answer/lead text, loads their SQL rows, and checks
`integrity.satisfies` against active requirements. The independent quantity ledger
and any missing written quantity are included without replaying categorical state
transitions or changing equivalent bound representations.

An invalid positive selection clears its products, recommendation, comparison,
suggestions and cached selection lists together, including the positive prose.
This includes a valid card paired with an invalid prose recommendation; a valid
structured item cannot mask an invalid selection in another output channel.
Informational specifications and `total=0` relaxed alternatives may remain only
with explicit failed-requirement labels; alternative item reasons and comparison
summaries also carry those labels. Already-correct named exclusions are preserved.
“Shown” selections are checked against the prior visible set as well.
An informational lookup carrying a new numeric minimum also labels a failing
product and retains that minimum for a later pick; the guard does not rely on the
lookup renderer to interpret the bound.
A factual assertion such as “confirm this model has 999 Nm” is checked against
the catalogue, not stored or echoed as a newly accepted minimum.

Relative requests such as “give me a stronger one than the second one” now use
the relative-search route and resolve the ordinal reference. If the service is
missing, the response asks for it and retains the unresolved requirement instead
of recommending the reference itself on a later metric turn.

## Full original-v15 scan

[scan.json](../agent_acceptance/p1_f/scan.json) records all **60 conversations,
131 responses, 169 product cards and 241 unique code references per turn**,
including recommendation items and comparison/prose references. Requirements in
[reviewed_scopes.json](../agent_acceptance/p1_f/reviewed_scopes.json) were reviewed
from the requests rather than trusting the recorded model's retained state.

The scan flagged eight turns:

* **Four unlabelled technical violations:** L1-01/3 and L4-04/2 above; additionally
  **L7-01/2 and /3** selected `762A00-11320000/A` after asking for something stronger
  than that very model. The displayed On/Off value was 150 Nm, so it cannot satisfy
  `>150 Nm`. The same equality problem holds under Modulating service; service
  ambiguity is a reason to clarify, not to select the reference. The following
  turn inherited that unfulfilled relative request. Both are covered by the new
  relative-request regression, including clarification and subsequent resolution.
* **Four explicit non-matches/informational cases, not additional recommendations:**
  L1-03/3 explicitly reports source N/A; L1-09/1 marks torque/supply relaxations;
  L7-04/3 says none qualify and names enclosure exclusions; L7-11/1 explicitly says
  DC has no mains frequency. These are retained separately from violations.

Two further **shown-set violations**, L7-03/3 and L7-05/4, selected technically
eligible products outside the prior visible choices. Recorded-state regressions
cover both; metric selection now uses the visible set when explicitly requested,
and the final guard independently rejects an out-of-set selection.

No other product eligibility violation was found in this reviewed sample. This
does **not** mean all v15 answers are correct: aggregate scope (L7-04/2), reversed
ranking intent, omitted requests and other interpretation defects remain separate
from this repair. v15 is diagnostic evidence, not a fresh held-out acceptance run.

## Verification

[test_p1_f_integrity.py](../../tests/test_p1_f_integrity.py) has nine test methods,
including the eight
original/paraphrased primary replays, relative-request lifecycle and shown-set
replays, a fresh-bound lookup followed by a pick, factual-claim rejection,
a valid-card/invalid-prose regression,
**1,280 seeded combinations** of bounds/output shapes/route labels, and
**108 calls through real entry routes** (search, clarification, metric verdict,
pick, ranked list, reference lookup, comparison, show-all and rank action).
The generated cases cover strict/inclusive lower and upper torque limits,
published Nm and in-lb columns, power and operating-time limits.

The older `test_upper_bound_correction_keeps_other_filters` expectation was corrected:
“make that at most 400 Nm” now means `<=400`, not the accidental intersection
`>=400 AND <=400`. Existing explicit-addition/range tests remain enabled.

Both requested commands exited **0** after the factual-claim and mixed-output fixes:

| Requested command | Final result |
|---|---|
| `SERIES76_TEST_DB=1 .venv-model-eval/Scripts/python.exe -m unittest discover -s tests` | exit 0; 669 tests, 667 passed, 2 skipped |
| `.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t14_gates.py` | exit 0; component results below |

[gates.json](../agent_acceptance/p1_f/gates.json) records `same_source: true`.
The outer runner and T14 manifests match across **194 source/config/fixture files**;
all current file hashes were checked against them after completion.
The [independent unittest log](../agent_acceptance/p1_f/unittest.log) spans an
overnight wall-clock jump and reports 24,926.827 seconds; this is test execution
evidence, not a latency benchmark.

| T14 component | Final result |
|---|---|
| unittest | 669 tests: 667 passed, 2 skipped; exit 0 (376.261 s) |
| v7 | 453/453; exit 0 |
| T10 | 48/48; exit 0 |
| T12 | 47/47; exit 0 |
| T14 | 42/42; exit 0 |
| Schema | 5,520 bytes, 108 enum values; exit 0 |
| Public-text invocation | exit 0; import-only limitation below |
| Ranking | 40 queries, 2,720 judgments, returned compliance 1.0, NDCG@3 0.965378; exit 0 |
| Historical v13 replay (diagnostic, excluded by existing runner) | 28/45 passed, 17 failed; exit 1 |

The replay's failures remain open; the requested T14 command returns zero because
its existing policy excludes that diagnostic replay from the gate. This repair
does not claim that the broader v13/v15 behavioral backlog is resolved.
Component logs and exact exits are preserved in [p1_f/t14](../agent_acceptance/p1_f/t14/),
without replacing the historical T14 evidence directory.

The preceding development run exposed an unwanted echo of a rejected number in
v7's `injection_number`; that failure was fixed before final acceptance.
The runner
[p1_f_final_gates.py](../agent_acceptance/p1_f_final_gates.py) obtains only DB settings
in memory from the running backend, disables dotenv/provider configuration, runs
the requested commands sequentially, and compares the source digests before/after.
Local HTTP provider fixtures in the existing suite remain synthetic loopback tests.
The existing runner's direct `check_public_text.py` invocation is an import-only
exit check: that file defines functions but has no command-line entry point.
Its exit status is reported without treating it as a standalone public-text audit.

Reproduce the source recovery and audit with the existing no-dotenv wrapper:

```text
.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py reports/agent_acceptance/p1_f_recover.py
.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py reports/agent_acceptance/p1_f_scan.py --source C:/Users/nrir/AppData/Roaming/orca/chat-scratch/97d6b63f2a41ae2054d3f6922c392659
.venv-model-eval/Scripts/python.exe reports/agent_acceptance/p1_f_final_gates.py
```

No new real-model or Android/device validation is claimed. No production container
was rebuilt; deployment of the pushed source is a separate action.
