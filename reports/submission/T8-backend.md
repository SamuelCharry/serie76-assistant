# T8 backend · verificación local

Estado: implementado y verificado con decisiones de modelo **scripted**, PostgreSQL real y HTTP local. No hubo inferencia pagada ni llamadas a OpenRouter/Google. La interpretación con un proveedor real y la prueba en emulador siguen pendientes; el selfcheck no las sustituye.

## Slices y commits

1. Texto público y scanner: `5a08466`, `104700f`. Quité la nota interna de supuestos, normalicé labels y el rechazo de términos ausentes; el scanner cubre respuestas, preguntas, tarjetas, recomendaciones y sugerencias.
2. Preguntas y Submit: `f9726f5`. Las preguntas distinguibles llegan juntas, con conteos SQL y orden por reducción de candidatos. Un conjunto de respuestas sin coincidencias produce `422 empty_combination` sin guardar turno.
3. Recomendaciones y acciones: `e58e1a2`, `370171a`. Ranking determinista, provisional para más de diez resultados, top tres para uno a diez, y modelos cercanos para cero. `compare_top`, `show_all` y `rank_by` usan la lista persistida en contexto sin modelo.
4. Referencias: `80db6a3`. Una decisión `get_actuator` puede señalar posiciones de la lista anterior o pedir su enumeración; el servidor resuelve códigos, sin una segunda decisión.
5. Ruta rápida y latencia: `0638c33`. Comparación o consulta cerrada de uno a cuatro códigos completos y existentes se resuelve en código. `debug` guarda latencia, intentos y `llm_called`; migración aditiva `006_t8_interactions.sql`.
6. Tarjetas: `7e1a2ef`. Cuatro campos como máximo, con filtros antes de los valores más distintos; se entrega `key_fields_reason`.
7. Sesiones: `4dfc361`. `DELETE /api/sessions/{id}` borra lógicamente por propietario; lista, mensajes y POST posterior ocultan la sesión.
8. Glosario: `8a76f23`. Contextos coloquiales de sitio peligroso, gas, minería y exterior piden confirmar un cerramiento con la descripción del glosario. Un término ausente recibe una negativa genérica sin sugerencias ni rating en el texto.
9. Nombres demo: `f1a26c5`. Los dos correos de prueba reciben `Demo Engineer` y `Review Engineer` de forma idempotente; IDs y hashes permanecen iguales.
10. Cierre y suite v7: `6ae4d82`, `4bcb37b`. Se conservan preguntas pendientes al enumerar o comparar resultados, se respeta la unidad de torque pedida, y se agregan las 103 situaciones v6 más 12 v7. Los archivos v6 no se editaron.

## Pruebas

- Suite Python completa con `SERIES76_TEST_DB=1`: **239 pruebas, OK, 2 omitidas** por módulos OCR/geometría opcionales.
- `agent_acceptance.py selfcheck` v7: **115/115 escenarios**, sin inferencia externa. Incluye frases originales, ruta rápida, acciones, cero resultados y mutaciones del scanner.
- Corrupciones v6: **6/6**. Scanner unitario: **3/3**; también corre sobre cada respuesta del selfcheck y de los escenarios scripted.
- `check_tool_schemas.py` offline: antes `arrays=6, bytes=4131, depth=7, enum_values=83, required=3, forbidden_nodes=0, numeric_ranges=0`; después `arrays=6, bytes=4360, depth=7, enum_values=83, required=2, forbidden_nodes=0, numeric_ranges=0`. No hay arrays de objetos en `get_actuator`.
- El selfcheck **v6** conserva expectativas de presentación T7 y no es una puerta verde para T8: en una ejecución intermedia fallaron 19/103 escenarios por preguntas, sugerencias y texto que cambiaron. El selfcheck v7 adapta esas expectativas sin alterar v6; conserva las verificaciones de SQL, unidades y valores. Las seis pruebas de corrupción v6 siguen verdes.

La reconstrucción final usó `docker compose -f docker-compose.yml -f %TEMP%/t8-keyless-compose.yml up -d --build backend`. El override temporal fija vacías las claves y nombres de modelo y desactiva tracing; no se inspeccionaron valores. El primer intento sin override dejó una clave de tracing presente aunque tracing estaba apagado; se corrigió antes de la verificación final. `/ready` respondió **HTTP 200**, con **68 filas** y **16 términos**. La comprobación final dentro del contenedor devolvió `false` para presencia de claves OpenRouter, Google y LangSmith, modelo/fallback y tracing. El volumen PostgreSQL se preservó.

## Tres respuestas JSON capturadas

Los tres cuerpos HTTP **completos y sin modificar** están en [T8-three-responses.json](T8-three-responses.json). [T8-scenarios.json](T8-scenarios.json) conserva las decisiones scripted, trazas, verdictos y respuestas de origen. Aquí se muestran campos seleccionados literalmente de esos cuerpos.

