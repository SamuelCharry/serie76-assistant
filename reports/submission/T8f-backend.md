# T8f backend: quinta cohorte retenida

## Resultado verificado

La evidencia v5 contiene 44 conversaciones y 77 turnos. La medición en vivo anterior fue 21/44; esta entrega no repitió Gemini ni hizo llamadas pagadas. El replay guionizado v7 pasó **360/360 escenarios**, incluidos los 44 nuevos. La suite Python pasó **390 pruebas, 2 omitidas**. El escáner de texto público pasó 3/3 y el control offline del esquema pasó.

El backend se reconstruyó con el override keyless. `/ready` devolvió **HTTP 200** y el contenedor confirmó `keyless=True`. No se modificó el volumen PostgreSQL.

| Corte | Commit | Evidencia |
|---|---|---|
| Integridad y respuestas | `dc7e72e` | Pruebas fallidas primero para recuento filtrado, límite superior, peligro, cambios parciales, empates, diferencia LRA/FLA, campos concretos, equivalentes y plantillas; 19 pruebas T8f pasan. |
| Replay v5 | `130ed7d` | Se importaron las 44 conversaciones y 77 turnos al generador v7, con aserciones para los fallos principales. |
| Reporte y evidencia final | Este commit | Se registraron los resultados finales del replay, suite, esquema y backend. |

## Cambios y límites

- Las preguntas de recuento aplican los filtros expresados: **24 V → 10 modelos**, con cifra de SQL.
- `max torque 50 Nm` y los demás operadores superiores prevalecen sobre un parámetro inferior propuesto por el modelo. La respuesta indica que no hay modelo a 50 Nm o menos y que el menor torque publicado es **65 Nm**, consultado en SQL. La comprobación posterior de filtros sigue excluyendo cualquier fila que incumpla los límites.
- Señales de peligro como hidrógeno, disolventes, gases, polvo combustible y zonas clasificadas activan confirmación de enclosure y vista previa Explosionproof. Una respuesta afirmativa aplica Explosionproof; una negación inequívoca aplica Weatherproof. Una segunda comprobación impide mostrar una recomendación Weatherproof mientras persiste una señal de peligro.
- Una corrección parcial conserva servicio, voltaje y los otros filtros. Los empates nombran todos los códigos; duty sin servicio muestra los ganadores de On/Off y Modulating. La diferencia LRA/FLA se calcula con valores publicados a la misma frecuencia.
- Las preguntas de una o dos propiedades muestran esos campos; temperatura, instalación y ruido no producen fichas completas. “Cheapest” con torque mínimo consulta los modelos que cumplen el torque y ordena por potencia de motor, con una advertencia explícita de que el catálogo no publica precios.
- “The 3-phase version” y “the 110 V one” resuelven el código equivalente en SQL a partir del modelo enfocado; no crean un filtro artificial de igualdad de torque. La normalización de Modulating cubre posiciones intermedias y expresiones de regulación en inglés y español. La descripción del campo `service` se amplió sin añadir valores enum.
- Se retiraron las frases “was unclear in your request”, “Without supply voltage, enclosure, these are…” y “no frequency in source” de las respuestas.

## Controles

| Control | Resultado |
|---|---|
| Python: `SERIES76_TEST_DB=1 ... unittest discover -s tests` | 390 pruebas, OK, 2 omitidas |
| v7 selfcheck | 360 escenarios, 0 fallos |
| Escáner de texto público | 3 pruebas, OK; mutaciones de frases prohibidas rechazadas |
| `scripts/check_tool_schemas.py` | Antes y después: 6 arrays, 5487 bytes, profundidad 7, **107 enum values**, 2 requeridos, 0 nodos prohibidos, 0 rangos numéricos |
| Docker keyless y `/ready` | `keyless=True`, HTTP 200 |

El replay usa decisiones guionizadas y PostgreSQL local. No demuestra una nueva tasa de aprobación del proveedor en vivo; la cifra 21/44 es la medición previa. La evidencia offline quedó en [T8f-scenarios.json](T8f-scenarios.json).
