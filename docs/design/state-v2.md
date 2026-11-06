# State v2 experiment

Status: design before implementation, 2026-11-05. Isolated branch `exp/state-v2`,
base `release/submission` at `503d25e`. Default `AGENT_STATE_MODE=v1` retains the
existing path. No inference is authorized by this experiment.

## Contract and ownership

One model call chooses `set_conversation_state`: an intent (`search`, `lookup`,
`compare`, `explain`, `clarify`, `recommend_from_shown`) and a **complete next
state**, not a delta. Omission removes an old requirement; retaining a requirement
means copying it. The server never merges natural-language deltas or repairs a
model interpretation. State is saved in the existing per-session context JSON;
no schema migration is needed. Session locking/transaction boundaries stay intact.

State contains `filters` (field, operator eq/gte/lte/gt/lt/range, value, optional
upper value, unit, verbatim user evidence), ordered `priority` (metric, direction,
optional frequency and evidence), `references` (selected/shown SQL part numbers),
`unsupported_requests`, `pending_question`, and `site_context` (hazard
yes/no/unknown and evidence). A bounded presentation request specifies focus,
glossary keys, catalogue topic and pagination. References to the visible set are
validated against server-owned display receipts; model output cannot invent a
previously shown product. SQL output receipts are separate from model-owned state.

Numbers are strings on the wire to avoid provider union schemas; the validator
parses finite decimals without rounding. Unit aliases normalize dimensions only;
they never infer fields, operators or requirements. Every constraint number and
unit needs a matching quote in the current or an earlier **user** message.
Categorical interpretations and priorities also carry a user quote; code checks
legal values and provenance, while semantic interpretation belongs to the model.
Unsupported labels select fixed catalogue-limit templates, never generated prose.
Schema uses validated strings/arrays rather than large enums (ceiling 108 enum
values). Exact serialized bytes/enums will be recorded by the offline schema gate.

## Validation, safety and rendering

Validate the entire proposal before replacing state. Reject illegal fields,
operators, units, nonfinite numbers, unsupported precision, contradictions,
fabricated references and ungrounded quantities. Resolve explicit user identifiers
with P1-C: exact/presentation variants and unique prefixes resolve visibly against
SQL; ambiguous or one-edit candidates require confirmation; unknown codes fail.
No model-only prefix completion. Every displayed product must pass
`integrity.satisfies`; catalogue numbers, aggregates, N/A, units and provenance
are rendered from SQL through fixed templates. A failed validation produces one
question identifying the problem, retains the previous valid state, and displays
no partial product selection. No dropping a rejected field and proceeding.

Coordinator clarification (`msg_a439b25ba56c`): an explicit Weatherproof choice
without hazard evidence is confirmation; keep its enclosure visible without an
extra warning. Positive/implied hazard evidence (including the existing safety
detector) forbids a Weatherproof-only recommendation pending confirmation. Unknown
means no hazard evidence and no enclosure choice: search both normally; ask once
before a single pick. Removing an enclosure restriction does not clear site hazard;
the model must represent explicit site clearance separately. Safety validators may
veto a decision, never substitute another enclosure or model.

Coordinator clarification (`msg_e49366e2e354`): selecting among explicitly named
or previously shown codes also confirms their visible enclosure, unless hazard
evidence exists. Symbolic reference constraints (same/stronger/faster/smaller plus
a validated reference code) may derive execution values from SQL; trace these as
`from reference <code>`. The model still cannot author unquoted numeric values.

## Exactly what v2 bypasses

Dispatch before `_turn` bypasses all v1 deterministic intent fast paths, including
`single_field_code`, `fast_path_codes`, `interactions.free_text_answer`, and the
regex branches in `_turn`. The new executor does not call `Turn.search`,
`Turn.lookup`, `Turn.ask`, `Turn.explain`, `Turn.recommend_shown` or `finish`:
these mix rendering with language-dependent state edits. Specifically excluded:
`policy.colloquial_requirements`, `explicit_context_values`, `current_requirement`,
`removed_fields`, `replaced_fields`, `merge_filters`, `merge_bounds`,
`grounding_errors`, `sort_grounded`, `normalized_term_keys`, `term_is_relevant`;
`requirement_coverage.apply/unsupported/missing`; `answer_planner.plan` and
`catalogue_answers` language routing; semantic retrieval field insertion.
These functions rewrite/drop fields or derive intent from lexicons. Retained:
P1-C SQL resolution, strict `SearchFilters` validation, hazard veto,
`integrity.satisfies`, ranking math and SQL-only rendering. v1 functions are not
modified internally. Structured UI actions require an explicit validated adapter,
not a hidden v1 fallback.

## Evaluation and risks

Freeze original oracle expectations. Convert T10/T12/T14 scripted decisions to
complete v2 states; report v7 separately with every deviation. Run v1 full DB
unittest and T14 gates against an isolated database; then adversarial v2 validators,
schema/public-text and ranking gates. Store evidence under SV2 paths so historical
reports remain unchanged. No live-provider score can be inferred from ideal inputs.

Risks: full-state token/latency growth, stale requirement omission by the model,
semantically incorrect but quoted categorical interpretation, novel units rejected
conservatively, safety vocabulary limits, and migration from existing v1 sessions.
Bounded history alone cannot support indefinitely old evidence: validation must
use persisted user-origin evidence or reject and ask. A paid A/B needs separate
authorization and a new held-out set, identical catalogue and frozen scoring.
