# ADR 0001: arquitectura del agente (A+)

> Actualización 2026-11-05: este ADR conserva la decisión histórica; la aceptación OpenRouter está completada y T9 usa pgvector para ejemplos de interpretación y anclas, sin sustituir el glosario ni las cifras SQL; ver [Models y predeterminados provisionales](../../README.md#models-design-and-limitations), con v12 reservado tras las correcciones pendiente.

- Estado: aceptada para la entrega, pendiente de aceptación final con OpenRouter.
- Fecha: 2026-11-03.
- Sustituye: la recomendación provisional "B corregida" de `https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/contexto/06_ARQUITECTURAS_Y_RELEVO.md`, que nunca fue un resultado experimental.

## Contexto

El assessment pide:

- un agente LangChain con al menos una Tool propia sobre las tablas;
- consulta exacta por Base Part Number;
- recomendación por requisitos técnicos;
- seguimientos multi-turno;
- manejo de códigos inválidos, datos ausentes, ambigüedad y requisitos imposibles.

Además: PostgreSQL local, pgvector solo si hay búsqueda semántica, modelos OpenRouter configurables con un presupuesto de USD 10, y "the LLM must not invent or recall numbers".

Se compararon cinco configuraciones (A–E) en Google y la comparación quedó **inconclusa**: un único escenario común y 19 fallos del proveedor. Su evidencia está archivada en el tag `arch-eval-cohort-1`. Los defectos compartidos que se observaron eran:

- un renderizador que eliminaba la definición de S4;
- viñetas concatenadas con saltos de maquetado;
- DC+60 Hz convertido en error de esquema;
- un código bien formado inexistente que se pedía completar;
- trazas incompletas.

**Dato medido que decide el diseño:** `data/raw/series_76_summary.pdf` tiene 348 palabras y 16 definiciones. Todo el corpus de contexto cabe en unos 600 tokens.

## Decisión

Un único agente LangChain con tool-calling. Hace **una llamada LLM por turno** y tiene cuatro herramientas:

| Herramienta | Qué hace | Quién garantiza la exactitud |
|---|---|---|
| `get_actuator` | Hasta 4 códigos completos, con un enfoque (torque, FLA...) y `explain_terms` opcional | SQL parametrizado sobre el catálogo |
| `search_actuators` | Requisitos como delta (`refine`/`more`/`remove`), con supuestos visibles y `explain_terms` opcional | Pydantic + reglas + SQL |
| `explain_terms` | Definiciones literales del resumen, con página | Tabla `series76.context_terms` |
| `ask_clarification` | Pide el dato que falta, desambigua o declara la petición fuera de alcance | Mensajes fijos |

El LLM solo elige la herramienta y sus argumentos. El código hace todo lo demás:

1. **Canonicaliza códigos** (mayúsculas, espacios y guion omitido) **sin completarlos**. Un código parcial o sin `/A` recibe candidatos por prefijo y la decisión queda en manos del usuario.
2. **Fundamenta cada valor.** Toda cifra debe aparecer en la conversación, y todo valor categórico debe estar en un léxico determinista o en un *supuesto* que cite palabras reales del usuario; el supuesto se le muestra. Un código debe aparecer en la conversación o en el contexto persistido.
3. **Fusiona los seguimientos.** El modelo envía solo el delta y el código conserva las restricciones anteriores. Si cambia el servicio, se elimina la tasa incompatible y se informa.
4. **Detecta contradicciones** (DC con Hz o fases, ciclos con modulante, arranques con On/Off, ambas tasas) y responde con una pregunta específica que conserva el resto de requisitos.
5. **Consulta SQL** y **redacta la respuesta con plantillas** a partir de las filas. El texto conserva unidades in-lb/Nm, servicio, frecuencia (50/60 Hz, DC sin frecuencia, no especificada), `source_NA` frente a `not_in_layout` y la página/tabla de procedencia. El LLM no escribe prosa técnica.
6. **Deja una traza por turno:** parámetros crudos y fusionados, validación, contexto antes/después, renderizador, modelo, latencia y tokens. No se guarda razonamiento.

La guarda del punto 1 también corrige el fallo de D: si el modelo pide un código que el usuario ya escribió bien formado, el código lo consulta igualmente.

### Por qué no B (pgvector)

- **Recall.** Con un corpus de 16 definiciones, la recuperación top-k solo puede *perder* información. Ocurrió en `context_duty`: B recuperó la página correcta pero mostró otros términos. Un glosario estructurado tiene recall completo y una cita exacta.
- **Dependencias.** pgvector obliga a usar un modelo de embeddings vía OpenRouter, regenerar el índice por firma y mantener un segundo camino de fallo. No hay evidencia de que mejore algo frente al glosario.
- **Cuándo se reconsideraría:** si el corpus creciera (manuales, fichas por producto, documentos que no caben en el prompt). La extensión pgvector está prevista en el contrato de PostgreSQL y documentada en el experimento archivado.

### Por qué no C, D ni E (multiagente)

- Multiplican por 2–3 las llamadas, el costo y la latencia. Comparten proveedor y cuota, así que un 503 sigue tumbando el turno.
- El revisor usa el mismo modelo, con errores correlacionados. **Un segundo LLM no sustituye la validación numérica**, que aquí ya es determinista.
- Los defectos observados eran del renderizador y de la validación, no de razonamiento que otro LLM corrigiera.
- El piloto académico más cercano (orquestador LangGraph) solo cumplió *todos* los requisitos en 6 de 22 solicitudes. Muestra viabilidad, no superioridad.

## Evidencia y lo que falta

- **Implementación publicada:** Designing an LLM-Based Copilot for Manufacturing Equipment Selection, arXiv:2412.13774v1. Usa un orquestador más una máquina de estados LangGraph, GPT-4o, SQLite y Chroma con all-MiniLM-L6-v2, sobre 22 solicitudes evaluadas por dos ingenieros de un socio industrial. **No describe cómo consulta el SQL.** Reverificado el 2026-11-03.
- **Afirmación comercial:** TraceParts + Leo AI ofrece búsqueda de componentes en lenguaje natural con aclaraciones. No revela motor, ER ni número de agentes. La página no devolvió contenido el 2026-11-03; se cita según el relevo.
- **Documentación de datos, no de agentes:** la API Product Catalog de Schneider Electric (referencias, especificaciones, clasificación ETIM) y ETIM (clases, características, unidades). Respondió 403 el 2026-11-03. De aquí se adoptó el rigor de unidades y sinónimos, no un modelo EAV.
- **Inferencia propia:** que un glosario estructurado basta para este corpus y que un solo agente basta para estas tareas.
- **Lo que falta:** no hay una comparación emparejada que demuestre que A+ supera a B o D. La decisión es de ingeniería (responsabilidades, costo y control) y se valida con una cohorte de aceptación propia con un LLM real (`https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/`), no con un ranking.

## Riesgos aceptados

- Los términos fuera del resumen reciben una respuesta honesta ("the summary does not define that term"), no una explicación libre.
- Las respuestas por plantilla son menos fluidas que la prosa de un LLM. A cambio, ninguna cifra sale del modelo.
- El léxico determinista puede rechazar formulaciones válidas poco comunes. En ese caso el sistema pide confirmación; no inventa.
- Una pregunta con dos pasos dependientes se resuelve en dos turnos.
- La comprensión lingüística se valida solo con un LLM real. Las pruebas con interpretación simulada validan la capa determinista.

## Consecuencias

- Migración `003_context_terms.sql`, `scripts/ingest_summary.py` y `cli load-context`. `/ready` exige el glosario.
- `ConversationResponse` añade `clarification`, `terms` y `assumptions`. Es aditivo y el cliente Android ignora claves desconocidas.
- Los errores del proveedor responden 503 con `error_code` (`timeout`, `rate_limited`, `budget_exhausted`, `provider_unreachable`, `provider_error`, `not_configured`) y no se persiste ningún turno parcial.
- Los experimentos A–E y la evaluación de modelos quedan archivados en el tag `arch-eval-cohort-1`. Sus pruebas se omiten de forma explícita en la rama actual y pasan en el tag.
