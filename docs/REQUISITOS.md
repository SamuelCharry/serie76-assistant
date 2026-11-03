# Lista completa de condiciones del assessment

Fuente: docs/assessment-en.pdf, seis páginas. Las casillas representan cumplimiento funcional final, no la mera existencia de una carpeta o archivo. Todas las capacidades de negocio siguen pendientes en este scaffold.

## Entorno y entrega

- [ ] E01. Un único repositorio GitHub con todo el backend y la app (p. 2, 5-6). Repositorio inicial publicado y clonado; código completo pendiente.
- [x] E02. Entorno local Python aislado creado y dependencias instaladas; pip check correcto (p. 2).
- [ ] E03. Docker local para construir y ejecutar el backend contenerizado (p. 2). CLI detectada; motor apagado durante la verificación inicial.
- [ ] E04. Android Studio o Xcode, según la plataforma (p. 2). Se elige Android/Kotlin/Compose; app pendiente.
- [ ] E05. Entregar respondiendo al correo con el enlace GitHub dentro de una semana desde la recepción (p. 6). Verificar fecha real de recepción; no inferirla de la fecha de creación del repo.
- [ ] E06. Entender la arquitectura y defender las decisiones/trade-offs en la entrevista posterior (p. 1).

## Datos y modelos

- [ ] D01. Usar series_76_electric_data.pdf como única fuente de cifras del agente (p. 2, 4).
- [ ] D02. Usar series_76_summary.pdf como contexto de negocio, sin reemplazar las tablas eléctricas (p. 2).
- [ ] D03. Script/pipeline que procese el PDF crudo y lo transforme al formato consultado por la herramienta (p. 3, 6). PDF → CSV/JSON implementado y verificado; falta integrar su carga PostgreSQL y herramienta final. Ver docs/INGESTION.md.
- [x] D04. Datos procesados incluidos o instrucciones claras para generarlos (p. 6). Salida real OCR en data/extracted/series76 e instrucciones reproducibles en docs/INGESTION.md; evaluación completa en reports/pipeline/verified.
- [ ] D05. PostgreSQL ejecutándose localmente, por ejemplo con Compose (p. 4).
- [ ] D06. Si se implementa búsqueda semántica/vectorial, usar pgvector (condicional, p. 4). No es obligatorio agregar búsqueda vectorial.
- [ ] D07. Utilizar modelos del API OpenRouter proporcionado para el LLM y embeddings, si se usan (p. 2-3).
- [ ] D08. Modelos configurables por variables de entorno (p. 2).
- [ ] D09. Explicar elección de modelos en README (p. 2).
- [ ] D10. Respetar presupuesto total de USD 10; no habrá recarga (p. 2-3).
- [ ] D11. Las cifras mostradas deben coincidir con las tablas; el LLM no debe inventarlas ni responderlas de memoria (p. 4).

## Backend y comportamiento

- [ ] B01. Servicio REST en Python con FastAPI (p. 2-4). Existe /health inicial; falta funcionalidad de negocio.
- [ ] B02. Agente orquestado con LangChain (p. 3-4).
- [ ] B03. Al menos una LangChain Tool propia que consulte datos de las tablas (p. 3).
- [ ] B04. Consulta exacta de datos por Base Part Number (p. 1).
- [ ] B05. Recomendación de uno o más actuadores según requisitos técnicos (p. 2).
- [ ] B06. Conversación de varios turnos por session_id (p. 3).
- [ ] B07. Resolver referencias al contexto previo, como preguntar por potencia sin repetir el código (p. 3).
- [ ] B08. Historial persistente, recuperable después de reiniciar el backend; no solo memoria (p. 3-4).
- [ ] B09. Manejar números de parte inválidos (p. 3, 6).
- [ ] B10. Manejar datos ausentes (p. 3, 6).
- [ ] B11. Manejar consultas ambiguas (p. 3, 6).
- [ ] B12. Manejar requisitos que ningún modelo satisface (p. 3).
- [ ] B13. Manejar entradas inesperadas y casos distintos de los ejemplos; evaluación con casos propios de Konecto (p. 6).

## Contrato obligatorio de API

- [ ] A01. POST /api/conversation (p. 3).
- [ ] A02. Request con query y session_id opcional (p. 3).
- [ ] A03. Sin session_id: iniciar conversación y devolver nuevo identificador (p. 3).
- [ ] A04. Con session_id: continuar esa conversación (p. 3).
- [ ] A05. Response con session_id y answer; se permiten campos adicionales (p. 3).
- [ ] A06. Diseñar la estructura adicional necesaria para representar productos y depuración en la app (p. 3).

