# Patterns

[Wiki](index.md) · [English](../en/patterns.md) · [Español](../es/patterns.md)

Pattern — where — why: decisions to defend in review.

### T8/T9: decisions and costs

- **One decision, no generated figures.** The LLM proposes intent/arguments; SQL and templates preserve figures, units, N/A and provenance. Complete-code routes, Submit and actions invoke neither chat nor embeddings. This reduces latency/cost while requiring explicit policies and bounded schemas.
- **Planner and final guard.** [answer_planner.py](../../../backend/conversation/answer_planner.py) chooses field/verdict; [requirement_coverage.py](../../../backend/conversation/requirement_coverage.py) and [integrity.py](../../../backend/conversation/integrity.py) check quantities, units, bounds and rows after merging. Clarification can interrupt flow, but omitting a requirement changes selection.
- **Declared ranking.** [ranking.py](../../../backend/conversation/ranking.py) publishes criterion and tie-breakers; provisional recommendations and relaxed alternatives are labelled. Missing prices and site suitability cannot be inferred from a score.
- **Additive-only retrieval.** [embeddings.py](../../../backend/conversation/embeddings.py) helps interpret phrases; it never provides product knowledge or replaces filters/negations. Always-on deterministic parsing, 1.5 s and zero retries bound its impact; it adds cost/dependency and gained only one conversation in round 9.
- **One card and actions.** Local review before Submit prevents partial selections being sent; structured actions avoid reinterpreting them. Owner-scoped soft deletion hides a conversation; Undo cancels the five-second pending DELETE, not a deletion already confirmed by the server.
- **Voice and debug.** Preferred on-device SpeechRecognizer avoids a server audio integration; fallback does not guarantee offline operation. Hidden per-answer debug exposes the selected decision without loading every trace; seven taps do not replace authentication/ownership or `DEV_DEBUG`.

[Current architecture](agent.md), [contract](api.md), [Android](android.md), [method and limits](testing.md#behavior-evaluation). At 100× traffic, per-process quota/capacity, external calls and open transactions still need measurement/redesign; T9 does not establish distributed scalability.

### Repository

[backend/catalog/repository.py](../../../backend/catalog/repository.py#L142) — Keeps SQL, decimal conversion and scope rules behind a deterministic interface. Android has its own repository interface for UI tests.

### Versioned SQL migrations

[backend/catalog/db.py](../../../backend/catalog/db.py#L32) — Checksums and a transaction/advisory lock prevent silent edits or partial migration. Never edit applied SQL.

### Singleton active catalogue

[backend/catalog/loader.py](../../../backend/catalog/loader.py#L381) — One active import pointer; transactional activation preserves prior versions. Repeating the same PDF/pipeline/hash is idempotent.

### Message snapshot

[backend/conversation/store.py](../../../backend/conversation/store.py#L70) — Persist the user/assistant pair, products, context and trace atomically. A later catalogue activation does not rewrite old responses.

### Deterministic policy around the LLM

[backend/conversation/policy.py](../../../backend/conversation/policy.py#L142) — Ground filters, merge follow-ups and ask on contradictions; SQL/template owns technical values. DC + 60 Hz becomes a question.

### Typed tools

[backend/conversation/tool_wire.py](../../../backend/conversation/tool_wire.py) — StructuredTool advertises compact JSON Schema; code expands its bounds and validates strict canonical Pydantic models before SQL. Names, enums, argument sizes and numeric limits remain checked.

### Append-only spend ledger

[scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L79) — The acceptance runner records reservation before network, then settlement/failure; unknown usage keeps its reservation. This is an evaluation control, not production billing enforcement.

### Error model

[backend/conversation/api.py](../../../backend/conversation/api.py#L76) — 503 plus safe error_code for provider/configuration failure; rollback prevents partial turns. Android maps status/code to actionable messages.

### Idempotent entrypoint

[docker/entrypoint.sh](../../../docker/entrypoint.sh#L1) — Migrate, load catalogue/glossary and ensure TEST ONLY users before Uvicorn. Existing passwords are never reset; [] disables new demo provisioning.

### One agent

Deterministic defects found in A–E (DC + 60 Hz validation and asking to complete a well-formed nonexistent code) were fixed in code; another LLM does not repair the validator or renderer. A reviewer shares model failure modes and gives no numeric guarantee: validation + SQL + templates own the numbers. [Archived defects, fixes and design](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), [reviewer limitation](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/reports/architecture_eval/ANALISIS.md).

The [archived engine](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/architecture_eval/engine.py) makes 2 provider decisions for completed C/E turns; D uses 1 for clarification, 2 for catalogue or 3 with context, excluding embeddings/local FixedRouter. With [19 provider failures in 103 calls](../../evidence/architecture_comparison.md) and the [USD 10 assessment budget](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), extra calls add failure exposure, latency and cost. These observations do not establish independent failure probabilities.

A+ achieved [50/55 in v4 with 4 provider-only failures](../../evidence/agent_acceptance.md), through Google. A–E was inconclusive: one agent is an engineering decision, not measured superiority. Reconsider multiple agents for genuinely different workflows or a large corpus requiring specialised retrieval; OpenRouter acceptance completed on 2026-11-05; see [Models](../../../README.md#models-design-and-limitations). Held-out v14 scored 32/45 and v15 v1 scored 42/60 before P1-F; fresh post-P1-F provider validation remains pending.

### Structured interaction and deterministic presentation

[interactions.py](../../../backend/conversation/interactions.py) validates pending IDs/options and removable filters. Submit is already structured, so another interpretation call would add latency and a chance to change the user's choice. Code applies it and reruns SQL. [quality.py](../../../backend/conversation/quality.py) computes comparison winners, hidden rows and optional suggestions; Android renders those fields instead of asking the LLM to judge them. Migration 005 snapshots the new fields while keeping old messages readable.

### Bounded retries and connection lifetime

[agent.py](../../../backend/conversation/agent.py) uses LangChain retry for transient failures only, while keeping one completed decision per language turn and zero for greetings/structured submissions. Defaults: `OPENROUTER_FALLBACK_MODEL=` (disabled), `AGENT_TIMEOUT_S=45`, `AGENT_TURN_DEADLINE_S=60`, `AGENT_RETRY_MIN_REMAINING_S=10`. Each attempt counts toward `AGENT_MAX_CALLS_PER_HOUR=120`; no 4xx retry and no SDK retry. See [configuration](operations.md#configuration-reference).

The Android pool expires after 30 s, before Uvicorn's 75 s keep-alive, to address reuse of a socket closed by the former 5 s server timeout. Automatic POST retries remain disabled because a timed-out write may already have committed. [Troubleshooting and evidence limits](operations.md#first-tap-fails-after-idle).

## Where in the code

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Known limits

A process-local call guard is not distributed quota or monetary accounting. Typed arguments and numeric occurrence checks do not guarantee semantic intent. A second model with correlated errors would not replace PDF/SQL validation; no experiment proves single-agent superiority.
