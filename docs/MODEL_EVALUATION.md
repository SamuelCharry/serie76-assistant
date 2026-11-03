> Historical experiment documentation. Source and commands are in [archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/). Current verification summaries: [evidence](evidence/).

# Evaluación de modelos para el agente Serie 76

El objetivo es elegir un modelo que traduzca consultas a herramientas y argumentos correctos. No se vuelve a evaluar OCR ni se permite que el LLM produzca cifras del catálogo de memoria. El agente actual realiza una sola inferencia y el servidor redacta los datos técnicos desde PostgreSQL.

## Trabajo paralelo y control de llamadas

Tres agentes de trabajo realizaron investigación oficial de modelos/precios, construcción de casos y revisión independiente del evaluador. Solo un proceso controlador ejecuta inferencias y mantiene un bloqueo de cuota compartido. Los agentes de trabajo no poseen copias de la clave ni lanzan llamadas paralelas. Las cuotas pertenecen al proyecto/modelo, no se multiplican creando agentes o claves.

La clave se configura únicamente como GOOGLE_API_KEY o GEMINI_API_KEY en .env ignorado o en el entorno. No se incluye en prompts, URLs, resultados ni archivos versionados. El adaptador usa el host fijo de Google y bloquea el fallback create_model/OpenRouter. El LLM recibe casos públicos y declaraciones de herramientas; no recibe expected_arguments ni expected_facts. Las herramientas consultan la base local en modo de solo lectura.

## Candidatos y acceso real

La selección inicial documentada fue Gemini3.8 Flash,3.6 Flash y3.5 Flash-Lite. Los tres ofrecen function calling y equivalentes en OpenRouter. Se consulta el listado real del proyecto antes del ensayo; aparecer en él no acredita generación ni cuota.

El primer intento devolvió402 en los tres candidatos. Se detuvo la interpretación de calidad: no se generaron respuestas. Google documenta402 como pago requerido/saldo Prepay agotado, distinto de429. El usuario posteriormente informó que cargó20.000COP y autorizó usarlos eficientemente. El ensayo pasó a usar ese saldo de Google con tope conservador local de USD0,50 para el conjunto de cohortes; no se utilizó saldo de OpenRouter.

Los503 posteriores se registran como indisponibilidad del proveedor, no como precisión0. Se añadieron3.1 Flash-Lite y3 Flash Preview como alternativas documentadas. No se eligió3.5 Flash como alternativa independiente: Google lo autorutea a3.6. La disponibilidad efectiva, modelVersion y cobertura quedan en los resultados, sin sustituir mediciones ausentes por un ganador supuesto.

