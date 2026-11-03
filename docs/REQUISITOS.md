# Lista completa de condiciones del assessment

Fuente: docs/assessment-en.pdf, seis páginas. Las casillas representan capacidades verificadas, no la mera existencia de archivos. Agente A+ verificado con un LLM real (Google, mismo cliente) en 4 cohortes y de extremo a extremo con reinicio del contenedor. La validación con OpenRouter y el recorrido Android→LLM→Android siguen pendientes. Ver https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance, docs/ANDROID.md y https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/mobile.

## Entorno y entrega

- [ ] E01. Un único repositorio GitHub con todo el backend y la app (p. 2, 5-6). Repositorio inicial publicado y clonado; código completo pendiente.
- [x] E02. Entorno local Python aislado creado y dependencias instaladas; pip check correcto (p. 2).
- [x] E03. Docker local para construir y ejecutar el backend contenerizado (p. 2). Construcción y ejecución DB/backend verificadas; https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/postgres/summary.json.
- [x] E04. Android Studio o Xcode, según la plataforma (p. 2). Android SDK/JDK y Gradle verificados; app Kotlin/Compose compilada en debug/release.
- [ ] E05. Entregar respondiendo al correo con el enlace GitHub dentro de una semana desde la recepción (p. 6). Verificar fecha real de recepción; no inferirla de la fecha de creación del repo.
- [ ] E06. Entender la arquitectura y defender las decisiones/trade-offs en la entrevista posterior (p. 1).

## Datos y modelos

- [x] D01. Usar data/raw/series_76_electric_data.pdf como única fuente de cifras del agente (p. 2, 4). Las cifras salen solo de SQL; el resumen no aporta magnitudes (ADR 0001).
- [x] D02. Usar data/raw/series_76_summary.pdf como contexto de negocio, sin reemplazar las tablas eléctricas (p. 2). Glosario literal en series76.context_terms (16 términos con página); sin FK a productos.
- [x] D03. Script/pipeline que procese el PDF crudo y lo transforme al formato consultado por la herramienta (p. 3, 6). PDF → OCR → PostgreSQL y funciones de consulta verificados. Wrapper LangChain pendiente en B03. Ver docs/POSTGRES.md.
- [x] D04. Datos procesados incluidos o instrucciones claras para generarlos (p. 6). Salida real OCR en data/extracted/series76 e instrucciones reproducibles en docs/INGESTION.md; evaluación completa en https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/pipeline/verified.
- [x] D05. PostgreSQL ejecutándose localmente (p. 4). PostgreSQL 17.11 y persistencia tras reiniciar verificados.
- [x] D06. Si se implementa búsqueda semántica/vectorial, usar pgvector (condicional, p. 4). No aplica a producción: sin búsqueda vectorial (ADR 0001). El experimento archivado usó pgvector.
- [ ] D07. Utilizar modelos del API OpenRouter proporcionado para el LLM y embeddings, si se usan (p. 2-3).
- [x] D08. Modelos configurables por variables de entorno (p. 2). OPENROUTER_CHAT_MODEL y AGENT_* en Compose y .env.example.
- [x] D09. Explicar elección de modelos en README (p. 2). Comparación Google y candidato3.6 Flash justificados con resultados y costo; despliegue OpenRouter todavía pendiente.
- [ ] D10. Respetar presupuesto total de USD 10; no habrá recarga (p. 2-3).
- [x] D11. Las cifras mostradas deben coincidir con las tablas; el LLM no debe inventarlas ni responderlas de memoria (p. 4). Las respuestas se renderizan desde SQL; las cifras que el modelo propone deben aparecer en la conversación. Ver la trampa de inyección en Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.

## Backend y comportamiento

