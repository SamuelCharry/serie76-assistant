# ADR 0001: arquitectura del agente (A+)

- Estado: aceptada; actualizada el 2026-11-06.
- Decisión inicial: 2026-11-03. La aceptación y las correcciones posteriores están en el [informe pareado v17](../../reports/submission/P2-A.md).

## Contexto

El assessment exige LangChain, herramientas propias, PostgreSQL local, consultas por Base Part Number, recomendaciones y conversación persistente. El PDF eléctrico es la única autoridad numérica; el resumen suministrado aporta 16 definiciones. El presupuesto OpenRouter es USD 10.

La [comparación histórica A–E](../evidence/architecture_comparison.md) fue inconclusa: sólo un escenario común y 19 fallos de proveedor en 103 llamadas. No demuestra superioridad de una arquitectura. Elegir un agente es una decisión de ingeniería sobre coste, control y responsabilidades.

## Decisión

Un agente LangChain completa una decisión de herramienta por turno interpretado. Las rutas deterministas no llaman al modelo; los reintentos transitorios pueden realizar más de un intento de transporte. El chat usa `google/gemini-3.6-flash`, sin fallback; los embeddings usan `google/gemini-embedding-2`.

| Herramienta | Responsabilidad |
|---|---|
| `get_actuator` | Consultar códigos y datos publicados, con definiciones opcionales |
| `search_actuators` | Buscar y refinar requisitos técnicos validados |
| `explain_terms` | Consultar definiciones literales y procedencia del resumen |
| `ask_clarification` | Pedir el dato que falta o delimitar el alcance |

El código valida argumentos, conserva o reemplaza requisitos según la operación, resuelve referencias y consulta SQL parametrizado. Las plantillas presentan valores, unidades, N/A, notas y procedencia; el LLM no redacta cifras técnicas. La comprobación final de elegibilidad cubre tarjetas, comparaciones, ranking y referencias positivas, incluyendo pertenencia al conjunto mostrado cuando se pide. [Contrato del agente](../wiki/es/agent.md) · [Invariante SQL](../../reports/submission/P1-F.md).

El glosario se consulta completo, sin recuperación semántica de definiciones. pgvector se usa sólo para añadir ejemplos de interpretación y anclas: no sustituye requisitos explícitos ni valores SQL. Sus fallos omiten la ayuda semántica. La conversación y sus respuestas se guardan en PostgreSQL por propietario y sesión.

## Alternativas y costes

- **Glosario por recuperación:** innecesario para 16 definiciones; seleccionar sólo algunos fragmentos puede omitir contexto disponible. Se reconsideraría con un corpus mayor.
- **Varios agentes o un revisor LLM:** añaden llamadas, latencia y exposición al mismo proveedor; no reemplazan comprobaciones deterministas de cifras. El ensayo histórico no permitió medir una ventaja.
- **Prosa técnica generada:** ofrece más flexibilidad, pero pierde el control directo de cifras y unidades. Se prefieren plantillas, aunque resulten menos fluidas.
- **Estado completo generado por el modelo:** el experimento SV2 obtuvo 8/60 frente a 42/60 del sistema anterior y no fue adoptado. [Evidencia](../../reports/submission/SV2-experiment.md).

## Evidencia y límites

La mejora posterior fue adoptada por decisión del propietario como excepción a la regla preinscrita de no introducir regresiones. v17 obtuvo 47/46/50 de 60 conversaciones en tres ejecuciones, frente a 37/35/38; media 79,4 % frente a 61,1 %. La integridad adjudicada fue 429/438 frente a 410/438, con cero cifras incorrectas en 18.792 valores auditados de ambas versiones. El código reparado `1dda5f2` pasó 797 pruebas (dos omitidas), el oráculo 119/119 y los controles offline obligatorios. Esa reparación no cambia las puntuaciones pagadas de `3ede96c`; v17 pasó a regresión y no hay evaluación pagada independiente del código reparado. [Decisión, límites y pruebas](../../reports/submission/P2-A.md).

Todavía falla cerca del 20 % de las conversaciones inéditas. Un dato SQL correcto puede responder a una intención o referencia equivocada; la selección requiere comprobación del ingeniero. Las pruebas con decisiones simuladas validan código, no comprensión del modelo. No existe evidencia de escalabilidad a cien veces el tráfico; la cuota por proceso, concurrencia, conexiones y presupuesto requieren medición antes de escalar.

## Consecuencias

- Mantener catálogo y glosario versionados y trazables; `/ready` comprueba su disponibilidad, no el proveedor.
- Conservar trazas autorizadas por usuario para herramientas, argumentos y datos; el debug permanece oculto por defecto.
- Separar mediciones reales, pruebas offline y aceptación Android. Un build o una transcripción inyectada no verifican reconocimiento de voz.
- Mantener una suite determinista y auditoría de texto público junto con evaluación ciega de conversaciones inéditas; ninguna de ellas es una garantía universal.
