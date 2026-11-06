# SV2 implementation and offline evidence

**Experimental branch only: `exp/state-v2`. Not ready for production adoption.**
The complete-state implementation passes the 137 T10/T12/T14 oracle scenarios,
but v7 is **353/453 (77.92%)**, below the requested 95% target. The experiment
runner exits **1**, preserving that failure. No paid or live inference was run.
The coordinator requested delivery of this diagnostic branch and deferred repairs
until after the separately authorized v15 A/B (`msg_32b107de8d5b`).

## Delivered contract

The [design](../../docs/design/state-v2.md) was committed before implementation.
`AGENT_STATE_MODE` defaults to `v1`; only exact `v2` selects the separate executor.
The existing v1 prompt, tool declarations, interpreter and finalizer remain
unchanged. The base is `release/submission` at `503d25e`; implementation commits
are `0e6d679` and `e93ec78`, following design commit `5136f80`.

One `set_conversation_state` decision supplies the full next filters, ordered
priorities, references, unsupported requests, pending question and site hazard.
Its intent is search, lookup, compare, explain, clarify or recommend_from_shown.
The full validated state is persisted in the session context. Omission removes a
field; the server does not interpret a natural-language delta. Eleven compact
prompt examples cover additions, replacement, removal, negation, priorities,
shown references, compound scope and separate hazard clearance.

Strict validators reject illegal operators/fields/enums, unquoted quantities or
units, wrong dimensions, invented/nonfinite numbers, invalid ranges, conflicting
constraints, unsupported glossary/view values and forged shown-product receipts.
Evidence comes from user messages or server-persisted, previously validated user
quotes; assistant prose cannot ground a constraint. P1-C SQL resolution handles
exact codes, presentation variants, unique prefixes and confirmation candidates.
Symbolic same/stronger/faster reference constraints derive numbers from SQL and
record reference provenance, rather than allowing model-authored SQL values.

Validation is atomic: one problem-specific clarification, previous state retained,
no partial product set and no silently discarded field. Every displayed product
is checked with `integrity.satisfies`; numbers and catalogue facts are rendered
from SQL/templates. Hazard validation can veto, but cannot rewrite the model's
enclosure or select another product. Explicit enclosure choice or named/shown
selection confirms enclosure when there is no hazard evidence, as clarified by
the coordinator; positive hazard still blocks a Weatherproof recommendation.

## Rules bypassed in v2

Dispatch before `_turn` bypasses `single_field_code`, `fast_path_codes`,
`interactions.free_text_answer` and `_turn` regex intent branches. The new executor
does not call `Turn.search`, `Turn.lookup`, `Turn.ask`, `Turn.explain`,
`Turn.recommend_shown` or `finish`. It bypasses:

- `policy.colloquial_requirements`, `explicit_context_values`, `current_requirement`,
  `removed_fields`, `replaced_fields`, `merge_filters`, `merge_bounds`,
  `grounding_errors`, `sort_grounded`, `normalized_term_keys`, `term_is_relevant`.
- `requirement_coverage.apply`, `.unsupported`, `.missing`;
  `answer_planner.plan`; `catalogue_answers` language routing; semantic retrieval
  field insertion.

These paths infer intent or merge/rewrite/drop fields. Retained validators are
P1-C SQL resolution, strict `SearchFilters`, the hazard veto, `integrity.satisfies`,
ranking mathematics and SQL rendering. Number/unit matching remains a provenance
validator: it rejects unsupported evidence instead of rewriting requirements.

## Offline results

All execution used the separate `serie76-sv2` Compose project and
`serie76-sv2_sv2_catalog` volume on localhost:55433: 68 catalogue rows and 16
glossary terms. The wrapper blocks `.env` reads and external socket connections,
clears provider credentials and disables embeddings/tracing. The main volume was
not accessed or changed. Existing validated OCR exports were imported; no numeric
authority was replaced by reference data.

| Mode / check | Result | Exit |
|---|---|---:|
| v1 full DB unittest discovery | 707 run, 705 passed, 2 optional OCR skips | 0 |
| v1 frozen v7 | 453/453 | 0 |
| v1 T10 / T12 / T14 | 48/48; 47/47; 42/42 | 0 |
| v1 `run_t14_gates.py` required checks | Passed | 0 |
| v2 final validator and fixture tests | 48/48 | 0 |
| v2 original T10/T12/T14 expectations | 137/137, 215 turns | 0 |
| v2 `check_tool_schemas` | 1,509 bytes; 6 enum values | 0 |
| v2 public-text response audit | 215 core + 760 v7 responses; zero issues | 0 |
| v2 ranking | NDCG@3 0.965377944; compliance 1.0000 | 0 |
| v2 frozen v7 | 353/453; 100 failures; target missed | **1** |
| Complete experiment runner | Required core gates passed; v7 target failed | **1** |

