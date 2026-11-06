# T8b · Corrección de comportamiento del backend

La evidencia de entrada fue `dump_v1.txt` y `out_v1/results.json`: 60 conversaciones, 113 turnos HTTP con Gemini. La latencia observada en esa corrida fue p95 de 4,2 s; la ejecución local de este informe fue guionada y no hizo inferencia de pago. El fixture derivado guarda consultas y decisiones ideales, sin sesiones ni respuestas de la corrida en vivo. Reproduce los 113 turnos y añade aserciones específicas a los seis fallos pedidos; su aprobación no demuestra que Gemini tome esas decisiones en una nueva corrida.

## Cortes y commits

| Corte | Commit | Resultado |
| --- | --- | --- |
| R1: torque y comparación | `8f32c4f` | Torque calificador por servicio y tiempo/frecuencia usados para ordenar; filas iguales ocultas. |
| R2: respuesta a opciones | `3627a6b` | Texto completo y unívoco a una pregunta pendiente se aplica en código. |
| R3: lenguaje coloquial | `d5e87bd` | Mapa cerrado de servicio, voltaje, kNm y español; gabinete con etiqueta breve y descripción. |
| R4: elección y motivo | `448afe4` | Una elección de la lista o comparación y explicación breve del criterio. |
| R5: referencias y páginas | `d4d4bd2` | Referencias de lista y páginas de tres; salida concisa para una pregunta no contestada. |
| R6: límites del documento | `3a9f4ce` | Respuestas breves para precio, calificaciones, otras marcas y notas de asterisco. |
| R7: vaguedad y superlativos | `05ebfd0` | Hasta dos preguntas útiles para una solicitud vacía; superlativos directos. |
| R8: texto y orden | `37e4eb4`, `3bd6a4d` | Desempates sin repetición, encabezados, comparación, acciones para pocos resultados y expectativas antiguas revisadas. |
| Cohorte v7 | `de622c0` | Guardas para código/etiqueta, inyección, secretos, solicitud vaga, términos compuestos y cancelación. |
| R9: 60 conversaciones | `4fe288d` | Fixture de 113 turnos, aserciones dirigidas, scanner extendido y oráculo de comparación actualizado para el marcador de dato ausente. |
| Revisión de la elección repetida | `64e463a` | Conserva las opciones abiertas y elimina una frase de supuesto redundante. |

## Verificación

| Puerta | Resultado |
| --- | --- |
| Suite Python con `SERIES76_TEST_DB=1` | 271 pruebas aprobadas, 2 omitidas. |
| Selfcheck v7 | 175/175 escenarios; incluye 60 conversaciones y 113 turnos del fixture retenido. |
| Scanner de texto público | 3/3 pruebas; también se aplica a las respuestas guionadas. |
| Esquema offline, antes → después | `arrays 6 → 6`, `bytes 4360 → 4360`, `depth 7 → 7`, `enum_values 83 → 83`, `forbidden_nodes 0 → 0`, `numeric_ranges 0 → 0`, `required 2 → 2`. |
| Backend reconstruido sin claves | `docker compose up -d --build backend` con override vacío; `/ready` HTTP 200, 68 filas y 16 términos. Se comprobaron como ausentes las claves/modelos de inferencia y la traza remota. |

La opción `interaction.questions[].options[].description` es aditiva; la etiqueta queda corta y la definición del glosario va en la descripción. Los cambios de expectativas de T7 corresponden a paginación de tres, acciones para uno a tres resultados, texto de límite de compra y precio, y etiquetas de gabinete breves. Las configuraciones v6 no se editaron.

## Fallos de la cohorte v7

| Caso | Causa en la corrida | Corrección o expectativa justificada |
| --- | --- | --- |
| EC05 | Decisión LLM: aclaración genérica ante dos códigos exactos. | Guarda por código/etiqueta/factura: compara ambos y pide comprobar la placa física. |
| EC31 | Decisión LLM: `unsupported` ante una instrucción que falsificaba 999 W. | Guarda de consulta de potencia con código completo: muestra los 15 W publicados. |
| EC21 | El contrato anterior aceptaba una tarjeta genérica para “Pick one” sin datos. | Sin lista ni requisitos, una frase pide función, voltaje y torque; se añadió esta expectativa natural. |
| EC34 | Decisión LLM: `decline` genérico ante una solicitud de secretos. | Guarda de rechazo explícito. La expectativa acepta los campos `unsupported` o `decline` solo si el texto rechaza la divulgación. |
| EC40 | Decisión LLM: comparación, pero omitió definiciones pedidas. | El lookup incorpora FLA, LRA y S4 expresamente pedidos y declara que el término ajeno no está definido. |
| t6_manual_07 | El LLM omitió `cancel_previous`, aunque el texto empezaba con “cancel that”. | El código fija el indicador y borra el contexto. La expectativa dejó de exigir el argumento crudo del LLM y sigue comprobando la cancelación real. |

