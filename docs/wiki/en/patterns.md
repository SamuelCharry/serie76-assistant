# Patterns

[Wiki](index.md) · [English](../en/patterns.md) · [Español](../es/patterns.md)

Pattern — where — why: decisions to defend in review.

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

[backend/conversation/agent.py](../../../backend/conversation/agent.py#L186) — Pydantic args_schema and StructuredTool constrain names, enums and argument sizes; malformed output cannot become arbitrary SQL.

### Append-only spend ledger

[scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L79) — The acceptance runner records reservation before network, then settlement/failure; unknown usage keeps its reservation. This is an evaluation control, not production billing enforcement.

### Error model

[backend/conversation/api.py](../../../backend/conversation/api.py#L76) — 503 plus safe error_code for provider/configuration failure; rollback prevents partial turns. Android maps status/code to actionable messages.

### Idempotent entrypoint

[docker/entrypoint.sh](../../../docker/entrypoint.sh#L1) — Migrate, load catalogue/glossary and ensure TEST ONLY users before Uvicorn. Existing passwords are never reset; [] disables new demo provisioning.

### One agent

Deterministic defects found in A–E (DC + 60 Hz validation and asking to complete a well-formed nonexistent code) were fixed in code; another LLM does not repair the validator or renderer. A reviewer shares model failure modes and gives no numeric guarantee: validation + SQL + templates own the numbers. [Archived defects, fixes and design](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), [reviewer limitation](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/reports/architecture_eval/ANALISIS.md).

The [archived engine](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/architecture_eval/engine.py) makes 2 provider decisions for completed C/E turns; D uses 1 for clarification, 2 for catalogue or 3 with context, excluding embeddings/local FixedRouter. With [19 provider failures in 103 calls](../../evidence/architecture_comparison.md) and the [USD 10 assessment budget](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), extra calls add failure exposure, latency and cost. These observations do not establish independent failure probabilities.

A+ achieved [50/55 in v4 with 4 provider-only failures](../../evidence/agent_acceptance.md), through Google. A–E was inconclusive: one agent is an engineering decision, not measured superiority. Reconsider multiple agents for genuinely different workflows or a large corpus requiring specialised retrieval; OpenRouter acceptance remains pending.

## Where in the code

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Known limits

A process-local call guard is not distributed quota or monetary accounting. Typed arguments and numeric occurrence checks do not guarantee semantic intent. A second model with correlated errors would not replace PDF/SQL validation; no experiment proves single-agent superiority.
