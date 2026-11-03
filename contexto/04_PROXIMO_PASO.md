# Próximo bloque: PostgreSQL y consultas deterministas

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL, agente y Android siguen pendientes.

1. Diseñar esquema que preserve códigos completos, servicio, frecuencia, unidades, source_NA/not_in_layout, notas y procedencia por documento/tabla/celda.
2. Cargar la salida OCR de data/extracted/series76 transaccionalmente e idempotentemente. Usar hashes de fuente/pipeline y definir versiones entre documentos; no importar la referencia manual.
3. Verificar Docker/PostgreSQL sin borrar volúmenes ni resetear el equipo; su fallo histórico no demuestra el estado actual.
4. Probar consulta exacta y filtros técnicos, incluyendo torque compartido trifásico, N/A y tablas separadas de 24 V.
5. Después integrar herramientas LangChain, agente OpenRouter configurable, historial/API y Android.

No sustituir BOO por 800 ni eliminar decimales globalmente. Las columnas se asignan por unidades y encabezados; las potencias solo se propagan dentro de límites medidos. Las relecturas OCR deben resolver las dudas; si no, revisión explícita. Ver docs/PIPELINE_ACCEPTANCE.md para el contrato ya verificado.
