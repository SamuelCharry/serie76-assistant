# T8e backend: cuarto conjunto retenido

## Resultado comprobado

La evidencia v4 contiene **45 conversaciones y 81 turnos**. La medición en vivo previa fue **24/45 aprobadas (53 %)**; esta entrega no repitió Gemini ni hizo llamadas pagadas. Se añadieron las 45 conversaciones al replay guionizado v7, que pasó **316/316 escenarios**. La suite Python pasó **371 pruebas, 2 omitidas**. El escáner de texto visible y el control offline de esquema pasaron.

El backend se reconstruyó con el override keyless, sin tocar el volumen PostgreSQL. `/ready` devolvió **HTTP 200** y el contenedor confirmó `keyless=True`.

| Corte | Commit | Evidencia |
|---|---|---|
| Límites y servicio | `ca88c8b` | Pruebas fallidas primero para `no more than`, `mod` y búsqueda aleatoria; comprobación independiente excluye filas que violen filtros. |
| Peligro y cero resultados | `e62b027` | Polvo combustible pide confirmación; `yes` aplica Explosionproof y el rechazo de área clasificada aplica Weatherproof. |
| Torque bajo límite superior | `f1e6735` | El orden y la etiqueta usan el torque calificante más próximo por debajo del límite. |
| Plan de respuesta y referencias | `4c14946` | Una tabla de métricas decide campo, veredicto, razón LRA/FLA, ficha y paginación; `on_screen` guarda el orden mostrado. |
| Cohorte v4 | `3f53077` | 45 conversaciones incorporadas en v7 con aserciones de integridad, forma y referencias. |
| Preferencia y alternativas | `db4b77b` | Se descarta un `sort_by` no expresado; el conflicto de 3 fases ofrece ambas relajaciones desde SQL. |

## Integridad y contrato

La normalización determinista reconoce límites superiores (`no more than`, `at most`, `up to`, `max`, `≤`, `below`, `under`, `hasta`, `máximo`) y `mod` como Modulating. La comprobación posterior exige que cada coincidencia positiva satisfaga servicio, categorías, límites de servicio y límites de frecuencia. Si SQL y esa comprobación difieren, el resultado excluye las filas conflictivas y deja `postcondition_excluded` en la traza. Las alternativas de cero resultados se etiquetan con el requisito que se tendría que relajar. Las pruebas aleatorias comprueban tanto filas SQL como modelos presentados.

El planificador usa un solo vocabulario de campos para lookup y métricas. Las respuestas de una sola propiedad muestran ese campo; las preguntas comparativas dan un veredicto; LRA/FLA se calcula con ambas columnas publicadas a la misma frecuencia. `show all` devuelve la lista completa con valores clave y `next` pagina sin volver a preguntar. La lista `on_screen` conserva los modelos visibles en orden, incluidos comparaciones y elecciones. Las preguntas de catálogo sobre voltajes, enclosures, servicios y total usan recuentos SQL.

El esquema de tools quedó **igual antes y después**: 6 arrays, 5487 bytes, profundidad 7, **107 enum values**, 2 requeridos, cero nodos prohibidos y cero rangos numéricos. No se añadió ninguna decisión LLM por turno.

## Respuestas guionizadas capturadas

El JSON de las ejecuciones seleccionadas está en [T8e-scenarios.json](T8e-scenarios.json). Estas respuestas usaron decisiones guionizadas y PostgreSQL local:

| Caso | Respuesta observada |
|---|---|
| S1-06 | `2 actuators meet: Weatherproof, 220 V, torque <= 100 Nm.` La lista ordenada empieza por `761B00-11320000/A` (100 Nm) y sigue con `761A00-11320000/A` (80 Nm). |
| S1-05 | `762A00-11320000/A LRA/FLA at 60 Hz: 1.2 A / 1 A = 1.2 (unitless).` |
| S2-06 | `Published supply voltages: 24 V (10 models), 110 V (21 models), 220 V (33 models).` |
| S3-01 | `13 actuators meet: Modulating service, 110 V, torque ≥ 200 Nm.` Después, `My pick: 763A00-11300000/A — Modulating torque 220 Nm; FLA 50 Hz 2.5 A.` |
| E-SHORTREF-01 | `compare the top 3` compara exactamente `761A00-11320000/A`, `761B00-11320000/A`, `762A00-11320000/A`. |
| E-IMPOSSIBLE-01 | `All 3-phase models are Weatherproof in this catalogue. If you can drop Explosionproof, Weatherproof 3-phase models are available. If you can drop 3-phase, Explosionproof 1-phase models are available.` |

## Límite de la evidencia

El replay confirma las rutas de código y los valores SQL para decisiones guionizadas. No demuestra que Gemini interprete las 45 conversaciones nuevas correctamente; la tasa de aprobación en vivo después de T8e sigue pendiente de una nueva evaluación autorizada.
