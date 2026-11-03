# Protocolo de comparación

## Objetivo y controles

Comparar A actual, B un agente con recuperación contextual, C dos especialistas, D supervisor y E proponente/revisor. Modelo de generación, herramientas SQL, catálogo y casos comunes. El efecto de recuperación se observa A/B; el de agentes adicionales, B frente a C/D/E. Los prompts necesariamente difieren por responsabilidad; no se atribuye causalidad universal a una diferencia descriptiva.

C/D/E son flujos acotados con roles LLM distintos, implementados con herramientas LangChain; no son sociedades de agentes autónomos ni modelos independientes. Usar el mismo modelo controla una variable, pero conserva el riesgo de errores correlacionados. El recuperador vectorial es una herramienta, no un agente por sí solo.

El corpus anterior de 18 casos es desarrollo. Los 24 escenarios nuevos se congelan antes de la primera generación. Cuatro por categoría: exacta, contexto, información insuficiente, seguimiento, contradicción y trampas técnicas. Seis escenarios piloto forman parte del mismo corpus y no se usan para modificar prompts después de observarlos. No es un benchmark independiente externo.

Los criterios de exactitud se basan en el PDF eléctrico y el SQL previamente auditado. No se incluyen respuestas esperadas en prompts, documentos vectoriales ni historial. Cada variante construye su propio historial de respuestas. Los seguimientos se evalúan como escenarios completos.

## Ejecución Windows

```powershell
./.venv-model-eval/Scripts/python.exe -m pip install -r requirements-architecture-eval.txt
./.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_architecture_eval.py -v
./.venv-model-eval/Scripts/python.exe -m architecture_eval setup
./.venv-model-eval/Scripts/python.exe -m architecture_eval prepare
./.venv-model-eval/Scripts/python.exe -m architecture_eval pilot
./.venv-model-eval/Scripts/python.exe scripts/continue_architecture_eval.py
./.venv-model-eval/Scripts/python.exe -m architecture_eval report
./.venv-model-eval/Scripts/python.exe scripts/analyze_architecture_eval.py
```

`setup` crea credenciales aleatorias solo en `.cache`, instancia pgvector aislada e importa la salida OCR validada. No usa manual/reference para cargar. Nunca usar `down -v` sobre el proyecto operativo. `prepare` genera embeddings reales en Google. La configuración está en `config/architecture_eval.json`; clave únicamente en `.env` ignorado o variable de entorno.

`frozen.json` registra hashes de implementación, casos, configuración, PDFs y catálogo. Reanudar no repite escenarios ya registrados ni cambia sus resultados. Un cambio congelado bloquea el append; no se permite modificar prompts para mejorar esta misma cohorte. El controlador usa bloqueo de archivo Windows; una sola ejecución pagada a la vez.

El script de continuación normaliza tuplas de Python a arrays JSON durante la comparación del manifiesto. Corrige una diferencia de representación detectada al reanudar el piloto; conserva todos los hashes, casos y presupuesto. No modifica el código congelado ni habilita reintentos de casos ya registrados.

## Presupuesto y fallos

Tope nuevo USD 0,50, compartido por embeddings, consultas y todas las variantes. Se reservan bytes UTF-8 del payload + 4096 tokens de margen y salida máxima antes de enviar cada llamada. Se cobra el uso declarado, incluyendo pensamiento; si falta uso o hay fallo, se conserva la reserva completa. El ledger es append-only y se sincroniza a disco antes de la red. No es una factura ni garantía de saldo del proveedor. Sin reintentos automáticos y sin fallback a otros modelos.

Precios consultados 2026-11-03: [Google](https://aistudio.google.com/docs/pricing). Generación 3.6 Flash: USD0,75 entrada/3,75 salida por millón; embeddings 001: USD0,15 por millón. Muestreo por defecto, pensamiento low, salida máxima 2048, separación mínima cinco segundos. El límite incluye reservas desconocidas aunque Google no las haya facturado.

Se rota la variante que empieza cada escenario y se comparan únicamente escenarios completos comunes a las cinco. Fallos de proveedor y agotamiento del presupuesto se separan del éxito lingüístico. La latencia incluye espera del controlador y recuperación; no equivale a una medición de concurrencia o capacidad productiva.

## Puntuación y decisión

Se verifica herramienta, argumentos, ausencia de filtros añadidos, hechos SQL esperados y aclaraciones equivalentes expresamente autorizadas por el caso. Definiciones requieren evidencia citada y palabras clave, una comprobación limitada de cobertura, no una evaluación exhaustiva de calidad semántica. Se publican IDs recuperados y distancia para revisión de relevancia.

Las cifras se renderizan desde SQL, por lo que este ensayo evalúa selección y preservación de requisitos, no la habilidad del modelo para escribir números de memoria. Un revisor no puede alterar cifras. Los casos ambiguos pueden necesitar aclaración aunque haya fragmentos parecidos.

El análisis final (`ANALISIS.md`/`analysis.json`) corrige una limitación del agregador original: rechazos de esquema/protocolo se cuentan como fallos de calidad, no se excluyen como errores de proveedor. `results.jsonl`, el ledger y la salida original se conservan intactos. Esto no modifica prompts ni convierte respuestas fallidas en éxitos. Los costos observados incluyen caché compartida y las latencias incluyen pacing; no permiten promoción por sí solos.

Promoción multiagente: completar los 24 escenarios comunes, resolver al menos dos más que B, sin filtros cambiados ni regresiones técnicas y costo medio/p95 como máximo doble de B. Si la evidencia es parcial, resultado inconcluso; no activar automáticamente ninguna variante. La regla de selección no sustituye la inspección de las trazas.

Antes de producción: cliente y embeddings OpenRouter mediante clave del assessment, regenerar índice si cambia el embedding y verificar contrato HTTP, persistencia tras reinicio y recorrido Android→LLM→SQL→Android. Este experimento Google no cierra esa aceptación.
