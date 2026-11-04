# T9: embeddings for interpretation

## Review repair (current behavior)

The independent review and the coordinator's v8 A/B findings supersede the original
fallback-only design. Retrieval is **additive**: deterministic service/hazard evidence,
canonical enclosure values and clause-level negations run with embeddings both ON and
OFF. Similar examples remain prompt data. Suggestions can only fill fields left unset
by deterministic parsing, grounded tool arguments and carried refinement filters.

- Enclosure normalization handles `explosion-proof`, `explosion proof`, `weather-proof`
  and `weather proof` before suggestions; a safe-area suggestion cannot replace a
  stated Explosionproof requirement.
- Suffix negations and no-preference clauses do not count as affirmative service.
  `on/off service does not matter` and `doesn't matter` remove service and retain the
  independent 110 V clause; `not modulating, just on/off` retains affirmative On/Off.
- `open and close`, `mod`, `que module`, `abrir y cerrar`, `regulating` and wood-dust
  hazard evidence remain available when the classifier abstains. Explicit negations
  such as `nothing flammable` / `no flammable atmosphere` prevent the hazard preview,
  including a follow-up rejecting an earlier Explosionproof preview. An uncertain
  chlorine/office request does not acquire an Explosionproof-only preview.
- Migration `008_example_bank_versions.sql` adds active status, dataset version and an
  immutable dataset manifest. Incremental reloads union all historical source IDs;
  conflicts deactivate a row. Explicit authoritative replacements deactivate missing
  or conflicting examples while retaining vectors and all historical provenance.
- Startup constructs the cached embedding client without inference. A lock prevents
  duplicate concurrent initialization. A single monotonic **1.5 s** retrieval budget
  covers cold initialization, budget reservation, embedding and both SQL searches.
  Late embedding results are discarded; four bounded worker slots prevent an unbounded
  backlog, and SQL stays on the caller's connection with the remaining statement timeout
  inside a rollback-only savepoint. Expired work cannot start a provider request after
  initialization or budget waiting, and cannot proceed to SQL. A request already sent
  before expiry may finish remotely, but its late result is ignored and is not retried.

Each of the five review findings was reproduced by a failing test before its repair.
The additive regression includes all **446 v7 scenarios / 745 turns**: full agent
filter preservation with classifier abstention (ON/OFF), plus normalizer property
checks with opposing semantic suggestions. These are offline checks, not a new live
chat A/B score. The coordinator's reported 61% ON / 63% OFF score is pre-repair evidence;
no improved live score is claimed.

The existing Google bank was reconciled as authoritative version
`v7-14e7fbf25214744f`, using the v7 file SHA256 prefix. **649 examples remain active,
100 anchors retained, 0 texts embedded, USD 0 additional inference cost** in this repair.
Initial T9 paid-call evidence below is historical and was not rerun.

Review completion snapshot: users **5**, conversations **623**, messages **2204**,
catalogue entries **68**; the historical pre-review counts below are not the current
conversation counts. The rebuilt backend has `EMBEDDINGS_ENABLED=true` and
`OPENROUTER_EMBEDDING_MODEL=gemini-embedding-2`; `/ready` returned **HTTP 200** after
startup initialization. No mobile files were modified and no push was performed.


## Approved specification and slices

The dispatched T9-B1 specification authorizes optional semantic examples and concept
suggestions, with SQL remaining the sole source of catalogue values. The unchanged
tool schema, explicit values, numeric bounds and negations take precedence. No
deterministic route may call embeddings; failures fall back to existing behavior.

1. Back up PostgreSQL, pin pgvector PG17, preserve all existing row counts, migrate.
2. Add a guarded 768-dimensional LangChain client and idempotent v7/anchor loader;
   test with a deterministic local embedder before the one authorized Google load.
3. Retrieve five examples and concept maxima before the single LLM decision;
   apply threshold/margin suggestions through the existing normalizer and expose debug.
4. Run Python tests, v7 selfcheck, text scanner and offline schema gate; rebuild
   the backend with Google embeddings enabled and verify `/ready`.

