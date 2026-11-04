# T8c backend: segundo conjunto retenido

## Resultado comprobado

El archivo crudo v2 contiene **51 conversaciones y 91 turnos** (el encargo decía 50). Se importaron todas como casos guionizados; no se hicieron llamadas pagadas ni inferencia durante esta entrega. El autoensayo v7 pasó **226/226 escenarios**. La suite Python pasó **309 pruebas, 2 omitidas**. El escáner de texto público y la comprobación offline del esquema pasaron.

La reconstrucción sin claves usó `docker compose -f docker-compose.yml -f %TEMP%/t8c-keyless-compose.yml up -d --build backend`, con un override que vacía claves y modelos y desactiva tracing. `/ready` devolvió **HTTP 200**, 68 filas y 16 términos. Dentro del contenedor, las claves de OpenRouter y LangSmith estaban ausentes y tracing estaba desactivado. Se conservó el volumen PostgreSQL.

| Corte | Commit | Comprobación principal |
|---|---|---|
| Página agotada y único modelo | `a4e7d31` | No se indexa una lista vacía; se ofrece relajar un requisito. |
| Referencias a modelos mostrados y comparados | `8e7eb0a` | Campos planos del tool y resolución por contexto. |
| Límites de torque y suministro | `741417a` | Sólo se muestra torque que satisface ambos límites; DC admite AC/DC. |
| Intención de elegir o explicar | `66e35c7` | Señal plana `intent`; elección en código. |
| Lenguaje coloquial y equivalentes | `d0bda81` | Pruebas de flujo preciso, errores tipográficos, sitio petroquímico, 220 V y enclosure equivalente. |
| Preguntas fuera del catálogo | `8915acc` | Una limitación y una oferta; no se vuelca una ficha completa. |
| Comparaciones | `07eb315` | Campos completos, filas idénticas ocultas, respuesta directa para corriente y LRA. |
| Respuestas breves y singular | `be5a15e` | `thanks`, `go`, códigos parciales y `1 actuator meets`. |
| Métrica LRA | `71acf33` | Valores en amperios a la frecuencia indicada y orden por LRA. |
| Cohorte v2 y escáner | `42986a8` | 51 conversaciones nuevas en v7; frases obsoletas vetadas. |
| Filas N/A | `d2d36f0` | Recuento SQL de filas N/A excluidas de superlativos amplios. |
| Descripción de tool dentro del presupuesto | `d25783c` | Se mantuvo la instrucción explícita para límites numéricos. |
| Referencia breve y entrega | `b4a10f5` | `the faster one` y `its power?` usan el conjunto comparado; la consulta de entrega no duplica el aviso. |

## Esquema del proveedor

Antes de T8c (T8b): 6 arrays, 4360 bytes, profundidad 7, 83 valores de enum, 2 campos requeridos. Después: **6 arrays, 5487 bytes, profundidad 7, 107 valores de enum, 2 requeridos**. Cero uniones/referencias prohibidas, cero rangos numéricos y cero arrays de objetos en lookup. El máximo offline de enums es 108 y el de bytes es 5522.

## Respuestas guionizadas capturadas

El JSON completo de las ejecuciones seleccionadas está en [T8c-scenarios.json](T8c-scenarios.json). Estas son respuestas producidas contra PostgreSQL por el modelo guionizado, no una nueva medición de Gemini en vivo:

| Caso | Respuesta observada |
|---|---|
| Q1-03, corriente a 60 Hz | `763B00-11300000/A is more current at 60 Hz: 4.8 A vs 2.3 A.` (lead) |
| Q3-04, `others?` después de un único resultado | `That's the only model that meets these requirements. Relax one requirement to see alternatives.` |
| Q4-03, versión 220 V | `Published voltage equivalents for 761B00-11300000/A: 761B00-11320000/A.` |
| C-FRUSTRATION-01 | La respuesta comienza `My pick:` y la siguiente explica el criterio. |
| C-SHORTREF-02 | La referencia al modelo más rápido se resuelve contra los dos modelos comparados. |
| Q6-01, tiempo de entrega | `The catalogue does not publish delivery times. I can show the published model specifications.` |

## Límite de la evidencia

Este resultado valida código, SQL local, contrato y replay guionizado. No es una nueva cohorte de inferencia Gemini; la comprensión del proveedor de frases nuevas sigue pendiente de una prueba en vivo autorizada. La comparación con tres modelos ahora oculta filas iguales y calcula el ganador para métricas publicadas; si faltan valores comparables, declara esa ausencia.
