# Patrones

[Wiki](index.md) · [English](../en/patterns.md) · [Español](../es/patterns.md)

Patrón — dónde — por qué: decisiones que defender en revisión.

### Repositorio

[backend/catalog/repository.py](../../../backend/catalog/repository.py#L142) — Encapsula SQL, conversión decimal y alcances en una interfaz determinista. Android tiene otra interfaz repository para pruebas de UI.

### Migraciones SQL versionadas

[backend/catalog/db.py](../../../backend/catalog/db.py#L32) — Checksums y transacción/bloqueo asesor evitan cambios silenciosos o migraciones parciales. No editar SQL aplicado.

### Catálogo activo singleton

[backend/catalog/loader.py](../../../backend/catalog/loader.py#L381) — Un puntero de importación activa; activación transaccional conserva versiones. Repetir PDF/firma/hash es idempotente.

### Instantánea de mensaje

[backend/conversation/store.py](../../../backend/conversation/store.py#L70) — Persiste par usuario/asistente, productos, contexto y traza atómicamente. Activar otro catálogo no reescribe respuestas previas.

### Política determinista alrededor del LLM

[backend/conversation/policy.py](../../../backend/conversation/policy.py#L142) — Fundamenta filtros, fusiona seguimientos y pregunta ante contradicciones; SQL/plantilla controla cifras. DC + 60 Hz produce pregunta.

### Herramientas tipadas

[backend/conversation/tool_wire.py](../../../backend/conversation/tool_wire.py) — StructuredTool anuncia JSON Schema compacto; el código expande sus límites y valida modelos canónicos Pydantic estrictos antes de SQL. Conserva controles de nombres, enums, tamaños y límites numéricos.

### Ledger de gasto append-only

[scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L79) — El evaluador reserva antes de red y añade liquidación/fallo; uso desconocido conserva reserva. Es control de evaluación, no límite monetario productivo.

### Modelo de errores

[backend/conversation/api.py](../../../backend/conversation/api.py#L76) — 503 con error_code seguro ante proveedor/configuración; rollback evita turnos parciales. Android traduce estado/código a mensajes accionables.

### Entrypoint idempotente

[docker/entrypoint.sh](../../../docker/entrypoint.sh#L1) — Migra, carga catálogo/glosario y asegura usuarios TEST ONLY antes de Uvicorn. Nunca restablece contraseñas; [] desactiva nuevas cuentas demo.

### Un agente

Los defectos deterministas de A–E (validación DC + 60 Hz y pedir completar un código bien formado inexistente) se corrigieron en código; otro LLM no repara validador ni renderizador. Un revisor comparte modos de fallo y no garantiza cifras: las controla validación + SQL + plantillas. [Defectos, correcciones y diseño archivados](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), [límite del revisor](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/reports/architecture_eval/ANALISIS.md).

El [motor archivado](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/architecture_eval/engine.py) hace 2 decisiones de proveedor en turnos completos C/E; D usa 1 al aclarar, 2 en catálogo o 3 con contexto, excluyendo embeddings/FixedRouter local. Con [19 fallos de proveedor en 103 llamadas](../../evidence/architecture_comparison.md) y [presupuesto de USD 10](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md), cada llamada extra añade exposición a fallo, latencia y coste. No son probabilidades de fallo independientes.

A+ logró [50/55 en v4 con 4 fallos solo de proveedor](../../evidence/agent_acceptance.md), mediante Google. A–E fue inconcluso: un agente es decisión de ingeniería, no superioridad medida. Reconsideraría varios ante flujos realmente distintos o un corpus grande que exija recuperación especializada; aceptación OpenRouter pendiente.

## Dónde está en el código

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Límites conocidos

La guarda por proceso no es cuota distribuida ni contabilidad monetaria. Tipos y presencia de números no garantizan intención semántica. Otro modelo con errores correlacionados no reemplaza validación PDF/SQL; ningún experimento prueba superioridad del agente único.
