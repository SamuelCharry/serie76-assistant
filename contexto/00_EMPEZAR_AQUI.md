# Continuación del assessment Serie 76

## Android: presentación Editorial A vigente

El usuario rechazó la apariencia genérica de V2, mantuvo chat inicial/historial lateral y aprobó la opción Editorial A para toda la app con adaptación nativa. Nueva dirección docs/MOBILE_DIRECTION_V3.md; evidencia reports/mobile/redesign-v3 y .impeccable/review/redesign-v3. Rethink Sans local, blanco/ciruela/lila Konecto, compositor delineado, filas de sugerencias y movimiento nativo. Base anterior publicada en main:7f69e9c; cambios visuales en design/android-editorial-v3. Trece pruebas Android pasan y debug/release compilan. No cambiar backend/modelos como parte del diseño.

## Historial visual Android: V2

El usuario sustituyó la composición C por una dirección más cercana a Gemini y aprobó explícitamente sus adaptaciones nativas. Inicio en chat, historial en drawer izquierdo y compositor tonal; alcance funcional sin cambios. Dirección vigente: docs/MOBILE_DIRECTION_V2.md; evidencia nueva: reports/mobile/redesign-v2 y .impeccable/review/redesign-v2. Siete pruebas unitarias/contrato y seis instrumentadas pasan en API35, debug/release compilados. La revisión visual y documentación de este rediseño se registran separadas de la evidencia histórica C. No interpretar estas pruebas UI con repositorio controlado como validación app→LLM→SQL→app.

## Actualización: evaluación real del modelo en Google

El usuario autorizó agentes para comparar y luego uso eficiente de20.000COP cargados a Google. Se completaron18casos con3modelos:3.6 Flash17/18,3 Flash Preview17/18,3.5 Flash-Lite16/18. Candidato recomendado google/gemini-3.6-flash por menor gravedad del fallo: omitiófocus en un N/A pero no inventó cifras; Preview añadió60Hz no pedidos. Desempate mecánico costo/latencia favorecePreview, preferenciaingenieril3.6 está explícita.3.8 y3.1Lite no respondieron por503 y no se puntúan como0.

Evidencia reports/model_eval/RESULTADOS.md y comparison.json; código model_eval/, CLI de evaluación y continuación con ledger append-only. Costo por tokensUSD0.06533735; reserva conjunta conservadoraUSD0.22145935, capclienteUSD0.50. Cero inferencias OpenRouter. No modificar ni divulgar GOOGLE_API_KEY en .env. No se cambió el cliente de producción concurrente: actualmente600tokens/temperatura0 difiere deGooglelow/2048. Próximo paso: alinear cliente y probar porOpenRouter con parámetros/proveedor explícitos; después verificar app→LLM→SQL→app. No declarar validado ese recorrido con esta prueba directa de run_agent. Mantener otros cambios Android/conversación y sus decisiones de diseño.

Corte: 3 de noviembre de 2026. Verificar Git, procesos y Docker antes de actuar.

## Actualización Android y conversaciones (posterior al bloque PostgreSQL)

El usuario autorizó implementar el plan Android y aprobó la maqueta C. mobile/android contiene una app Kotlin/Compose compilable en debug/release; tres pantallas, inglés, fondo claro/lila Konecto, tabla comparativa, sin Firebase/login/voz. Wrappers LangChain, API de conversaciones y migración 002_conversations.sql están implementados. Historial/productos sobreviven reinicio real de DB/backend; ver reports/mobile/backend.json. Pruebas con routing controlado y datos SQL reales, cero OpenRouter. Clave y modelo siguen sin configurar/evaluar; no presentar como validada la comprensión del LLM. Guía actual: docs/ANDROID.md y reports/mobile. La descripción del bloque anterior a continuación es histórica respecto a agente/Android. No revertir cambios de catálogo ni borrar volúmenes.

OCR, PostgreSQL y consultas técnicas están implementados y verificados. PostgreSQL 17.11 y backend corren en Docker. La reconstrucción SQL coincide en 68 referencias, 869 cifras, cuatro N/A, cinco marcas y 272 atributos de contexto (941/941 comprobaciones primarias). Las 62 pruebas actuales pasan con SERIES76_TEST_DB=1. El reinicio de DB/backend conserva catálogo y hash. Ver docs/POSTGRES.md y reports/postgres/summary.json. Agente, LangChain, historial, selección del LLM y Android siguen pendientes.

Leer AGENTS.md, README.md, docs/REQUISITOS.md y docs/POSTGRES.md. Solo el PDF eléctrico aporta cifras; el resumen explica semántica. OCR: scripts/ingest.py; salida real: data/extracted/series76. Carga/consultas: backend/catalog; CLI: python -m backend.catalog.cli. Referencia manual exclusivamente para evaluación.

Docker Desktop arrancó correctamente; el fallo histórico ya no describe el estado actual. Servicios db/backend en puertos loopback5432/8000; volumen serie76-assistant_postgres_data. No borrar volúmenes. .env ignorado con contraseña generada: no mostrar/versionar. Cero OpenRouter. Imágenes fijadas por digest y requirements-backend.lock.txt. Desarrollo .venv con requirements-dev.txt; .venv-ingest conserva runtime OCR aislado. Pruebas DB usan rollback.

Siguiente: wrappers LangChain y diseño/persistencia de conversaciones; selección del LLM más adelante por instrucción del usuario. No introducir otros productos, pgvector, login ni voz. Los cambios de este bloque siguen locales, sin commit/push nuevo ni modificación de issues. No actualizar memorias globales sin solicitud.
