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

[backend/conversation/policy.py](../../../backend/conversation/policy.py#L139) — Ground filters, merge follow-ups and ask on contradictions; SQL/template owns technical values. DC + 60 Hz becomes a question.

### Typed tools

[backend/conversation/agent.py](../../../backend/conversation/agent.py#L156) — Pydantic args_schema and StructuredTool constrain names, enums and argument sizes; malformed output cannot become arbitrary SQL.

### Append-only spend ledger

[scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L77) — The acceptance runner records reservation before network, then settlement/failure; unknown usage keeps its reservation. This is an evaluation control, not production billing enforcement.

### Error model

[backend/conversation/api.py](../../../backend/conversation/api.py#L76) — 503 plus safe error_code for provider/configuration failure; rollback prevents partial turns. Android maps status/code to actionable messages.

### Idempotent entrypoint

[docker/entrypoint.sh](../../../docker/entrypoint.sh#L1) — Migrate, load catalogue/glossary and ensure TEST ONLY users before Uvicorn. Existing passwords are never reset; [] disables new demo provisioning.

### One agent

[backend/conversation/agent.py](../../../backend/conversation/agent.py#L456) — One decision reduces call paths; literal glossary fits this context, so no vector store is needed. The A–E experiment was inconclusive; this is engineering judgment, not measured superiority.

The [architecture comparison](../../evidence/architecture_comparison.md) had only 1/24 common scenarios and 19 provider failures; heterogeneous available sets cannot rank variants. A SQL agent, contextual vector agent, two specialists, supervisor and proposer/reviewer were compared. See [ADR 0001](../../adr/0001-arquitectura-agente.md) and [testing](testing.md) for frozen records.

## Where in the code

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Known limits

A process-local call guard is not distributed quota or monetary accounting. Typed arguments and numeric occurrence checks do not guarantee semantic intent. A second model with correlated errors would not replace PDF/SQL validation; no experiment proves single-agent superiority.
