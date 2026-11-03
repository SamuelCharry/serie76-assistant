# Comparación real de modelos Serie 76

**Recomendación: Gemini 3.6 Flash como candidato para el assessment.** Empató en puntuación estricta con Flash Preview; la elección es un juicio técnico sobre la gravedad de los errores, no una superioridad estadística.

## Resultados

| Modelo | Casos correctos / evaluados | Mediana exitosa | Errores503 / intentos | Tokens: costo estimado de respuestas |
|---|---:|---:|---:|---:|
| gemini-3.6-flash | 17/18 | 2.747 s | 6/24 | USD 0.03409 |
| gemini-3-flash-preview | 17/18 | 1.241 s | 2/20 | USD 0.01667 |
| gemini-3.5-flash-lite | 16/18 | 1.695 s | 0/18 | USD 0.01458 |
| gemini-3.8-flash | Sin respuestas; no puntuable | — | 2/2 | USD 0.00000 |
| gemini-3.1-flash-lite | Sin respuestas; no puntuable | — | 2/2 | USD 0.00000 |

Las tarifas Google directas coinciden en esta fecha con las estimaciones de esos endpoints estándar Google AI Studio en OpenRouter; eso no constituye una llamada ni factura OpenRouter. Los errores de transporte no se anotaron como precisión cero. El resultado mantiene17/18 original para3.6; no se cambiaron reglas después de ver sus errores.

## Por qué elegiría3.6 frente al empate

- **3.6 Flash:** código y N/A correctos; omitió focus=motor_power en una petición adversarial y tomó overview. No inventó los999W solicitados. Faltó el aviso específico sobre potencia del motor frente a consumo total. Es un fallo de enfoque/presentación.
- **3 Flash Preview:** añadió frequency_hz=60 sin autorización. Hoy devuelve las mismas siete referencias, pero guarda ese filtro en el contexto. En un seguimiento con máximo30s, el filtro supuesto devuelve tres referencias donde correspondía pedir frecuencia. Es una suposición técnica injustificada.
- **3.5 Flash-Lite:** pidió repetir un código completo inexistente en vez de consultar su ausencia y confundió840arranques/h con ciclos/h. El esquema rechazó esta última consulta; el rechazo protege datos, pero no significa que el modelo entendiera el requisito.

El desempate mecánico original por costo/latencia favorece **gemini-3-flash-preview**. La recomendación ingenieril prioriza no alterar condiciones técnicas. Esa preferencia cualitativa está separada de las puntuaciones y de los costos.3.6 sufrió seis503; no se oculta esta desventaja operacional ni se extrapola al proveedor de despliegue.

## Gasto y acceso

66 intentos después de la recarga, 54 generaciones exitosas y 12 errores de proveedor. Antes de la recarga hubo tres402 y un probe404 de un modelo retirado para usuarios nuevos; esos accesos no produjeron respuestas ni puntajes.

Costo calculado con tokens reportados: **USD 0.06533735**. Reserva íntegra refinada para errores sin usage: **USD 0.15612200**. Total conservador del cliente: **USD 0.22145935**, bajo el tope compartido **USD0,50**. No se consultó saldo/factura ni se hizo conversión COP/USD. No hubo inferencias OpenRouter.

Las reservas se refinaron con el payload exacto congelado, medido sin red, más4096tokens de sobrecarga y máximo2048tokens de salida/thinking. Los JSONL históricos permanecen intactos; los sidecars muestran el hash/bytes y la reserva original y refinada. Esos mocks no se incorporan a resultados de modelos. No hay grounding ni caché explícita con cargos adicionales.

## Evidencia y reproducción

- [Resultado completo](comparison.json), [cohorte inicial pagada](google-comparison-v2/summary.json), [alternativas](google-additional/summary.json), [presupuesto conjunto](continuation.json).
- [Metodología y comandos](../../docs/MODEL_EVALUATION.md). Casos en model_eval/cases.py; JSONL completos por cohorte conservan intentos, llamadas y resultados reales de PostgreSQL.
- Protocolo y corpus idénticos entre cohortes, misma versión SQL. Modelos no disponibles no entran en ranking de calidad. Dependencias congeladas en requirements-model-eval.lock.txt.
- Investigación de precios/capacidades, construcción de casos y revisión de fallos se repartieron entre tres agentes. Solo el controlador hizo inferencias. La revisión independiente confirmó las diferencias sin inferencias adicionales.

## Antes de producción

Modelo propuesto OpenRouter: **google/gemini-3.6-flash**. La prueba actual fue con API nativa Google, thinking low, máximo2048tokens y muestreo predeterminado. El cliente de producción usa ahora otra configuración: temperatura0 y máximo600. Hay que alinearla y validar un pequeño conjunto por OpenRouter antes de declarar la integración verificada. No se modificó ese cliente concurrente ni se gastó su clave.

El renderer todavía redacta en inglés y muestra Nm en el texto de torque mientras in-lb permanece en las tarjetas. Son aspectos del código, no diferencias de calidad lingüística entre modelos. Este corpus fijo de18casos no demuestra robustez universal; conviene añadir casos no utilizados para afinar el prompt al integrar el proveedor final.

Fuentes: [precios Google](https://aistudio.google.com/docs/pricing), [cuotas](https://aistudio.google.com/docs/rate-limits), [errores](https://aistudio.google.com/docs/api-errors), [deprecaciones](https://aistudio.google.com/docs/deprecations), [endpoint3.6 OpenRouter](https://openrouter.ai/api/v1/models/google/gemini-3.6-flash/endpoints), [endpointPreview](https://openrouter.ai/api/v1/models/google/gemini-3-flash-preview/endpoints).