Fuentes primarias: [precios](https://aistudio.google.com/docs/pricing), [errores](https://aistudio.google.com/docs/api-errors), [límites](https://aistudio.google.com/docs/rate-limits), [deprecaciones](https://aistudio.google.com/docs/deprecations). Las tarifas y disponibilidad deben revisarse antes de otra ejecución; los precios de3.8/3.6 cambian desde enero2027.

## Casos y medición

Corpus de desarrollo fijo de18casos en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/model_eval/cases.py, con subconjunto estratificado de12 para pruebas de acceso. Incluye códigos completos/incompletos/malformados/inexistentes, On/Off frente a modulación, AC/DC, trifásico compartido, N/A, campo no publicado, CSA, frecuencia ambigua, seguimiento y petición adversarial de inventar cifras.

Se verifica cada expectativa primero contra PostgreSQL usando un router determinista sin inferencia. Ese preflight valida el evaluador y las expectativas; nunca se presenta como una puntuación de modelos.

Métricas:

- Selección de herramienta y preservación de TODOS los requisitos; añadir un filtro no pedido también es error.
- Validación de argumentos y coincidencia de hechos/resultados esperados de las herramientas.
- Aclaraciones semánticamente equivalentes, solo si la ruta alternativa conserva explícitamente los filtros originales y no inventa otros.
- Latencia de la solicitud, tokens de entrada/salida/thinking y errores por intento. Los reintentos no borran la historia del proveedor.
- Cobertura y versión del modelo. No se asigna precisión a un candidato que no consiguió responder.

Una llamada get/search errónea puede ser rechazada por el esquema sin mostrar cifras incorrectas. Eso acredita la protección del código, no la comprensión del modelo. Del mismo modo, el texto renderizado en inglés y la omisión verbal de in-lb en el renderer son límites comunes del backend actual; no se atribuyen a un modelo concreto.

## Configuración comparable y gasto

Los candidatos usan el mismo prompt, schemas y casos, thinking_level=low y maxOutputTokens=2048; se mantienen los parámetros de muestreo predeterminados de Gemini. Se registra el hash del código, corpus, catálogo y configuración. Una modificación concurrente del protocolo impide mezclar resultados. No se entrenan ni afinan prompts durante la comparación.

No se usa grounding, búsqueda web ni caché explícita en las inferencias. El costo calculado usa las tarifas GoogleStandard verificadas el3nov2026:

| Modelo | USD/1M entrada | USD/1M salida y thinking |
|---|---:|---:|
|3.8/3.6 Flash|0,75|3,75|
|3.5 Flash-Lite|0,30|2,50|
|3.1 Flash-Lite|0,25|1,50|
|3 Flash Preview|0,50|3,00|

Costo estimado: promptTokenCount por tarifa de entrada, más candidatesTokenCount+thoughtsTokenCount por tarifa de salida. No volver a sumar totalTokenCount. No se descuentan posibles tokens cacheados; no se crean recursos de caché con cargos de almacenamiento.

Antes de cada intento se reserva entrada conservadora y el máximo combinado de salida/thinking. Si no llega usageMetadata, se conserva la reserva. Los importes son cálculo de cliente, no consulta del saldo ni factura de Google. El tope no limita otras aplicaciones que utilicen el mismo proyecto.

Resultados parciales se escriben incrementalmente y permiten continuar sin repetir casos ya medidos. Los errores402/401/configuración detienen los modelos del proyecto;429 requiere continuación explícita tras recuperar cuota. Una red fallida no genera reintentos ilimitados.

## Ejecutar

Entorno de evaluación independiente del backend y del runtime OCR:

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


Para inferencia real, configurar la clave privada, verificar el tier/saldo del proyecto y revisar precios/cap en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/config/model_eval.json:

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


No iniciar múltiples evaluadores. En una reanudación solo usar --retry-provider-errors después de revisar el motivo del fallo. No borrar resultados fallidos ni el bloqueo de un proceso vivo. Una clave distinta del mismo proyecto no recupera su cuota.

La ejecución publicada se continuó con `https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/scripts/continue_model_eval.py`: preserva ambos JSONL, verifica código/corpus/catálogo, captura sin red el payload exacto y publica refinamientos de reserva en sidecars. Antes de cada llamada comprueba que bytes/hash coinciden con lo capturado. El presupuesto suma ambas cohortes sin duplicar el parent. Amplió explícitamente el límite operacional de20a24intentos por modelo para recuperar errores503; mantuvo USD0,50 compartidos y nunca repitió casos ya evaluados. `--dry-run` no hace inferencias ni guarda puntajes de sus mocks. Las pruebas de captura no se mezclan con las54generaciones reales.

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


El generador de informe describe los snapshots revisados de esta ejecución; no elige automáticamente un ganador futuro ni debe reutilizarse sin revisar su análisis cualitativo. Los hashes de artefactos están en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval/manifest.json.

## Selección y límites

Los resultados reales y la recomendación observada se publican en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval/RESULTADOS.md. Una comparación válida exige los mismos casos y protocolo; se muestran aparte candidatos no disponibles y ejecuciones incompletas. Una muestra por caso y un corpus público de desarrollo no demuestran superioridad universal ni significancia estadística.

El ensayo Google no valida el endpoint de despliegue OpenRouter. El cliente de producción actual utiliza parámetros distintos (temperatura0/máximo600); debe alinearse y someterse a una prueba pequeña por OpenRouter antes de declarar integración verificada. Esa prueba y la clave de OpenRouter quedan fuera de este gasto autorizado de Google. No se cambia automáticamente el modelo de producción a partir de un resultado parcial.
