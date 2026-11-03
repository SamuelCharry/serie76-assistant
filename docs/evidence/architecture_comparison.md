# Architecture comparison

The A-E experiment was inconclusive: 1/24 common scenarios, 103 calls and 19 provider failures. No measured superiority was established. Available scenario sets differ, so their pass counts cannot rank architectures.

A: single SQL agent; B: contextual agent with pgvector; C: two specialists; D: supervisor; E: proposer/reviewer.

| Variant | Attempted | Available | Available passed | Provider failures | Schema/protocol failures | Paired passed |
|---|---:|---:|---:|---:|---:|---:|
| A | 11 | 8 | 5 | 3 | 0 | 1/1 |
| B | 11 | 8 | 6 | 3 | 1 | 1/1 |
| C | 11 | 7 | 5 | 4 | 1 | 1/1 |
| D | 11 | 6 | 5 | 4 | 0 | 1/1 |
| E | 10 | 5 | 5 | 5 | 0 | 1/1 |

Controller charge: USD 0.48392565 / 0.50; known-usage tokens USD 0.16573125 and unknown-usage reservations USD 0.31819440. These are not an invoice or independent per-variant deployment costs. Latencies included controller pacing and embeddings were shared.

A+ was subsequently selected as an engineering decision: the 348-word summary has 16 definitions, so a literal glossary fits the context; one decision per turn plus deterministic policy, SQL and rendering limits calls and numeric authority. This is not an experimental ranking. See [ADR 0001](../adr/0001-arquitectura-agente.md).

Reproduce the historical analysis only after restoring the archived experiment in a separate checkout: `python scripts/analyze_architecture_eval.py`. Re-running inference requires explicit approval. Render the retained schema without DB access: `python scripts/render_architecture.py --offline`.

[Original archive](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/architecture_eval). [Archived experiment source](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/architecture_eval).

Use the activated generic backend environment from [test setup](../wiki/en/testing.md#run-locally); it installs requirements-dev.txt.

## T3 review: verified workflow mechanics

Read with `git show archive/pre-cleanup:architecture_eval/engine.py`: successful C turns call context_specialist + catalog_or_context (2 provider decisions); E calls catalog_or_context + independent_review (2). D calls supervisor first: clarify returns after 1, catalog requires 2, context/combined requires 3. Counts exclude embeddings and FixedRouter, which replays a decision locally without provider inference. Source: [archived engine](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/architecture_eval/engine.py), [shared model configuration](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/config/architecture_eval.json).

The [archived analysis](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/reports/architecture_eval/ANALISIS.md) identifies deterministic preparation/rendering failures, including S4 definition removal and DC contradictions becoming schema errors; it also notes the reviewer uses the same model and can share biases. The [archived A+ ADR](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md) records code fixes for contradictions and asking to complete a well-formed nonexistent code, assigns numeric guarantees to validation/SQL/templates, and records the assessment's USD 10 budget. Adding a reviewer is not a repair for those deterministic defects. Reconsider specialised workflows/retrieval if responsibilities or corpus size justify them; that is a design condition, not an experimental result.
