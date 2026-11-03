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

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL, agente y Android siguen pendientes.

Siguiente acción: PostgreSQL. La sección siguiente conserva el estado histórico de revisión manual y los issues; no afirma una nueva revisión remota.

## Siguiente acción histórica

El catálogo revisado está en data/reviewed/catalog-v1 y la auditoría completa en reports/manual_review/AUDIT.md. Se revisaron visualmente las siete tablas y notas; las seis diferencias del OCR están resueltas en esa exportación mediante decisiones exactas. El siguiente bloque es esquema y carga idempotente PostgreSQL (#2). Docker debe verificarse para la base y el backend (#1). Después implementar herramientas/agente (#3), contrato conversacional (#4) y Android (#5). Los perfiles HTML anteriores siguen describiendo el OCR crudo y la referencia del benchmark.

Revisión en vivo de los siete issues: todos abiertos. El issue #2 conserva sin marcar los tres primeros subpasos ya comprobados localmente (OCR, comparación y revisión de las 11 filas iniciales). No corresponde cerrar el issue: faltan validación completa, ingestión y modelos. No se modificaron los issues remotos durante esta revisión. Los cambios del laboratorio siguen sin commit; no confundir archivos locales con una entrega publicada.

Estos siete grupos conservan la clasificación del assessment; no son una secuencia rígida. El grupo 1 incluye la entrega final y el grupo 6 se actualiza durante el trabajo. No cerrar un milestone mientras conserve tareas obligatorias pendientes.
