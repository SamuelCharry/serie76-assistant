# T8d backend: tercer conjunto retenido

## Resultado comprobado

El archivo crudo v3 contiene **45 conversaciones y 81 turnos** (el encargo decía 46). Se añadieron todas al replay guionizado v7. La suite Python terminó con **341 pruebas correctas y 2 omitidas**; v7 selfcheck pasó **271/271 escenarios**. El escáner de texto público pasó y el esquema offline conserva **107 valores de enum**, uno por debajo del límite de 108. No hubo inferencia ni llamadas pagadas en este trabajo.

El backend se reconstruyó con el override keyless; después de iniciar, `/ready` devolvió **HTTP 200** y el contenedor confirmó `keyless=True`. Se conservó el volumen de PostgreSQL.

| Corte | Commit | Cambio y prueba |
|---|---|---|
| Atributos fuera del catálogo | `61ecc53` | Una limitación y una oferta; pruebas de peso, cableado y señal. |
| Métricas del conjunto actual | `f0de8d2` | Ganador por duty, ciclos, corriente, velocidad, potencia y torque; pruebas sobre listas y comparaciones. |
| Foco después de elegir | `fc586c9` | El modelo elegido queda en contexto; consultas eléctricas resuelven ese modelo. |
| Requisitos explícitos | `d569e43` | Fases, servicio, exterior y peligro se normalizan en cada búsqueda. |
| Cero coincidencias categóricas | `26bca48` | El conflicto y sus dos relajaciones salen de consultas SQL. |
| Equivalentes | `55c5bef` | Voltaje y enclosure buscan el equivalente más cercano y actúan si es único. |
| Lista y redacción | `bd57a09` | Top 3 una sola vez y elecciones abiertas en frase natural. |
| Preguntas inútiles | `0bd3817` | Se omiten opciones que retienen todos los candidatos. |
| Campo solicitado | `355df15` | Una pregunta de un campo devuelve ese campo, sin ficha completa. |
| Calificadores no disponibles | `ae8fb59` | Interior, silencio y tamaño compacto quedan declarados como no comprobables. |
| Alcance de medidas | `4d3ce00` | Torque calificante, frecuencia de corriente y torque compartido se etiquetan. |
| Bandas de torque | `cc1e3c0` | Opciones y recuentos basados en SQL; pruebas de selección y envío. |
| Cohorte v3 | `ff70ac4` | 45 conversaciones añadidas a v7 y frases obsoletas al escáner. |
| Empates de métricas | `1eb5fa1` | Veredicto plural probado para varios ganadores. |

## Esquema

Antes de T8d: 6 arrays, 5487 bytes, profundidad 7, **107 enum values**, 2 requeridos. Después: los mismos valores. Hay cero nodos prohibidos, cero rangos numéricos y cero arrays de objetos en lookup. No se añadió ningún campo al esquema del proveedor.

## Respuestas guionizadas

El JSON completo está en [T8d-scenarios.json](T8d-scenarios.json). Son respuestas del código con decisiones guionizadas y PostgreSQL local, no una nueva medición de Gemini.

| Caso | Respuesta observada |
|---|---|
| R6-01, peso | `The catalogue doesn't publish weight for 763A00-11320000/A. I can show its published specifications.` |
| R1-03, ciclos | Lead: `761Y30-11300000/A has the highest On/Off cycles: 190 cycles/h vs 100 cycles/h.` |
| D-IMPOSSIBLE-01, 24 V Weatherproof | `No actuator meets Weatherproof, 24 V. 24 V models are only Explosionproof under the other requirements in this catalogue. Weatherproof models are available at 110/220 V under the other requirements.` |
| D-TOPICJUMP-01, duty | La consulta sobre el conjunto mostrado devuelve los modelos empatados con 70 % S4 sin una lista de 19 códigos. |

## Límite de la evidencia

La meta de ≥90 % en una nueva cohorte Gemini **no está verificada** aquí: estos controles son replay guionizado, pruebas locales y reconstrucción keyless. El resultado previo en vivo fue 21/45 según la revisión del coordinador; hace falta repetir la evaluación en vivo con autorización para medir el nuevo porcentaje.
