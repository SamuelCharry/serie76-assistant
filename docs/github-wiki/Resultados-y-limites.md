# Resultados y límites

Cada resultado corresponde a una versión y tipo de prueba. Una suite programada no mide comprensión del lenguaje; voz inyectada en emulador no mide reconocimiento real.

| Evidencia | Resultado | Alcance |
|---|---|---|
| OCR archivado | 941/941 controles primarios | Fidelidad al PDF evaluado; no generalización a nuevos diseños |
| v17: 60 conversaciones repetidas tres veces | 79,4 % mejorada frente a 61,1 % anterior | Mejora del candidato medido, con cerca de 20 % de fallos |
| v17: pasan las tres ejecuciones | 43/60 frente a 33/60 | Consistencia sobre los mismos casos; no 180 casos independientes |
| Auditoría estructurada v17 | 0 cifras erróneas en 18.792 valores, ambas versiones | Exactitud observada; no elección correcta universal |
| Integridad por turno v17 | 429/438 frente a 410/438 | Incluye respeto de requisitos y referencias |
| Latencia mejorada | p95 6,69 s; máximo 17,89 s; tres turnos >10 s | p95 dentro del umbral; no todos los turnos bajo 10 s |
| Fuente reparada, offline | 795 pruebas Python aprobadas, 2 omitidas; oráculo 119/119 | Regresiones cubiertas en ese alcance |
| Etiqueta final, T18 | 10/10 pasos; v7 453/453; 126 pruebas JVM y APK | Reproducción Windows sin inferencia pagada |
| Emulador, P2-D | 8/8 pruebas seleccionadas | HTTP real sin LLM y datos controlados para fallos/debug/voz |

## La distinción que no se debe omitir

El candidato medido es `3ede96c`. Se adoptó como **excepción autorizada** a la regla original de cero regresiones: esa regla no se cumplió. Dos regresiones nuevas y defectos compartidos se repararon en `1dda5f2`, incluido en la entrega. Las reparaciones pasaron controles offline, pero **no tienen nueva evaluación pagada independiente**. v17 pasó a ser material de regresión al usar sus fallos para reparar.

La comparación pareada reportó McNemar p=0,013 / 0,007 / 0,002. Son tres ejecuciones sobre los mismos 60 casos, no tres poblaciones independientes.

**Gasto registrado:** USD 6,170259916 de 10, incluidos intentos fallidos y experimentos. Es un registro cerrado, no saldo actual ni garantía de gasto futuro.

## Pendientes reales

Reconocimiento de voz y permisos reales; legibilidad física; cobertura manual de fallos de login/debug; medición de carga y futura evaluación independiente del código reparado. El catálogo no permite inventar precio, stock, dimensiones ni certificar una instalación.

[Evaluación y reparaciones](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-A.md) · [T18](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/T18-tag-clean-clone.md) · [Emulador](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-D.md) · [OCR](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/evidence/ocr.md)