- [x] B01. Servicio REST en Python con FastAPI (p. 2-4). Catálogo, sesiones, mensajes y conversación implementados y probados; interpretar lenguaje requiere configurar modelo.
- [x] B02. Agente orquestado con LangChain (p. 3-4). A+: una tool call por turno con cuatro herramientas. Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B03. Al menos una LangChain Tool propia que consulte datos de las tablas (p. 3). Wrappers get_actuator/search_actuators ejecutados contra PostgreSQL en pruebas.
- [x] B04. Consulta exacta de datos por Base Part Number (p. 1). Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B05. Recomendación de uno o más actuadores según requisitos técnicos (p. 2). Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B06. Conversación de varios turnos por session_id (p. 3). Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B07. Resolver referencias al contexto previo, como preguntar por potencia sin repetir el código (p. 3). También tras reiniciar el contenedor: https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/e2e/restart_check.json. OpenRouter pendiente.
- [x] B08. Historial persistente, recuperable después de reiniciar el backend; no solo memoria (p. 3-4). Mensajes y productos restaurados por HTTP tras reinicio real DB/backend; routing controlado, https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/mobile/backend.json.
- [x] B09. Manejar números de parte inválidos (p. 3, 6). Inexistente, parcial, sin /A, sufijo erróneo y canonicalización. Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B10. Manejar datos ausentes (p. 3, 6). source_NA frente a not_in_layout y DC sin frecuencia. Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B11. Manejar consultas ambiguas (p. 3, 6). Aclaraciones de servicio, frecuencia, producto y requisitos, y contradicciones. Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [x] B12. Manejar requisitos que ningún modelo satisface (p. 3). Indica qué requisito bloquea. Pendiente: un límite estricto ('below 5 W') falló en la cohorte v4; corregido en el prompt, sin verificar con LLM real. Evidencia LLM real (Google, cliente de producción): https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance/RESULTADOS.md; OpenRouter pendiente.
- [ ] B13. Manejar entradas inesperadas y casos distintos de los ejemplos; evaluación con casos propios de Konecto (p. 6). 28 escenarios de reserva escritos antes de ejecutar (inyección, fuera de alcance, español). Los casos de Konecto no se pueden verificar de antemano.

## Contrato obligatorio de API

- [x] A01. POST /api/conversation (p. 3). Contrato probado con interpretación controlada.
- [x] A02. Request con query y session_id opcional (p. 3).
- [x] A03. Sin session_id: iniciar conversación y devolver nuevo identificador (p. 3). Requiere modelo configurado en ejecución normal.
- [x] A04. Con session_id: continuar esa conversación (p. 3). Persistencia probada; comprensión lingüística real pendiente en B07.
- [x] A05. Response con session_id y answer; se permiten campos adicionales (p. 3).
- [x] A06. Productos estructurados, message_id y trazas recuperadas por endpoint de desarrollo separado (p. 3).

Request mínimo: {"query":"..."}. Request de continuación: {"session_id":"...","query":"..."}. Response: {"session_id":"...","answer":"...", ...}.

## App nativa

- [x] M01. Kotlin + Jetpack Compose O Swift + SwiftUI; no Flutter ni web como sustituto (p. 4). APK debug/release compilados.
- [x] M02. Pantalla de conversaciones guardadas (p. 4). API paginada y pantalla verificadas; fixtures solo en androidTest.
- [ ] M03. Abrir conversación anterior, cargar mensajes y continuar con el mismo contexto (p. 4). Implementado y probado por capas; falta recorrido completo con LLM real.
- [ ] M04. Crear conversación nueva (p. 4). Flujo y contrato probados; falta envío integral contra modelo real.
- [x] M05. Pantalla de chat multi-turn que conserve session_id (p. 4). Verificado con pruebas de ViewModel y contrato HTTP.
- [x] M06. Mostrar datos claros y comparables (p. 4). Ficha/tabla con servicio, frecuencia y unidades; captura en emulador.
- [x] M07. No mostrar herramientas ni detalles internos al usuario final (p. 4). Payload público separado de trazas.
- [x] M08. Pantalla debug solo para desarrolladores (p. 4). Implementación y cliente excluidos del source set release.
- [x] M09. Por respuesta: herramientas, parámetros y datos (p. 4). API con herramientas reales y pantalla con fixtures verificadas; LLM real pendiente.
- [x] M10. Acceso debug documentado y excluido de release (p. 4). docs/ANDROID.md.
- [x] M11. Estados de carga/error en las tres pantallas (p. 5). Conectividad, recuperación y representación probadas por capas.
- [x] M12. Un solo usuario, sin login, listado paginado de conversaciones (p. 5).

