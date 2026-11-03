# Autoevaluación de la selección

Comparación medida y recomendación explícita, con ranking numérico separado del juicio de ingeniería.

| Eje | Nota | Evidencia y límite |
|---|---|---|
| Exactitud | 4 | Tres candidatos completaron los mismos 18 casos; trazas SQL y revisión independiente. Una muestra por caso no demuestra superioridad estadística. |
| Completitud | 4 | Investigación, corpus, ejecución, costos y análisis completados. Otros dos modelos no generaron respuestas por 503, por lo que no se declara una comparación universal. |
| Claridad | 4 | Empate 17/18 documentado sin elevar puntajes; explicación de enfoque frente a frecuencia inventada. Las cohortes/reanudaciones requieren seguir varios archivos enlazados. |
| Accionabilidad | 4 | Candidato y parámetros ensayados registrados, dependencias congeladas y CLI reproducible. El endpoint de producción OpenRouter no se ensayó y usa una configuración diferente. |
| Concisión | 4 | Resumen principal con tabla; detalle técnico separado. El control de reservas y continuidad añade complejidad, cubierta por pruebas. |

Media: 4.0/5. Sin problemas críticos pendientes para publicar este resultado medido. No se certifica el modelo de producción.

Mejoras siguientes por impacto: alinear y validar el cliente OpenRouter antes de activarlo; incorporar casos reservados antes de afinar prompts; comprobar estabilidad del proveedor final. No repetir los casos medidos para buscar retrospectivamente una nota mejor.

Auto-comprobación: el usuario puede auditar qué se midió y cuánto se estimó, y distinguir el candidato recomendado del ganador mecánico por costo. La diferencia de severidad de los errores justifica una preferencia técnica, no una afirmación estadística.