EC30 y EC35 también actualizaron expectativas por redacción: el catálogo no publica precios ni calcula una ponderación con precio, y la limitación de compra ya no usa la frase prohibida. La validez de las correcciones frente a Gemini y un emulador queda pendiente de una nueva corrida autorizada.

## Respuestas guionadas solicitadas

Las respuestas completas y trazas locales están en [T8b-scenarios.json](T8b-scenarios.json). Las siguientes respuestas se copiaron de ese selfcheck, no de la corrida de pago.

### P5-01

Consulta: necesito un actuador on/of para 220v con almenos 100 nm

```text
30 actuators meet: On/Off service, 220 V, torque ≥ 100 Nm. To narrow it down: enclosure and number of phases.
Ranked by closest torque at or above 100 Nm, then lowest FLA.
761B00-11320000/A: On/Off torque 100 Nm; FLA 0.7 A
762X30-11320000/A: On/Off torque 150 Nm; FLA 0.9 A
762A00-11320000/A: On/Off torque 150 Nm; FLA 1 A
```


### P2-03

Consulta: we have a refinery with flammable gas, need a valve motor

```text
Which published enclosure matches your site? Explosionproof: Built with a more robust enclosure to be safely operated in hazardous environments where flammable gases or dust may be present (compliant with CSA, IECEx/ATEX standards). Weatherproof: Designed for general industrial use, protected against dust, rain, and environmental elements (compliant with CSA, CE, & UKCA standards).
Ranked by lowest FLA, then shortest operating time.
761X30-11320000/A: On/Off torque 80 Nm; Modulating torque 65 Nm; FLA 0.6 A
761Y30-11320000/A: On/Off torque 90 Nm; Modulating torque 72 Nm; FLA 0.6 A
762X30-11320000/A: On/Off torque 150 Nm; Modulating torque 130 Nm; FLA 0.9 A
```


### B-FRUSTRATION-01

Consulta: this doesn't help

```text
My pick: 761X30-11380000/A — On/Off torque 70 Nm; FLA 5 A. Assumes no preference on supply voltage, enclosure; tell me if that matters.
```

Consulta: just tell me which one to buy

```text
My pick: 761X30-11380000/A — On/Off torque 70 Nm; FLA 5 A. Assumes no preference on supply voltage, enclosure; tell me if that matters.
```


### B-SHORTREF-01

Consulta: that one

```text
763A00-11330C00/A
  • Torque: 2650 in-lb / 300 Nm (published once for On/Off and Modulating)
  • Duty S4 On/Off and Modulating (shared): 70%
  • On/Off cycles per hour: 39
  • Modulating starts per hour: 1200
  • Operating time at 50 Hz: 32 s
  • Operating time at 60 Hz: 26 s
  • FLA at 50 Hz: 1 A
  • FLA at 60 Hz: 1 A
  • LRA at 50 Hz: 1.2 A
  • LRA at 60 Hz: 1.2 A
  • Motor power: 40 W
  Source: Series 76 electrical catalogue, page 2.
```

Consulta: the other one

```text
763A00-11320000/A
  • On/Off torque: 2650 in-lb / 300 Nm
  • Modulating torque: 1950 in-lb / 220 Nm
  • Duty S4 On/Off: 40%
  • Duty S4 Modulating: 40%
  • On/Off cycles per hour: 24
  • Modulating starts per hour: 960
  • Operating time at 50 Hz: 29 s
  • Operating time at 60 Hz: 24 s
  • FLA at 50 Hz: 1.3 A
  • FLA at 60 Hz: 1.3 A
  • LRA at 50 Hz: 1.5 A
  • LRA at 60 Hz: 1.4 A
  • Motor power: 40 W
  Source: Series 76 electrical catalogue, page 1.
```


### P6-01

Consulta: how much does 761A00-11300000/A cost?

```text
The catalogue doesn't publish prices. A weighted price score is unavailable; I can compare published motor power or torque as a proxy only.
```


### P1-03

Consulta: 764A00-11300000/A vs 765A00-11300000/A — which is faster at 60 Hz?

```text
Comparing 764A00-11300000/A vs 765A00-11300000/A. 9 identical fields hidden.
On/Off torque: 6650 in-lb / 750 Nm vs 17700 in-lb / 2000 Nm
Modulating torque: 6020 in-lb / 680 Nm vs 15000 in-lb / 1700 Nm
On/Off cycles: 12 /h vs 4 /h
Operating time at 50 Hz: 36 s vs 106 s
FLA at 50 Hz: 6.5 A vs 6.8 A
Operating time at 60 Hz: 30 s vs 88 s
FLA at 60 Hz: 6.5 A vs 6.8 A
LRA at 60 Hz: 7.3 A vs 7.4 A
```

Lead: 764A00-11300000/A is faster at 60 Hz: 30 s vs 88 s.
