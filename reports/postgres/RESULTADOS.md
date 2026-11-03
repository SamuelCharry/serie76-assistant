# Resultado: catálogo PostgreSQL y API técnica

Estado: verificado. PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2). Fuente y firma OCR preservadas en [summary.json](summary.json). Backend/DB Docker ejecutados con dependencias congeladas e imágenes fijadas por digest.

## Datos y persistencia

- 68 referencias, 869 cifras, cuatro filas N/A y cinco marcas de excepción. [Evaluación desde SQL](roundtrip_evaluation.json): 941/941 comprobaciones primarias y 272/272 atributos de contexto, cero diferencias contra la referencia visual.
- Comparación adicional contra catalog.json del pipeline: todos los valores, estados y campos reconstruidos coinciden. La carga no utiliza la referencia manual: esta solo participa en la evaluación posterior.
- Reinicio real de db/backend verificado: mismo import activo y hash canónico antes/después f7454653c8c1562455e84b2b1e06681915f0dea18e4a140ed88da6ee4c4c116d. No se borraron volúmenes ni datos existentes. El ID2 inicial refleja una secuencia consumida por un rollback, no una importación parcial.
- Carga repetida devuelve already_loaded; las pruebas comprueban rollback de carga incompleta y de DDL fallido, rechazo de hashes/versiones conflictivos y activación opcional/atómica de versiones.

## Pruebas e interfaces

62 pruebas pasan en conjunto: 43 previas de OCR/revisión y 19 nuevas de entrada/PostgreSQL/API. Las de integración se ejecutaron con SERIES76_TEST_DB=1 y rollback, sin eliminar esquema ni catálogo. Tests.log queda local por la regla general *.log; el driver genera el conteo y falla si la suite no termina correctamente.

Nueve comprobaciones HTTP reales registradas: salud, referencia válida, código mal formado, código inexistente, filtros de 24 V, torque compartido trifásico, aclaración de servicio, aclaración de frecuencia y rechazo de filtro desconocido. Readiness devuelve200 después de reiniciar. Pruebas adicionales cubren DB no disponible503 sin detalles privados, N/A, ciclos/arranques, excepciones CSA y paginación estable.

Ruff F/E9, pip check local y pip check dentro del contenedor pasan. Se conserva una advertencia de deprecación del adaptador httpx de Starlette en las pruebas; no afecta al backend HTTP real ni se ocultó como fallo resuelto.

## Planes y límites de rendimiento

[Planes completos](query_plans.json): consulta por código en catálogo real y tablas temporales sintéticas con100.000 entradas y100.000 prestaciones. Consulta exacta sintética: Index Scan, ejecución 0.037ms. Join filtrado sintético: 16.501ms. Medidas puntuales locales, no SLA ni prueba de carga concurrente. Las tablas temporales se revierten y no se mezclan con las68 referencias reales.

## Reproducir y continuar

[Comandos, esquema y contratos](../../docs/POSTGRES.md). Driver: .venv/Scripts/python.exe scripts/verify_catalog_db.py --restart. El catálogo está disponible en http://127.0.0.1:8000/docs. Backend y DB quedan corriendo en loopback.

La selección del LLM, wrappers LangChain, conversaciones/API conversacional y Android quedan para el siguiente bloque. Cero OpenRouter en esta implementación. No hubo commit/push ni cambios en issues. No se promete soporte para otros productos ni PDF arbitrarios.