### Preguntas simultáneas

```json
{
  "answer": "59 actuators meet: On/Off service, torque ≥ 70 Nm. To narrow it down: supply voltage and enclosure.\nRanked by closest torque at or above 70 Nm, then lowest FLA.\n761X30-11380000/A: 70 Nm torque; FLA 5 A\n761X30-11320000/A: 80 Nm torque; FLA 0.6 A\n761A00-11320000/A: 80 Nm torque; FLA 0.7 A",
  "interaction": {"kind": "question", "questions": [
    {"id": "supply_voltage_v", "prompt": "Which supply voltage?", "options": [{"value": "24", "label": "24 V", "count": 5}, {"value": "110", "label": "110 V", "count": 21}, {"value": "220", "label": "220 V", "count": 33}]},
    {"id": "enclosure", "prompt": "Which enclosure?", "options": [{"value": "explosionproof", "label": "Explosionproof", "count": 25}, {"value": "weatherproof", "label": "Weatherproof", "count": 34}]}
  ]},
  "recommendation": {"ranked_by": "closest torque at or above 70 Nm, then lowest FLA", "total": 59, "shown": 3},
  "debug": {"latency_ms": 261, "attempts": 1, "llm_called": true}
}
```

### Submit de 110 V y Explosionproof

```json
{
  "answer": "10 actuators meet: Explosionproof, On/Off service, 110 V, torque ≥ 70 Nm. Here are the leading published models.\nRanked by closest torque at or above 70 Nm, then lowest FLA.\n761X30-11300000/A: 80 Nm torque; FLA 1.1 A\n761Y30-11300000/A: 100 Nm torque; FLA 1.1 A\n762X30-11300000/A: 150 Nm torque; FLA 1.9 A",
  "recommendation": {"ranked_by": "closest torque at or above 70 Nm, then lowest FLA", "total": 10, "shown": 3, "items": [
    {"part_number": "761X30-11300000/A", "reason": "80 Nm torque; FLA 1.1 A", "key_values": [{"label": "On/Off torque", "value": "80 Nm"}, {"label": "FLA", "value": "1.1 A"}]},
    {"part_number": "761Y30-11300000/A", "reason": "100 Nm torque; FLA 1.1 A", "key_values": [{"label": "On/Off torque", "value": "100 Nm"}, {"label": "FLA", "value": "1.1 A"}]},
    {"part_number": "762X30-11300000/A", "reason": "150 Nm torque; FLA 1.9 A", "key_values": [{"label": "On/Off torque", "value": "150 Nm"}, {"label": "FLA", "value": "1.9 A"}]}
  ]},
  "suggested_replies": ["Compare top 2", "Show all 10"],
  "debug": {"latency_ms": 78, "attempts": 0, "llm_called": false}
}
```

### Comparación por ruta rápida

```json
{
  "answer": "Comparing 761A00-11300000/A vs 761B00-11300000/A. 10 identical fields hidden.\nOn/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm\nModulating torque: 580 in-lb / 65 Nm vs 620 in-lb / 70 Nm\nOn/Off cycles: 36 /h vs 31 /h\nOperating time at 50 Hz: 20 s vs 23 s\nFLA at 50 Hz: 1.1 A vs 1.2 A\nOperating time at 60 Hz: 17 s vs 19 s\nFLA at 60 Hz: 1.2 A vs 1.3 A",
  "comparison": {"layout": "table", "models": ["761A00-11300000/A", "761B00-11300000/A"], "summary": "761A00-11300000/A wins 5 of 7 differing fields with an agreed direction; 761B00-11300000/A wins 2. This is an unweighted field count, not an overall suitability rating."},
  "debug": {"latency_ms": 61, "attempts": 0, "llm_called": false}
}
```

La latencia de estos tres turnos corresponde a pruebas locales con decisiones scripted; no mide el proveedor real ni el emulador.

## Revisión de naturalidad

La selección de preguntas ahora compara los conjuntos de códigos obtenidos de SQL: omite una pregunta cuando sus opciones no separan candidatos adicionales y omite campos con una sola alternativa que cubre todos los resultados. La primera interacción de 59 candidatos pide voltaje y gabinete; la partición AC/AC-DC ya queda determinada por el voltaje. Servicio y frecuencia conservan su pregunta cuando definen cómo interpretar los datos técnicos, aunque las filas coincidan.

El texto de respuesta resume los temas pendientes en una oración y el criterio de ordenamiento usa minúscula después de «Ranked by» en la respuesta, el encabezado y `recommendation.ranked_by`. Las dos correcciones tuvieron pruebas que fallaron antes de la implementación. Verificación final: 239 pruebas Python aprobadas (2 omitidas), selfcheck v7 115/115, scanner 3/3 y esquema offline sin nodos prohibidos ni rangos numéricos.
