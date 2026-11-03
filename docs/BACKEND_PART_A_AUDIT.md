# Auditoría de Part A: Backend y Technical Considerations

Corte: 3 de noviembre de 2026. Fuente: [assessment original](assessment-en.pdf), páginas 2–4. Esta revisión separa implementación, pruebas por capas y validación con el proveedor requerido. No se hicieron inferencias externas ni cambios de código durante la auditoría.

## Resultado general

La infraestructura, los contratos, las herramientas y la persistencia están implementados. El backend aún no está cerrado como asistente operativo: OPENROUTER_API_KEY y OPENROUTER_CHAT_MODEL están vacíos tanto en la configuración local revisada como en el contenedor.

GET /health, /ready y /api/sessions respondieron200. /ready comprueba PostgreSQL/catálogo; no acredita un modelo configurado. POST /api/conversation en el backend real devuelve503 por falta de configuración del proveedor. Las nueve pruebas actuales de conversación pasaron contra PostgreSQL real con interpretación controlada. Una comprobación HTTP adicional creó una sesión, hizo un seguimiento con el mismo ID, obtuvo15W de SQL y recuperó cuatro mensajes; la transacción se revirtió y no se llamó un modelo. También se volvió a exportar SQL y evaluar:941/941 comprobaciones primarias y272/272 atributos, sin diferencias contra la referencia visual.

La evaluación previa sí usó modelos reales mediante la API de Google y run_agent: no fue una prueba HTTP del proveedor OpenRouter ni del recorrido completo desde Android.

## 4. Functional Requirements

| Condición | Evidencia actual | Qué falta |
|---|---|---|
| Servicio REST Python/FastAPI | Implementado; endpoints vivos y contrato probado. | Verificación integral del chat con proveedor final. |
| Agente LangChain con al menos una herramienta propia que consulte tablas | run_agent enlaza herramientas LangChain; get_actuator y search_actuators consultan PostgreSQL real. | Probar el cliente OpenRouter, no reimplementar las herramientas. |
| Script de ingestión PDF a formato consultado | OCR validado, CSV/JSON, carga SQL transaccional y consultas sobre esa base. | Ningún bloque funcional de ingestión pendiente; conservar regresiones. |
| Historial y conversación por session_id | Mensajes, productos y contexto persistidos; dos turnos HTTP con el mismo ID comprobados mediante routing controlado. | Dos o más turnos naturales por OpenRouter, incluyendo seguimiento sin repetir código. |
| Reanudar conversación tras reiniciar backend | Evidencia previa de reinicio real y recuperación de mensajes/productos en reports/mobile/backend.json. | Completar la reanudación con interpretación real después del reinicio. |
| Código de parte inválido | Diferencia formato inválido, código bien formado inexistente y referencia conocida. | Confirmar respuestas naturales con el proveedor final. |
| Datos ausentes | source_NA y not_in_layout diferenciados; no se inventan valores ni se convierten en cero. | Verificar la respuesta final y su estructura por OpenRouter. |
| Consultas ambiguas | ask_clarification y búsqueda con needs_clarification; contexto y validaciones disponibles. | Probar resolución de aclaraciones entre turnos, preservando requisitos. |
| Ningún modelo cumple requisitos | SQL devuelve lista vacía; respuesta explícita, sin sustituir por un modelo que incumple. | Probarlo con consultas naturales por el proveedor final. |

Los objetivos de consulta exacta por Base Part Number y recomendación según requisitos tienen implementación y evidencia SQL. Su aceptación integral queda dentro de las pruebas reales pendientes de arriba.

## Contrato API obligatorio

| Condición | Estado |
|---|---|
| POST /api/conversation | Implementado. |
| Request con query y session_id opcional | Modelos Pydantic; validación de vacío, longitud y UUID probada. |
| Sin session_id: crear y devolver una nueva conversación | Probado por HTTP con routing controlado. |
| Con session_id: continuar esa conversación | Dos respuestas200 con el mismo ID y cuatro mensajes comprobados; comprensión real por OpenRouter pendiente. |
| Response con session_id y answer | Implementado; añade message_id y products. |
| Diseñar datos adicionales para fichas y debug | Productos estructurados y trazas por endpoint de desarrollo separado; no se exponen herramientas en el historial público. |