No chat inference, OpenRouter inference, mobile edits, pushes, secret output or volume
deletion are authorized. Tests use unittest and the approved `local_environment()`
connection mapping. Each slice is verified and committed separately.

## Initial T9 database checkpoint (historical)

Backup: ignored `backups/t9-before.dump`, SHA256
`e6924174edbf5d3f6c2c9c1494b1de4dbe5f8018d14903933d5007fe36d953f7`.
Before: users 5, conversations 540, messages 1924, entries 68.
All 15 existing table counts matched before migration; migration was applied twice.
The initial pg17 tag used glibc 2.36, whereas the volume was created with 2.41.
Before the embedding load, switched to the coordinator-approved `pg17-trixie` digest in
Compose and CI. Container `ldd` confirms 2.41; database, postgres and template1
collation versions match their actual versions. All original data counts still match.
At original T9 completion, data counts still matched: users **5**, conversations **540**, messages **1924**,
entries **68**; all 14 preexisting data tables were checked. The migration registry
has one additional row. No volume was deleted and no existing password was changed.

## Implemented design

`007_embeddings.sql` enables vector and adds `series76.example_bank` (text,
interpretation JSON, source IDs, model, dimension, vector) and
`series76.concept_anchor` (concept, phrase, model, vector). Both use 768-dimensional
vectors and unique constraints; exact cosine search is appropriate for 749 rows.
The final image is
`pgvector/pgvector:pg17-trixie@sha256:01215e09bd4bd582d20230e025b6c971deeeffee49ceef1aae167e839cb62a7e`,
shared by Compose and CI.

`backend/conversation/embeddings.py` uses LangChain `OpenAIEmbeddings`, the configured
endpoint/key, `dimensions=768`, a **1.5 s total retrieval deadline** and **zero retries**; provider and SQL timeouts use the remaining budget.
Each actual provider request reserves through `reserve_agent_call`; failures count.
This existing rolling-hour guard is per process and resets on restart, not a billing
account cap. Loader batches use a 30 s timeout, outside the turn path, with zero retries.
No provider call occurs at import or on deterministic conversation routes.

After deterministic routes, the agent embeds once, executes two parameterized SQL
queries, and supplies at most five examples with similarity >= **0.70** as JSON prompt
data. Numeric values still pass the original grounding, quantity, bound, conflict and
SQL rendering checks. Example numbers cannot become requirements merely because
they appeared in the prompt. Concept maxima feed the normalizer as suggestions;
explicit values and code-side negations win. Hazard requests enclosure confirmation
and previews only Explosionproof candidates. Accepted safe-area and service concepts
can supply those categorical requirements. `out_of_scope_property` is diagnostic;
the existing catalogue-scope rules still own unsupported-property responses.

The deterministic normalizer always runs. Missing configuration, disabled flag, empty
anchor bank, provider failure or SQL failure simply omits semantic additions. Optional SQL runs inside a savepoint so a
failed retrieval does not poison the surrounding conversation transaction.
Every result's debug includes `retrieval.examples` (IDs/similarities),
`retrieval.concepts` and `retrieval.embedding_ms`; deterministic routes report empty
retrieval with zero embedding time. The tool schema is unchanged.

## Bank, provenance and leakage controls

The loader selected **649** unique v7 user queries with unambiguous scripted decisions
or explicit expected tool/argument pairs; ambiguous alternatives, conflicting
duplicate labels, unlabeled turns and UI actions are excluded. It loaded **100**
anchors, exactly 20 English/Spanish phrases per concept, from
[concept_anchors.json](../../config/concept_anchors.json).

`source` stores a JSON array of every source scenario ID for a duplicate query.
Set `EMBEDDING_EXCLUDE_SOURCES=id1,id2` to exclude any row associated with a held-out
ID. Exclusion happens before distance ranking and LIMIT, so excluded rows cannot
occupy the five slots. The bank includes historical v7 held-out cases by task design;
evaluation must supply exclusions or a fresh cohort. The smoke evidence here is
calibration, **not** held-out acceptance.

