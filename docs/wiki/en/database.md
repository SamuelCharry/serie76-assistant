# Database

[Wiki](index.md) · [English](../en/database.md) · [Español](../es/database.md)

The relational schema, numeric authority and concrete rows behind the tools.

T9 adds `series76.example_bank`, `concept_anchor` and `example_dataset` through migrations 007/008: 768-dimensional vectors, phrasings/interpretations, provenance, active state and versioned manifests. They are not a source of technical figures. The diagram and queries below show the relational core; [glibc-compatible pgvector pin](operations.md#pgvector) and [bank loading](operations.md#example-bank).

```mermaid
erDiagram
    documents ||--o{ imports : sources
    documents ||--o{ context_terms : defines
    imports ||--o| catalog_state : activates
    imports ||--o{ source_tables : contains
    imports ||--o{ entries : versions
    source_tables ||--o{ entries : contains
    entries ||--o{ service_specs : service
    entries ||--o{ frequency_specs : frequency
    entries ||--o{ source_cells : evidence
    users |o--o{ conversations : owns
    users ||--o{ auth_sessions : authenticates
    conversations ||--o{ messages : contains
    auth_login_limits {
        text scope_hash PK
        timestamptz window_start
        integer attempts
    }
```

Relationships above follow the [SQL migrations](../../../backend/catalog/migrations); [live FK inspection](../../../reports/submission/T3-database.json) confirms them. `conversations.owner_id` is nullable: pre-login history stays quarantined. `auth_login_limits` has no FK. Migration-runner metadata is separate; the retained [full schema SVG](../../er-series76.svg) is a historical snapshot.

An entry is an occurrence within an import/table, not a globally deduplicated part. `service_specs` separates On/Off, modulating and shared values; `frequency_specs` separates 50/60 Hz, unspecified and not applicable. Measurements use NUMERIC, variable evidence uses JSONB. A singleton `catalog_state` points to one active import. Messages store product/context/trace snapshots without an FK to catalogue entries, preserving old answers after activation changes.

## Real read-only examples

Queried locally through `backend.catalog.cli.local_environment()` and `connect()`, with `connection.read_only=True`; `SHOW transaction_read_only` returned `on`. Only SELECTs and SHOW ran. No users, password hashes, auth sessions or tokens were selected. SQL and complete returned projections are retained in [T3-database.json](../../../reports/submission/T3-database.json). Decimal values below are JSON strings in this evidence export, not changed catalogue types.

### Entry and service specifications

```sql
SELECT e.base_part_number,e.supply_voltage_v,e.supply_current,e.phase_count,e.motor_power_w,s.service,s.torque_nm,s.torque_in_lb,s.duty_s4_percent,s.cycles_per_hour,s.starts_per_hour
FROM series76.entries e
JOIN series76.catalog_state c ON c.active_import_id=e.import_id
JOIN series76.service_specs s ON s.entry_id=e.id
WHERE e.base_part_number='761A00-11300000/A'
ORDER BY s.service;
```

```json
[
  {
    "base_part_number": "761A00-11300000/A",
    "supply_voltage_v": "110",
    "supply_current": "AC",
    "phase_count": 1,
    "motor_power_w": "15",
    "service": "modulating",
    "torque_nm": "65",
    "torque_in_lb": "580",
    "duty_s4_percent": "40",
    "cycles_per_hour": null,
    "starts_per_hour": 960
  },
  {
    "base_part_number": "761A00-11300000/A",
    "supply_voltage_v": "110",
    "supply_current": "AC",
    "phase_count": 1,
    "motor_power_w": "15",
    "service": "on_off",
    "torque_nm": "80",
    "torque_in_lb": "700",
    "duty_s4_percent": "40",
    "cycles_per_hour": 36,
    "starts_per_hour": null
  }
]
```

### Explicit N/A

```sql
SELECT e.base_part_number,e.data_status,e.motor_power_w,e.field_status->>'motor_power_w' AS power_status
FROM series76.entries e
JOIN series76.catalog_state c ON c.active_import_id=e.import_id
WHERE e.data_status='source_NA'
ORDER BY e.base_part_number LIMIT 1;
```

```json
[
  {
    "base_part_number": "761A00-11330C00/A",
    "data_status": "source_NA",
    "motor_power_w": null,
    "power_status": "source_NA"
  }
]
```

### Cell evidence and provenance

```sql
SELECT e.base_part_number,t.source_page,t.source_table,e.source_row,sc.field,sc.status,sc.unit,sc.evidence
FROM series76.entries e
JOIN series76.catalog_state c ON c.active_import_id=e.import_id
JOIN series76.source_tables t ON t.id=e.table_id
JOIN series76.source_cells sc ON sc.entry_id=e.id
WHERE e.base_part_number='761A00-11300000/A' AND sc.field='motor_power_w';
```

```json
[
  {
    "base_part_number": "761A00-11300000/A",
    "source_page": 1,
    "source_table": "p1_t1",
    "source_row": 1,
    "field": "motor_power_w",
    "status": "reported",
    "unit": "W",
    "evidence": {
      "raw_text": "15",
      "value": 15,
      "method": "image_consensus",
      "source_sha256": "4c28023929183df8e2a763e759cc84572b44604b30837a21e22c1166f88267e0",
      "source_span_rows": [
        1,
        2
      ],
      "bbox": [
        2051.25,
        826.5,
        2140.75,
        923.0
      ]
    }
  }
]
```

Projection excerpt; complete evidence, including alternate reads, is in the linked JSON.

### Literal glossary term

```sql
SELECT term_key,label,definition,page
FROM series76.context_terms
WHERE term_key='fla'
ORDER BY id LIMIT 1;
```

```json
[
  {
    "term_key": "fla",
    "label": "Full Load Current (FLA)",
    "definition": "The electric current (in Amps) drawn by the motor under its maximum rated load.",
    "page": 2
  }
]
```

### Stored assistant message and trace

```sql
SELECT role,content,tool_calls->0->>'name' AS tool,tool_calls->0->'parameters'->'part_numbers' AS part_numbers,tool_calls->0->'validation' AS validation,tool_calls->0->>'renderer' AS renderer
FROM series76.messages
WHERE role='assistant' AND tool_calls->0->>'name'='get_actuator' AND tool_calls->0->'parameters'->'part_numbers'='["761A00-11300000/A"]'::jsonb AND content LIKE '761A00-11300000/A%'
ORDER BY sequence LIMIT 1;
```

```json
[
  {
    "role": "assistant",
    "content": "761A00-11300000/A — weatherproof, 110 V AC 1-phase\n  • On/Off torque: 700 in-lb / 80 Nm\n  • Modulating torque: 580 in-lb / 65 Nm\n  • Duty S4 On/Off: 40%\n  • Duty S4 Modulating: 40%\n  • On/Off cycles per hour: 36\n  • Modulating starts per hour: 960\n  • Operating time at 50 Hz: 20 s\n  • Operating time at 60 Hz: 17 s\n  • FLA at 50 Hz: 1.1 A\n  • FLA at 60 Hz: 1.2 A\n  • LRA at 50 Hz: 1.3 A\n  • LRA at 60 Hz: 1.4 A\n  • Motor power: 15 W\n  Source: series_76_electric_data.pdf, page 1, table p1_t1.",
    "tool": "get_actuator",
    "part_numbers": [
      "761A00-11300000/A"
    ],
    "validation": [
      "ok"
    ],
    "renderer": "get_actuator"
  }
]
```

This is a real persisted deterministic answer. Its stored trace alone does not establish which provider produced the decision; it is not OpenRouter acceptance.

## Where in the code

- [backend/catalog/db.py](../../../backend/catalog/db.py#L32)
- [backend/catalog/repository.py](../../../backend/catalog/repository.py#L126)
- [backend/catalog/loader.py](../../../backend/catalog/loader.py#L133)
- [backend/conversation/store.py](../../../backend/conversation/store.py#L70)

## Known limits

The import loader is catalogue-specific, with a bounded JSON size; no automatic version deletion or migration rollback UI exists. Shared values are not independent measurements. A glossary definition never certifies an entry. Historic SQL equality checks are in [PostgreSQL evidence](../../evidence/postgres.md).