The v1 full discovery started before the final added SQL-candidate confirmation
test; the subsequent 48-test v2 suite includes that test on the final code.
The unchanged historical Flash-decision replay remains **28/45**, exit 1. The
existing T14 runner excludes that diagnostic from its required-gate exit; it is
not represented here as a passing live-model run.

The direct `check_public_text.py` command exits zero but only imports definitions.
To avoid mistaking that for an audit, `response_text_issues` was additionally run
over every saved core/v7 response; the [actual audit](../agent_acceptance/sv2_final/public_text_audit.json)
has zero findings. Acceptance also checks public text during replay.

The v1 wire schema is 5,520 bytes / 108 enum values; v2 is 1,509 bytes / 6 values
(72.7% fewer bytes), with 6 arrays, depth 7 and no forbidden nodes or numeric
ranges. The many legal field values are validated strings described in the prompt,
not additional wire enums. This trades provider schema size for validator/prompt
responsibility; it is not evidence of better model interpretation.

The core fixtures preserve the original queries and expectations. The offline
converter uses successful v1 traces to author full-state decisions; it is never
called by the v2 runtime. Ranking exercises v2 validation, SQL filtering and
ranking on 40 synthetic queries / 2,720 judgments, with literal synthetic evidence
for oracle constraints. Neither test measures natural-language model accuracy.

## v7 differences and adoption limits

[All 100 differences](SV2-v7-differences.md) are classified by conversation:

| Class | Count | Meaning |
|---|---:|---|
| (i) Intentional contract differences | 7 | One decision instead of a fast path, or stricter quantity/unit grounding |
| (ii) Presentation/question format | 36 | Fact, empty result or safe refusal present; legacy wording/structure differs |
| (iii) Genuine replay regressions | 57 | Missing/wrong answers, lost scope/priority, broken controls or unresolved qualification |

Mixed cases count as (iii). Converter failures are failures of the delivered
offline path, even when the runtime correctly rejects them. The 57 include
lost DC/frequency conflicts, pagination, equivalent-code follow-ups, objective
changes, arithmetic answers, shown-set selection and a wrong-scope aggregate.
The classification does not waive any of the 100 failed expectations. In
particular, a frozen assertion about repeated code text can hide a lost ranking
priority, so the review used actual responses and state traces as well.

Remaining architectural risks: a complete-state model can omit an old requirement;
code cannot distinguish that omission from an intentional removal. Quoted
categorical evidence can still be semantically misread. Unit conversions and
grouping notation are conservative; some valid requests require clarification.
Shown-set multi-priority selection is rejected rather than silently reduced to one
priority. History and persisted evidence can grow; no 100x-load or latency claim
was tested. Existing v1 sessions have no complete-state migration guarantee.
The hazard detector remains vocabulary-dependent. Live provider acceptance of
the new schema and prompt is untested. These risks preclude declaring production
readiness from the core oracle score.

## Reproduction and handoff

Start only the isolated database with an empty Compose environment file:

```powershell
$sv2EmptyEnv = New-TemporaryFile
docker compose --env-file $sv2EmptyEnv.FullName -p serie76-sv2 -f docker/compose.sv2.yml up -d --wait
python scripts/sv2_offline.py -m backend.catalog.cli migrate
python scripts/sv2_offline.py -m backend.catalog.cli load data/extracted/series76
python scripts/sv2_offline.py -m backend.catalog.cli load-context
python scripts/sv2_offline.py scripts/run_sv2_gates.py
```

Use an environment with the repository dependencies installed. The runner selects
v1/v2 explicitly and returns 1 for the documented v7 target failure. Source hashes,
logs and results are under [SV2 final evidence](../agent_acceptance/sv2_final/summary.json);
the [v1 identity audit](../agent_acceptance/sv2_final/v1_identity.json) compares
the unchanged v1 source with the release base. The
[v7 classification evidence](../agent_acceptance/sv2_v7/classification.json)
contains every failed conversation's observed responses and trace.

Ready for a **diagnostic** paid v15 A/B: opt-in runtime, complete-state prompt/tool,
schema preflight, isolated catalogue, frozen offline fixtures and failure ledger.
No provider calls, cost estimate, v15 outcome or adoption decision are included.
The coordinator owns the separately authorized paid comparison and the follow-up
repair/adoption decision; v1 remains the default.
