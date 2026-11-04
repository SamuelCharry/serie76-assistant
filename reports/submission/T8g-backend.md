# T8g backend: sexta cohorte retenida

## Resultado comprobado

La evidencia v6 de Gemini 3.6 Flash contiene **43 conversaciones y 74 turnos**. La revisión en vivo anterior fue **28/43 (65 %)**; no se repitió el proveedor ni se hizo ninguna llamada pagada. Gemini 3.6 Flash sigue como modelo predeterminado. El replay guionizado v7 pasó **403/403 escenarios**. La suite Python pasó **407 pruebas, 2 omitidas**. El escáner de texto público y el control offline del esquema pasaron.

El backend se reconstruyó con el override keyless. `/ready` devolvió **HTTP 200** y el contenedor confirmó `keyless=True`; el volumen PostgreSQL permaneció intacto.

| Corte | Commit | Evidencia |
|---|---|---|
| Integridad y respuesta | `c07f89a` | Pruebas fallidas primero para peligro, precedencia de 110 V, servicio implícito, pregunta sobre válvula grande, diferencia FLA, rango de torque, referencias y corrección de código. |
| Replay v6 | `b40b351` | Las 43 conversaciones se añadieron a v7 con aserciones sobre los fallos principales. |
| Reporte | Este commit | Registra las verificaciones finales sin atribuirlas a una nueva prueba en vivo. |

## Cambios de integridad

- La detección de peligro cubre gases y vapores nombrados (propano, butano, LPG, gas natural, metano, hidrógeno, amoniaco y acetileno), polvo combustible y áreas clasificadas. Si el modelo propone Explosionproof al interpretar ese texto, el código lo acepta; si queda por confirmar, la vista previa sólo muestra Explosionproof. “Outside the hazardous zone” aplica Weatherproof en la respuesta a la pregunta pendiente.
- Un voltaje explícito en el turno prevalece sobre sinónimos como “battery”. “Battery room, 110 V” conserva **110 V** y no infiere alimentación DC. Las expresiones “open and shut/open/shut/open or close” y “partial positions/set to partial/mixing positions” fijan el servicio. `wp` y `xp` fijan el enclosure correspondiente.
- Una válvula “big/large” sin torque pide un mínimo mediante bandas con recuentos SQL; una respuesta vaga posterior no lista los modelos pequeños. La pregunta “what's closest?” tras un conflicto DC y 3 fases indica qué requisito habría que relajar.
- La diferencia FLA de dos modelos se calcula a la misma frecuencia con los dos valores SQL. Las preguntas comparativas sobre los modelos visibles dan un veredicto; cada código queda emparejado con su propio valor. La etiqueta de la recomendación sigue la métrica que decidió el veredicto. Los empates siguen nombrando todos los modelos.
- La pregunta de rango de torque de catálogo consulta mínimos y máximos por servicio en SQL. Una corrección de código conserva el campo enfocado. La vida útil no publicada recibe una limitación breve. En cero resultados, la recomendación se etiqueta expresamente como alternativas tras relajar un requisito. La elección evita repetir la suposición de torque abierto.

## Controles

| Control | Resultado |
|---|---|
| Python: `SERIES76_TEST_DB=1 ... unittest discover -s tests` | 407 pruebas, OK, 2 omitidas |
| v7 selfcheck | 403 escenarios, 0 fallos; 43 conversaciones v6 nuevas |
| Escáner de texto público | 3 pruebas, OK |
| `scripts/check_tool_schemas.py` | Antes y después: 6 arrays, 5487 bytes, profundidad 7, **107 enum values**, 2 requeridos, 0 nodos prohibidos, 0 rangos numéricos |
| Docker keyless y `/ready` | `keyless=True`, HTTP 200 |

El replay usa decisiones guionizadas y PostgreSQL local. No prueba que la tasa de aprobación en vivo haya subido de 28/43. La evidencia offline está en [T8g-scenarios.json](T8g-scenarios.json).