The batched loader checks existing keys before embedding, serializes concurrent
loaders with an advisory lock, and inserts transactionally. Incremental mode unions
source IDs and never reactivates a previously retired row merely because its old
label reappears. Conflicting incremental labels deactivate the row.

To intentionally replace the authoritative example set, pass both
`--replace-dataset --dataset-version <immutable-version-id>`. The version fingerprints
the complete labeled payload and source associations; reusing it with different data
is rejected before inference. Rows absent or ambiguous in that version become inactive,
not deleted, and retrieval excludes them. A later explicit authoritative version can
reactivate an existing vector without re-embedding. Historical source IDs are never
removed, even when replacing the active interpretation. Retain a new version ID for
an intentional change, and do not present a subset as the full authoritative dataset. A second dry run found
**0 texts pending / 0 estimated cost**; the DB test also reruns loading with an
embedder that fails if called and verifies no call occurs. A failed load rolls back;
already incurred provider charges are not refunded, so inspect a failed load before
retrying. No load retry was needed in this run.

## Thresholds and observed limits

| Concept | Minimum similarity | Margin over opposite |
| --- | ---: | ---: |
| hazard | 0.63 | 0.015 over safe_area |
| safe_area | 0.75 | 0.08 over hazard |
| on_off | 0.72 | 0.08 over modulating |
| modulating | 0.72 | 0.08 over on_off |
| out_of_scope_property | 0.78 | No paired opposite |

Initial conservative thresholds used hazard 0.70 and a uniform 0.08 margin. The
[18-query smoke](T9-embedding-smoke.json) recognized all four motivating short
phrases, but [compound queries](T9-embedding-turn-initial.json) diluted similarity
when voltage/torque were included. The [16 controls](T9-embedding-controls.json)
showed that lowering service margins would classify generic actuator requests as
service requirements. Those stricter filter thresholds were retained.

Only hazard was calibrated lower: its consequence is a confirmation question,
not silently applying an enclosure. Compound ethanol/paint queries score 0.642/0.664,
with margins 0.023/0.017; generic-process and gas-free controls have margins only
0.005/0.012. Those scores are frozen in regression tests. This small calibration
set does not establish a production false-positive rate.

[Final live-embedding/scripted-chat turns](T9-embedding-turn-smoke.json) confirm both
compound hazards, modulating wording and safe-area application. **Remaining limit:**
`que abra y cierre, 110 V, at least 70 Nm` retrieves the matching example at 0.929,
but the service classifier abstains (0.672 similarity / 0.021 margin). The normalizer
retains voltage and torque and asks service when the scripted chat omits it. Whether
a live chat model uses the retrieved example correctly is pending; no chat calls
were authorized. A Spanish safe-area phrase also abstains at the margin gate.

Provider timeout is not a whole-feature wall-clock deadline: cold Python/client
initialization made first retrievals take roughly 3.2–4.0 s, while observed warm
retrieval embedding times were roughly 0.35–0.74 s. This overhead is disclosed rather
than reported as a 1.5 s end-to-end guarantee.

## Simplification and compatibility

Removed **17 physical phrase-list lines** from the main agent/policy path: 15 lines
of service/enclosure lexicons, colloquial patterns and the broad hazard regex, plus
two repeated weather-location expressions in the agent. The compatibility expressions
were isolated in `context_fallback.py`; the review repair now runs that deterministic
evidence on every turn, including when retrieval is enabled. The module name is retained
for compatibility, but it is no longer gated by embedding availability.
Explicit labels and negation checks remain in policy. New paraphrases belong in
anchors rather than additional scenario regexes.

The initial T9 change was not a net line-count reduction (agent.py **2166 -> 2185**,
policy.py **500 -> 537**). The review adds correctness and deadline guards rather than
claiming a reduction in code size. No existing test was changed or disabled. The additive property tests now explicitly compare both modes as described above.

## Verification and runtime