## Archivos y documentación de entrega

- [ ] R01. Código completo backend + app en el mismo repositorio (p. 5).
- [x] R02. Pipeline de ingestión y datos procesados o instrucciones para generarlos (p. 6). OCR/carga SQL documentados y verificados.
- [x] R03. Dockerfile que construya backend (p. 6). Construido/probado con dependencias congeladas e imagen base fijada.
- [x] R04. docker-compose.yml que arranque backend y base de datos (p. 6). Ambos ejecutados y reiniciados sin perder catálogo.
- [ ] R05. .env.example con valores ficticios, sin claves reales (p. 6). Preparado.
- [ ] R06. README con requisitos y variables de entorno (p. 6). Documentado para scaffold; completar al entregar.
- [x] R07. README con construcción/ejecución Docker y acceso a API (p. 6). Ver docs/POSTGRES.md.
- [x] R08. README con ejecución de ingestión y ubicación de resultados (p. 6). OCR y carga SQL documentados.
- [x] R09. Compilación/ejecución en emulador o dispositivo documentada (p. 6). docs/ANDROID.md; ejecución local verificada en emulador.
- [x] R10. URL del backend configurable por propiedad Gradle y documentada (p. 6).
- [x] R11. Acceso a debug y aislamiento de release documentados (p. 6).
- [x] R12. README con arquitectura, decisiones y trade-offs, incluyendo modelos (p. 2, 6). ADR 0001 y docs/ARQUITECTURA.md; validar el modelo en OpenRouter sigue pendiente.
- [x] R13. Si se agregan opcionales: usuarios de prueba y explicación de voz (p. 6). Login implementado; cuentas de prueba y generación de credenciales locales documentadas en AUTH.md. Voz no implementada; no se declara verificada.
- [ ] R14. Directorio real de configuración del asistente de IA utilizado (p. 6). Se incluye .codex/ con alcance documentado y AGENTS.md.
- [ ] R15. Instrucciones completas y reproducibles sin consultas adicionales; verificar ejecución limpia antes de entregar (p. 6).

## Endpoints sugeridos, no contratos obligatorios

- GET /api/sessions: id, título y fecha de las conversaciones.
- GET /api/sessions/{id}/messages: historial para reanudación.
- POST /api/auth/login: solo si se implementa login.
- Se pueden cambiar nombres y formatos de estos endpoints explicándolo en README (p. 3). Las funciones de listar/reabrir siguen siendo necesarias para la app.

## Opcionales: solo después de completar lo obligatorio

El usuario seleccionó expresamente login y aislamiento por usuario. Implementación y evidencia en AUTH.md y https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/mobile/auth-v7: contraseña con hash, token por petición, propietario derivado del token, login nativo y usuarios de prueba. El historial antiguo se conserva sin asignarlo automáticamente. Estas pruebas no cierran las condiciones aún pendientes de interpretación con LLM real; voz sigue sin implementar.

Login (p. 5): email/password -> token; contraseñas con hash; usuarios de prueba precargados y documentados; cuarta pantalla de login; token en cada petición; usuario obtenido del token por backend; aislamiento de conversaciones por usuario. No se pide registro, recuperación de contraseña ni OAuth.

Voz (p. 5): mensajes de voz además de texto; transcripción en dispositivo, modelo abierto o OpenRouter; no se entrega clave aparte; gasto de OpenRouter comparte el límite; documentar funcionamiento y decisiones.

## Aclaraciones de alcance

- El uso de IA para escribir código está permitido y se espera; no sustituye entenderlo (p. 1).
- Google AI Studio aparece como sugerencia para experimentar con extracción sin gastar OpenRouter, no como obligación (p. 2).
- No se exige desplegar públicamente, usar múltiples agentes, entrenar modelos ni utilizar embeddings.
- OCR local es una elección inicial nuestra, no un motor impuesto por el assessment.
