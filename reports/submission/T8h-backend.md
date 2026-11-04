# T8h backend: final held-out repair

## Result and boundary

The supplied live Gemini round scored **24/43 strict** before these changes. This repair was verified with offline scripted decisions and local PostgreSQL; no paid inference was run, so a new live score is pending.

## Changes

| Slice | Commit | Evidence |
| --- | --- | --- |
| Quantity coverage, enclosure transparency, filter negation, catalogue and contextual answers | `12f2cf3` | New failing tests for numeric ranges, typos, enclosure disclosure, negation, superlatives, differences, follow-ups, and cancellation; then 429-test suite green. |
| Final held-out replay | `f60be3f` | Imported all 43 v7 conversations (72 turns) into the offline v7 acceptance set; 446/446 scenarios green. |

The quantity guard reads stated units and ranges before SQL. Clear limits are applied to the filter, including upper bounds and approximate torque minima; ambiguous measurements are disclosed instead of being silently omitted. Carried quantities are checked after filter merging, and a pick with an unrepresented quantity is withheld. Unit typos are matched only when unambiguous; otherwise the answer asks for a clear unit.

Recommendations and picks without an enclosure filter name each model's enclosure and add one site-classification line. Explicit negations clear carried fields. Catalogue superlatives and compared-model differences use SQL rows, while the shown set supports “compare all,” “why that,” a nearest alternative, and a corrected model/frequency follow-up. Three-phase counts distinguish seven models with published data from four listed without values.

## Verification

| Gate | Result |
| --- | --- |
| `SERIES76_TEST_DB=1 .venv-model-eval\\Scripts\\python.exe -m unittest discover -s tests` | 429 tests, OK; 2 skipped |
| v7 scripted `selfcheck` | 446 scenarios, 0 failing |
| Public-text scanner | 3 tests, OK |
| Offline tool schema | `enum_values=107` (cap 108), `bytes=5487`, `arrays=6`, `depth=7`, `forbidden_nodes=0`, `numeric_ranges=0` |
| Keyless backend rebuild | `docker compose -f docker-compose.yml -f <keyless override> up -d --build backend`; `keyless=True`; `/ready` returned HTTP 200 after startup |

The complete replay evidence is [T8h-scenarios.json](T8h-scenarios.json). The schema was unchanged from the prior round, preserving the one-decision contract and its enum budget. The first readiness request during container startup closed its connection; the retry returned 200.

## Remaining limit

The offline replay tests code behavior under scripted tool decisions. It does not establish that live Gemini will choose the correct tool for every unseen wording; the live strict score remains 24/43 until an authorized new round is run.