GET /api/sessions y GET /api/sessions/{id}/messages están implementados. Son endpoints sugeridos en el enunciado, no nombres obligatorios. POST /api/auth/login es opcional; su ausencia no es una tarea pendiente para cerrar Part A.

## 5. Technical Considerations

| Punto literal | Estado y tarea restante |
|---|---|
| 1. LLM y embeddings mediante la API proporcionada; cuidar presupuesto | Pendiente en ejecución final: usar OpenRouter con la clave del assessment. La elección3.6 y sus costos están documentados, pero el experimento Google no acredita este punto. No se usan embeddings y no es obligatorio añadirlos. |
| 2. Orquestación con LangChain | Implementado y ejecutado con herramientas reales. La comprobación pendiente es el proveedor final. |
| 3. Elegir procesamiento/almacenamiento de tablas; PostgreSQL local obligatorio | Cumplido por el pipeline y PostgreSQL17.11 en Docker, con tipos, servicio/frecuencia, estados, notas y procedencia. |
| 3, condicional. pgvector si hay búsqueda semántica | No aplica: consultas relacionales deterministas, sin búsqueda vectorial. |
| 4. Conversaciones fuera de memoria, resistentes al reinicio | Cumplido en almacenamiento SQL y comprobado tras reinicio; falta la prueba de continuación lingüística real. |
| 5. Servidor REST FastAPI | Cumplido. |
| 6. Cifras fieles a las tablas; el LLM no las inventa ni recuerda | Catálogo reconstruido desde SQL:941/941 comprobaciones primarias y272/272 atributos. Las cifras del answer/productos se construyen desde SQL, no desde texto libre del modelo. Falta cerrar la trazabilidad en el recorrido final por OpenRouter. |

Requisitos vinculados de la página2: el identificador del modelo y las credenciales ya se leen de variables de entorno; falta configurarlos. La elección y sus trade-offs están explicados en README. No se verificó el saldo de la clave OpenRouter. El gasto de las pruebas Google se documenta aparte.

## Tareas para cerrar este bloque

1. **Configurar y alinear OpenRouter.** Clave privada en .env, google/gemini-3.6-flash y parámetros compatibles con el ensayo. El cliente actual fija temperatura0/máximo600; el ensayo usó muestreo predeterminado/thinking low/máximo2048. Registrar configuración efectiva y costo de una prueba acotada.
2. **Probar POST /api/conversation con lenguaje real.** Consulta exacta y recomendación por servicio, tensión, fases, frecuencia y umbrales. Incluir cambio de requisitos y aclaraciones sin perder restricciones previas.
3. **Cerrar los cuatro casos límite con el proveedor final.** Código incompleto/malformado/inexistente, N/A/campo no publicado, ambigüedad y ausencia de coincidencias. No dar por cerrada la comprensión solo porque el código rechaza parámetros erróneos.
4. **Verificar persistencia y continuidad real.** Crear conversación, obtener respuesta, reiniciar backend, recuperar historial y continuar con el mismo session_id sin repetir el modelo seleccionado.
5. **Registrar la aceptación numérica y de contrato.** Comprobar request/response, productos, unidades, servicio, frecuencia, notas y valores mostrados. Conservar las pruebas existentes y actualizar el checklist únicamente con esa evidencia.

La omisión de focus en el caso adversarial de3.6 es una observación de presentación, no una invención de cifras ni un requisito nuevo del assessment. Debe revisarse al validar la respuesta final, sin cambiar retrospectivamente la nota17/18 del experimento.

## Evidencia

- backend/app/contracts.py; backend/conversation/api.py, agent.py y store.py.
- tests/test_conversations.py: nueve pruebas aprobadas en esta revisión, sin proveedor externo.
- reports/mobile/backend.json: PostgreSQL real, reinicio y recuperación con routing controlado.
- reports/postgres/roundtrip_evaluation.json: igualdad numérica y contexto reconstruidos desde SQL.
- reports/model_eval/comparison.json: tres candidatos completos, selección Google y límites del ensayo.
