# Seguimiento local actual

OCR, PostgreSQL y consultas técnicas están implementados y verificados. PostgreSQL 17.11 y backend corren en Docker. La reconstrucción SQL coincide en 68 referencias, 869 cifras, cuatro N/A, cinco marcas y 272 atributos de contexto (941/941 comprobaciones primarias). Las 62 pruebas actuales pasan con SERIES76_TEST_DB=1. El reinicio de DB/backend conserva catálogo y hash. Ver docs/POSTGRES.md y https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/postgres/summary.json. Agente, LangChain, historial, selección del LLM y Android siguen pendientes.

Los apartados siguientes conservan historia anterior. Sus pendientes de PostgreSQL/Docker ya fueron resueltos. No se modificaron issues remotos; el grupo de datos sigue abierto porque falta integración/modelos.

# Seguimiento del proyecto

Repositorio: https://github.com/SamuelCharry/serie76-assistant (privado).

| Grupo | Milestone | Issue | Estado |
|---|---|---|---|
| 1. Entorno y entrega | [M1](https://github.com/SamuelCharry/serie76-assistant/milestone/1) | [#1](https://github.com/SamuelCharry/serie76-assistant/issues/1) | En curso: Python listo; Docker pendiente; entrega al final |
| 2. Datos, OCR y modelos | [M2](https://github.com/SamuelCharry/serie76-assistant/milestone/2) | [#2](https://github.com/SamuelCharry/serie76-assistant/issues/2) | Pipeline OCR real verificado; PostgreSQL/modelos pendientes; checklist remoto sin modificar |
| 3. Backend y agente | [M3](https://github.com/SamuelCharry/serie76-assistant/milestone/3) | [#3](https://github.com/SamuelCharry/serie76-assistant/issues/3) | Pendiente |
| 4. Contrato API | [M4](https://github.com/SamuelCharry/serie76-assistant/milestone/4) | [#4](https://github.com/SamuelCharry/serie76-assistant/issues/4) | Pendiente |
| 5. Android | [M5](https://github.com/SamuelCharry/serie76-assistant/milestone/5) | [#5](https://github.com/SamuelCharry/serie76-assistant/issues/5) | Pendiente |
| 6. Documentación y reproducibilidad | [M6](https://github.com/SamuelCharry/serie76-assistant/milestone/6) | [#6](https://github.com/SamuelCharry/serie76-assistant/issues/6) | Parcial; verificar producto completo al final |
| 7. Login y voz | [M7](https://github.com/SamuelCharry/serie76-assistant/milestone/7) | [#7](https://github.com/SamuelCharry/serie76-assistant/issues/7) | Opcional, diferido |

## Evidencia del primer paso — 2026-11-02

- Repositorio publicado y clon verificado en el PC de Samuel.
- Entorno .venv creado desde cero; requirements.txt instalado y pip check sin incompatibilidades declaradas.
- Renderizado de página 1 a 300 DPI ejecutado usando ese entorno: data/ocr/page1-clean-venv. Es renderizado, no reconocimiento OCR.
- Android Studio, Android SDK y adb localizados. No se compiló ni ejecutó una app.
- Se intentó iniciar Docker Desktop. El proceso terminó y docker info no pudo conectar con dockerDesktopLinuxEngine. Los registros muestran cierre del backend; no permiten atribuir una causa concreta con la evidencia revisada. No se construyeron contenedores.
- Sin llamadas a OpenRouter.

## Estado actual

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/pipeline/RESULTADOS.md y https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL, agente y Android siguen pendientes.

Siguiente acción: PostgreSQL. La sección siguiente conserva el estado histórico de revisión manual y los issues; no afirma una nueva revisión remota.

## Siguiente acción histórica

El catálogo revisado está en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/data/reviewed/catalog-v1 y la auditoría completa en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/manual_review/AUDIT.md. Se revisaron visualmente las siete tablas y notas; las seis diferencias del OCR están resueltas en esa exportación mediante decisiones exactas. El siguiente bloque es esquema y carga idempotente PostgreSQL (#2). Docker debe verificarse para la base y el backend (#1). Después implementar herramientas/agente (#3), contrato conversacional (#4) y Android (#5). Los perfiles HTML anteriores siguen describiendo el OCR crudo y la referencia del benchmark.

Revisión en vivo de los siete issues: todos abiertos. El issue #2 conserva sin marcar los tres primeros subpasos ya comprobados localmente (OCR, comparación y revisión de las 11 filas iniciales). No corresponde cerrar el issue: faltan validación completa, ingestión y modelos. No se modificaron los issues remotos durante esta revisión. Los cambios del laboratorio siguen sin commit; no confundir archivos locales con una entrega publicada.

Estos siete grupos conservan la clasificación del assessment; no son una secuencia rígida. El grupo 1 incluye la entrega final y el grupo 6 se actualiza durante el trabajo. No cerrar un milestone mientras conserve tareas obligatorias pendientes.