| Gate | Result |
| --- | --- |
| Full Python suite, local PostgreSQL | **469 tests, OK; 2 existing optional skips** |
| New embedding/retrieval/normalizer tests | **40 embedding/review tests, all passed**, deterministic hashed fake, scripted chat, event-controlled deadlines and real local SQL |
| v7 scripted selfcheck | **446 scenarios, 0 failures**, [review evidence](T9-review-scenarios.json) |
| Public text scanner tests | **3 passed**; scanner also runs across scripted responses |
| Offline tool schema | bytes=5487, enum_values=107, arrays=6, depth=7, forbidden_nodes=0, numeric_ranges=0; unchanged |
| Backup, migration, collation, existing counts | Verified locally, as recorded above |
| Rebuilt Google backend | `EMBEDDINGS_ENABLED=true`, model `gemini-embedding-2`; `/ready` **HTTP 200** |
| Runtime retrieval in rebuilt container | Initial T9 live smoke retained; review rebuild uses startup-only initialization and no inference |

Commands used (PowerShell, from the repository):

```powershell
$env:SERIES76_TEST_DB='1'; $env:EMBEDDINGS_ENABLED='false'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --evidence reports/submission/T9-review-scenarios.json
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_user_text.py
.venv-model-eval/Scripts/python.exe scripts/check_tool_schemas.py
```

CI uses the same pinned pgvector image, the offline fake tests, v7 selfcheck and
offline schema gate. CI was updated, but a remote CI run was not triggered (no push).
The coordinator's authorized `start_google.py` wrapper was updated to set the model,
flag and separate Google embedding endpoint/key in the subprocess environment. Its
`--off` mode disables embeddings and clears the separate embedding key. The wrapper
is outside the repository; no secret value was read into tool output or committed.

## Cost and provider switching

One Google load: **749 texts, 24 requests, estimated USD 0.004911** using a conservative
24,554 UTF-8-byte token estimate at the published
[$0.20 per million text tokens](https://ai.google.dev/gemini-api/docs/pricing#gemini-embedding-2).
This is an estimate, not a provider billing receipt; LangChain did not expose billed
token usage here. An additional **47 embedding-only smoke requests** were made
(18 short queries + 16 controls + 6 initial turns + 6 final turns + 1 container check),
within the authorized 50. No Google chat or OpenRouter inference was run.

For Google, use `OPENROUTER_EMBEDDING_MODEL=gemini-embedding-2` and the
[OpenAI-compatible endpoint](https://ai.google.dev/gemini-api/docs/openai)
`https://generativelanguage.googleapis.com/v1beta/openai/`. A separate
`EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` overrides the chat endpoint/key; otherwise
the `OPENROUTER_*` values are reused. `EMBEDDING_DIM` must remain 768.

For a future authorized OpenRouter run, set:

```text
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=<private provided key>
OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2
EMBEDDINGS_ENABLED=true
EMBEDDING_DIM=768
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
```

Load with `python scripts/load_example_bank.py`, then recreate the backend with
`docker compose up -d backend`. Rows are namespaced by model, so the OpenRouter model
name requires a separately authorized load. Do not relabel old vectors as a different
model. OpenRouter client configuration was tested offline; live compatibility and
chat quality remain pending. `.env.example` contains placeholders only.

## Commits

- `7980375`: additive storage and initial image pin, after backup.
- `6207125`: corrected image base to trixie before embedding data was loaded.
- `07b7c48`: guarded client, bank/anchor loader and offline tests.
- `47df34f`: exclude database backups from Docker build context.
- `27f421c`: retrieval, concept suggestions, negation precedence and CI gates.

Review commits:

- `1b46e75`: canonical enclosures, clause-scoped preferences, additive interpretation
  and complete v7 ON/OFF filter-preservation regressions.
- `c6291de`: versioned provenance, retired examples, startup warmup,
  concurrent initialization guard and one retrieval deadline.

Remote CI and a new live chat A/B evaluation remain pending; the local offline gates
and runtime configuration/readiness checks are complete. The repaired behavior has
not been assigned a new live acceptance score.
