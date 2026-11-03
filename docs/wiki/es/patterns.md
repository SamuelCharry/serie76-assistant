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

[backend/conversation/policy.py](../../../backend/conversation/policy.py#L139) — Fundamenta filtros, fusiona seguimientos y pregunta ante contradicciones; SQL/plantilla controla cifras. DC + 60 Hz produce pregunta.

### Herramientas tipadas

[backend/conversation/agent.py](../../../backend/conversation/agent.py#L156) — Pydantic args_schema y StructuredTool restringen nombres, enums y tamaños; salida malformada no se convierte en SQL arbitrario.

### Ledger de gasto append-only

[scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L77) — El evaluador reserva antes de red y añade liquidación/fallo; uso desconocido conserva reserva. Es control de evaluación, no límite monetario productivo.

### Modelo de errores

[backend/conversation/api.py](../../../backend/conversation/api.py#L76) — 503 con error_code seguro ante proveedor/configuración; rollback evita turnos parciales. Android traduce estado/código a mensajes accionables.

### Entrypoint idempotente

[docker/entrypoint.sh](../../../docker/entrypoint.sh#L1) — Migra, carga catálogo/glosario y asegura usuarios TEST ONLY antes de Uvicorn. Nunca restablece contraseñas; [] desactiva nuevas cuentas demo.

### Un agente

[backend/conversation/agent.py](../../../backend/conversation/agent.py#L456) — Una decisión reduce caminos de llamada; el glosario literal cabe en contexto y no necesita vectores. El experimento A–E fue inconcluso; es decisión de ingeniería, no superioridad medida.

La [comparación de arquitecturas](../../evidence/architecture_comparison.md) solo tuvo 1/24 escenarios comunes y 19 fallos de proveedor; conjuntos disponibles distintos no permiten ordenar variantes. Se compararon agente SQL, agente contextual con vectores, dos especialistas, supervisor y proponente/revisor. Ver [ADR 0001](../../adr/0001-arquitectura-agente.md) y [pruebas](testing.md) para registros congelados.

## Dónde está en el código

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Límites conocidos

La guarda por proceso no es cuota distribuida ni contabilidad monetaria. Tipos y presencia de números no garantizan intención semántica. Otro modelo con errores correlacionados no reemplaza validación PDF/SQL; ningún experimento prueba superioridad del agente único.
