# Próximo bloque: herramientas y conversaciones

## Actualización: evaluación real del modelo en Google

El usuario autorizó agentes para comparar y luego uso eficiente de20.000COP cargados a Google. Se completaron18casos con3modelos:3.6 Flash17/18,3 Flash Preview17/18,3.5 Flash-Lite16/18. Candidato recomendado google/gemini-3.6-flash por menor gravedad del fallo: omitiófocus en un N/A pero no inventó cifras; Preview añadió60Hz no pedidos. Desempate mecánico costo/latencia favorecePreview, preferenciaingenieril3.6 está explícita.3.8 y3.1Lite no respondieron por503 y no se puntúan como0.

Evidencia reports/model_eval/RESULTADOS.md y comparison.json; código model_eval/, CLI de evaluación y continuación con ledger append-only. Costo por tokensUSD0.06533735; reserva conjunta conservadoraUSD0.22145935, capclienteUSD0.50. Cero inferencias OpenRouter. No modificar ni divulgar GOOGLE_API_KEY en .env. No se cambió el cliente de producción concurrente: actualmente600tokens/temperatura0 difiere deGooglelow/2048. Próximo paso: alinear cliente y probar porOpenRouter con parámetros/proveedor explícitos; después verificar app→LLM→SQL→app. No declarar validado ese recorrido con esta prueba directa de run_agent. Mantener otros cambios Android/conversación y sus decisiones de diseño.

## Actualización posterior: plan Android implementado

Herramientas, persistencia de conversaciones y Android ya tienen implementación. Leer docs/ANDROID.md y reports/mobile antes de retomar; los pasos anteriores de abajo son históricos. Usuario aprobó maqueta C, inglés, estilo claro/lila y tabla de comparación. Próximo bloque funcional pendiente: elegir/configurar/evaluar el modelo OpenRouter y verificar lenguaje/contexto en el recorrido completo app -> LLM -> SQL -> app. No gastar presupuesto ni elegir un modelo por inferencia; la selección fue diferida por el usuario. No añadir Firebase/login/voz. Consultar evidencia de emulador, contratos y reinicio; ninguna de esas pruebas equivale a evaluación de un modelo real.

OCR, PostgreSQL y consultas técnicas están implementados y verificados. PostgreSQL 17.11 y backend corren en Docker. La reconstrucción SQL coincide en 68 referencias, 869 cifras, cuatro N/A, cinco marcas y 272 atributos de contexto (941/941 comprobaciones primarias). Las 62 pruebas actuales pasan con SERIES76_TEST_DB=1. El reinicio de DB/backend conserva catálogo y hash. Ver docs/POSTGRES.md y reports/postgres/summary.json. Agente, LangChain, historial, selección del LLM y Android siguen pendientes.

1. Reutilizar get_actuator/search_actuators de backend/catalog/repository.py para wrappers LangChain; no permitir SQL arbitrario del LLM ni releer el CSV en consultas.
2. Diseñar sesiones/mensajes persistentes en PostgreSQL con migraciones nuevas; no editar SQL ya aplicado.
3. Definir contrato conversacional con productos comparables, aclaraciones y trazas separadas para debug.
4. Probar contexto, historial y errores de forma determinista.
5. Elegir/evaluar LLM y costo más adelante; no consumir OpenRouter ahora. Después Android.

POST /api/conversation aún no existe. El catálogo SQL sí está listo: comprobar /ready. Evidencia en reports/postgres. No hacer commit/push ni actualizar memorias sin solicitud.
