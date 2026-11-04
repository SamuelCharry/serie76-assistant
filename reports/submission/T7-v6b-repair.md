# T7 v6b follow-up repair

Implemented in `50bb349`; verified offline with scripted decisions and real PostgreSQL. No paid calls or recorded-result edits. The coordinator reported v6b as 10 passed, 3 failed and 2 provider-only, with combined v6/v6b coverage 98/103; this repair does not claim a new live score.

## Causes and changes

- `exact_noncanonical`: the query extractor already returned the canonical full code, but `grounded_lookup_codes` compared it with the model's undashed prefix using literal `startswith`, so `761A0011300000` failed to match `761A00-11300000/A`. Matching now ignores case and presentation separators on both sides. A complete query code must still supply its explicit A suffix; neither SQL nor a default supplies it. Canonicalization also accepts a missing slash before that explicit suffix. The recovery override and the user-facing normalization note are retained.
- `EC35`: the model selected `ask_clarification(unsupported)`, which previously returned only a purchase limitation and generic capabilities. For commerce requests naming a complete code, that path now invokes normal deterministic lookup, records `purchase_catalogue_lookup`, and prepends the purchase/delivery limitation. One model decision; no suggestions. Purchase without a complete code and unrelated unsupported requests do not trigger lookup.
- `t6_manual_03`: accepted interpretation difference per coordinator instruction, unchanged. The recorded model treated the second Spanish request as a refinement and retained the previous 70 Nm threshold; the scripted expectation starts a fresh search. The historical failed verdict and existing expectation remain intact.

Tests were written first: both live failures reproduced, as did separator variants. Four new methods cover recovery, punctuation/case variants and explicit prefix preservation, useful purchase lookup, and negative unsupported/purchase cases. All 12 focused regression tests now pass. No existing test or acceptance expectations changed.

## Exact scripted answers

These are copied from [captured JSON](T7-v6b-repair-evidence.json), with the recorded v6b queries and model arguments; only the model decision is scripted, and figures come from the normal SQL lookup. The JSON retains raw arguments, original model calls, canonical parameters, overrides, products, suggestions and decision counts.

### exact_noncanonical

```text
Interpreted '761a0011300000/a' as 761A00-11300000/A.
761A00-11300000/A
  • On/Off torque: 700 in-lb / 80 Nm
  • Modulating torque: 580 in-lb / 65 Nm
  • Duty S4 On/Off: 40%
  • Duty S4 Modulating: 40%
  • On/Off cycles per hour: 36
  • Modulating starts per hour: 960
  • Operating time at 50 Hz: 20 s
  • Operating time at 60 Hz: 17 s
  • FLA at 50 Hz: 1.1 A
  • FLA at 60 Hz: 1.2 A
  • LRA at 50 Hz: 1.3 A
  • LRA at 60 Hz: 1.4 A
  • Motor power: 15 W
  Source: Series 76 electrical catalogue, page 1.
```

### EC35

```text
I cannot place orders or confirm delivery. I can provide published catalogue specifications.
761A00-11300000/A
  • On/Off torque: 700 in-lb / 80 Nm
  • Modulating torque: 580 in-lb / 65 Nm
  • Duty S4 On/Off: 40%
  • Duty S4 Modulating: 40%
  • On/Off cycles per hour: 36
  • Modulating starts per hour: 960
  • Operating time at 50 Hz: 20 s
  • Operating time at 60 Hz: 17 s
  • FLA at 50 Hz: 1.1 A
  • FLA at 60 Hz: 1.2 A
  • LRA at 50 Hz: 1.3 A
  • LRA at 60 Hz: 1.4 A
  • Motor power: 15 W
  Source: Series 76 electrical catalogue, page 1.
```

## Required checks

All final commands exited 0:

```powershell
$env:SERIES76_TEST_DB='1'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
# Ran 216 tests in 30.173s; OK (skipped=2)

.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json
# {"selfcheck":"ok","scenarios":103,"failing":[]}

.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_acceptance_v6.py -v
# Ran 6 tests; OK

.venv-model-eval/Scripts/python.exe scripts/check_tool_schemas.py
# {"arrays":6,"bytes":4131,"depth":7,"enum_values":83,"forbidden_nodes":0,"get_actuator_object_arrays":0,"numeric_ranges":0,"required":3}

docker compose -f docker-compose.yml -f "$env:TEMP/t7-keyless-compose.yml" up -d --build backend
# exit 0; backend rebuilt/recreated, database remained running
Invoke-WebRequest -UseBasicParsing http://localhost:8000/ready
# HTTP 200; status ready; catalog rows 68; context_terms 16
```

The two skips remain optional OCR/geometry modules. The rebuild ran with model/tracing credential variables removed and the existing override explicitly clearing model keys/names and tracing. Standard approved test helpers load connection settings internally; no secrets or `.env`/`.cache` contents were inspected or printed, and no container credentials were extracted. No mobile, catalogue, OCR, migration, recorded v6/v6b results or volumes changed. No push.

Real-model confirmation of the two repairs remains for the coordinator. The successful scripted result does not establish that a new provider response will choose the same arguments.
