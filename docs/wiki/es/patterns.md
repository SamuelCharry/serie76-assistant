# Patrones

[Wiki](index.md) · [English](../en/patterns.md) · [Español](../es/patterns.md)

Patrón — dónde — por qué: decisiones que defender en revisión.

### T8/T9: decisiones y costes

- **Una decisión, cero cifras generadas.** El LLM propone intención/argumentos; SQL y plantillas conservan cifras, unidades, N/A y procedencia. Las rutas de códigos completos, Submit y acciones no llaman chat ni embeddings. Reduce latencia/coste, a cambio de mantener políticas explícitas y esquemas acotados.
- **Planificador y guarda final.** [answer_planner.py](../../../backend/conversation/answer_planner.py) elige campo/veredicto; [requirement_coverage.py](../../../backend/conversation/requirement_coverage.py) y [integrity.py](../../../backend/conversation/integrity.py) comprueban cantidades, unidades, límites y filas tras la fusión. Pedir aclaración puede interrumpir el flujo, pero omitir un requisito cambia la selección.
- **Ranking declarado.** [ranking.py](../../../backend/conversation/ranking.py) publica criterio y desempates; una recomendación provisional o alternativa relajada se etiqueta. Ni precio ausente ni idoneidad de instalación se deducen de una puntuación.
- **Retrieval solo aditivo.** [embeddings.py](../../../backend/conversation/embeddings.py) ayuda a interpretar frases; nunca provee conocimiento de producto ni sustituye filtros/negaciones. Parser determinista ON/OFF, 1.5 s y cero retries limitan el impacto; suma coste y dependencia y solo ganó una conversación en ronda 9.
- **Una tarjeta y acciones.** Revisión local antes de Submit evita enviar selecciones parciales; acciones estructuradas evitan reinterpretarlas. Borrado lógico por propietario permite ocultar una conversación; Undo cancela el DELETE pendiente de cinco segundos, no restaura una eliminación ya confirmada por servidor.
- **Voz y debug.** SpeechRecognizer on-device preferido evita una integración de audio del servidor; el fallback no garantiza offline. Debug oculto por respuesta permite inspeccionar la decisión elegida sin cargar todas las trazas; siete toques no sustituyen autenticación/propiedad ni `DEV_DEBUG`.

[Arquitectura vigente](agent.md), [contrato](api.md), [Android](android.md), [método y límites](testing.md#behavior-evaluation). A 100× tráfico, la cuota y capacidad por proceso, llamadas externas y transacciones abiertas siguen requiriendo medición/rediseño; T9 no prueba escalabilidad distribuida.

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

### Interacción estructurada y presentación determinista

[interactions.py](../../../backend/conversation/interactions.py) valida IDs/opciones pendientes y filtros removibles. Submit ya está estructurado: otra interpretación añadiría latencia y riesgo de cambiar la elección. El código lo aplica y repite SQL. [quality.py](../../../backend/conversation/quality.py) calcula ganadores, filas ocultas y sugerencias opcionales; Android presenta esos campos sin pedir al LLM que los juzgue. La migración 005 conserva los campos nuevos como snapshots y mantiene mensajes antiguos legibles.

### Reintentos acotados y vida de conexiones

[agent.py](../../../backend/conversation/agent.py) usa retry LangChain solo ante fallos transitorios, conservando una decisión completada por turno de lenguaje y cero para saludos/envíos estructurados. Predeterminados: `OPENROUTER_FALLBACK_MODEL` vacío, `AGENT_TIMEOUT_S=45`, `AGENT_TURN_DEADLINE_S=60`, `AGENT_RETRY_MIN_REMAINING_S=10`. Cada intento cuenta para `AGENT_MAX_CALLS_PER_HOUR=120`; sin retry 4xx ni del SDK. Ver [configuración](operations.md#referencia-de-configuración).

El pool Android expira a 30 s, antes del keep-alive Uvicorn de 75 s, para evitar reutilizar sockets cerrados por el antiguo timeout de 5 s. Los retries POST automáticos siguen desactivados: una escritura con timeout pudo haberse confirmado. [Diagnóstico y límites de evidencia](operations.md#falla-el-primer-toque-tras-inactividad).

## Dónde está en el código

- [backend/auth/api.py](../../../backend/auth/api.py#L24)
- [tests/test_submission_readiness.py](../../../tests/test_submission_readiness.py#L1)

## Límites conocidos

La guarda por proceso no es cuota distribuida ni contabilidad monetaria. Tipos y presencia de números no garantizan intención semántica. Otro modelo con errores correlacionados no reemplaza validación PDF/SQL; ningún experimento prueba superioridad del agente único.
