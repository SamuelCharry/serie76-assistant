# Resultados de arquitecturas

**Conclusión: comparación inconclusa; no se promovió ninguna arquitectura.**

Las cinco configuraciones están implementadas y se hicieron llamadas reales en Google. Los errores de esquema cuentan como fallos de calidad. Los fallos del proveedor se separan. Los archivos originales del runner permanecen intactos.

| Variante | Intentados | Disponibles sin error proveedor | Éxitos disponibles¹ | Fallos proveedor | Fallos esquema/protocolo | Éxitos emparejados |
|---|---:|---:|---:|---:|---:|---:|
| A | 11 | 8 | 5 | 3 | 0 | 1/1 |
| B | 11 | 8 | 6 | 3 | 1 | 1/1 |
| C | 11 | 7 | 5 | 4 | 1 | 1/1 |
| D | 11 | 6 | 5 | 4 | 0 | 1/1 |
| E | 10 | 5 | 5 | 5 | 0 | 1/1 |

¹ Las columnas disponibles tienen conjuntos diferentes y no sirven para ordenar las variantes. La comparación válida usa los escenarios emparejados.

A: actual; B: agente único contextual; C: dos especialistas; D: supervisor; E: proponente/revisor.

Escenarios comunes: 1/24. IDs: trap_units.
Controlador: **USD 0.48392565 / 0.50**. Tokens con uso conocido: USD 0.16573125; reservas de uso desconocido: USD 0.31819440. No es una factura.
Llamadas: 103; fallos de proveedor: 19. Deriva de entradas congeladas: [].

## Observaciones verificables
- A / context_fla: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.
- A / conflict_dc: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.
- B / conflict_dc: ValidationError, contado como fallo de calidad y no como indisponibilidad de Google.
- C / conflict_dc: ValidationError, contado como fallo de calidad y no como indisponibilidad de Google.
- D / exact_unknown: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.
- A / context_duty: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.
- B / context_duty: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.
- C / context_duty: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.

## Límites y siguiente decisión

Recuperar contexto permite contestar definiciones que A no tiene cómo recuperar. Eso no demuestra que añadir agentes supere B. Los 503 y la reserva conservadora consumen el presupuesto antes de completar el diseño. No se repiten casos fallidos ni se cambian prompts para inflar la puntuación.

Los costos observados incluyen reutilización compartida de embeddings; no representan costos unitarios independientes. Las latencias incluyen pausas del controlador. No deben usarse para afirmar escalabilidad ni para promover una variante. Antes de una comparación definitiva hay que contabilizar embeddings por invocación y separar latencia de servicio del pacing.

**Defecto del renderizador contextual:** el filtro genérico de dígitos elimina la oración que define Duty Cycle porque contiene el identificador S4. En context_duty, B/C recuperaron la página correcta pero mostraron otros términos. Es un fallo compartido de preparación/presentación de evidencia, no una prueba contra los embeddings ni contra el modelo. El extractor también conserva un carácter de sustitución en algunas viñetas. Antes de integrar hay que distinguir identificadores de magnitudes, segmentar definiciones individualmente y validar que la respuesta conserva el término solicitado; verificarlo en una cohorte nueva, sin retocar estas puntuaciones.

Las definiciones son extractos citados, con oraciones numéricas omitidas; no se evaluó una redacción libre en español. El revisor usa el mismo modelo y puede compartir sesgos. Algunas decisiones intermedias solo guardan metadatos de uso, no el argumento completo: ampliar esas trazas requiere una cohorte nueva, sin alterar esta.

Sigue pendiente la validación final por OpenRouter. No cambiar el chat operativo con esta evidencia. Protocolo: ../../docs/ARCHITECTURE_EVALUATION.md.