Request mínimo: {"query":"..."}. Request de continuación: {"session_id":"...","query":"..."}. Response: {"session_id":"...","answer":"...", ...}.

## App nativa

- [ ] M01. Kotlin + Jetpack Compose O Swift + SwiftUI; no Flutter ni web como sustituto (p. 4).
- [ ] M02. Pantalla de conversaciones guardadas (p. 4).
- [ ] M03. Abrir conversación anterior, cargar mensajes y continuar con el mismo contexto (p. 4).
- [ ] M04. Crear conversación nueva (p. 4).
- [ ] M05. Pantalla de chat multi-turn que conserve session_id (p. 4).
- [ ] M06. Mostrar datos de producto claros y comparables; no solo párrafos de texto (p. 4).
- [ ] M07. No mostrar nombres de herramientas ni detalles internos al usuario final (p. 4).
- [ ] M08. Pantalla debug solo para desarrolladores (p. 4).
- [ ] M09. Para cada respuesta, mostrar herramientas ejecutadas, parámetros y datos devueltos (p. 4).
- [ ] M10. Documentar cómo acceder a debug; no exponerlo a usuarios finales (p. 4).
- [ ] M11. Todas las pantallas con estados de carga y errores, incluido backend inaccesible (p. 5).
- [ ] M12. Sin login, operar como aplicación de un solo usuario y listar todas sus conversaciones guardadas (p. 5).

## Archivos y documentación de entrega

- [ ] R01. Código completo backend + app en el mismo repositorio (p. 5).
- [ ] R02. Pipeline de ingestión y datos procesados o instrucciones para generarlos (p. 6).
- [ ] R03. Dockerfile que construya backend (p. 6). Preparado, ejecución aún no verificada.
- [ ] R04. docker-compose.yml que arranque backend y base de datos (p. 6). Preparado, ejecución aún no verificada.
- [ ] R05. .env.example con valores ficticios, sin claves reales (p. 6). Preparado.
- [ ] R06. README con requisitos y variables de entorno (p. 6). Documentado para scaffold; completar al entregar.
- [ ] R07. README con construcción/ejecución Docker y acceso a API (p. 6).
- [ ] R08. README con ejecución de ingestión y ubicación de resultados (p. 6). Pipeline real y ubicación de salida documentados; README y docs/INGESTION.md.
- [ ] R09. README con compilación/ejecución app en emulador o dispositivo (p. 6). Pendiente.
- [ ] R10. README con configuración de URL del backend en la app (p. 6). Pendiente.
- [ ] R11. README con acceso a debug (p. 6). Pendiente.
- [ ] R12. README con arquitectura, decisiones y trade-offs, incluyendo modelos (p. 2, 6).
- [ ] R13. Si se agregan opcionales: usuarios de prueba y explicación de voz (p. 6).
- [ ] R14. Directorio real de configuración del asistente de IA utilizado (p. 6). Se incluye .codex/ con alcance documentado y AGENTS.md.
- [ ] R15. Instrucciones completas y reproducibles sin consultas adicionales; verificar ejecución limpia antes de entregar (p. 6).

## Endpoints sugeridos, no contratos obligatorios

- GET /api/sessions: id, título y fecha de las conversaciones.
- GET /api/sessions/{id}/messages: historial para reanudación.
- POST /api/auth/login: solo si se implementa login.
- Se pueden cambiar nombres y formatos de estos endpoints explicándolo en README (p. 3). Las funciones de listar/reabrir siguen siendo necesarias para la app.

## Opcionales: solo después de completar lo obligatorio

Login (p. 5): email/password -> token; contraseñas con hash; usuarios de prueba precargados y documentados; cuarta pantalla de login; token en cada petición; usuario obtenido del token por backend; aislamiento de conversaciones por usuario. No se pide registro, recuperación de contraseña ni OAuth.

Voz (p. 5): mensajes de voz además de texto; transcripción en dispositivo, modelo abierto o OpenRouter; no se entrega clave aparte; gasto de OpenRouter comparte el límite; documentar funcionamiento y decisiones.

## Aclaraciones de alcance

- El uso de IA para escribir código está permitido y se espera; no sustituye entenderlo (p. 1).
- Google AI Studio aparece como sugerencia para experimentar con extracción sin gastar OpenRouter, no como obligación (p. 2).
- No se exige desplegar públicamente, usar múltiples agentes, entrenar modelos ni utilizar embeddings.
- OCR local es una elección inicial nuestra, no un motor impuesto por el assessment.
