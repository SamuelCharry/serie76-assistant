# Series 76

Un asistente Android para consultar y seleccionar actuadores de un catálogo técnico. **El modelo interpreta la petición; PostgreSQL y el código producen los valores y la respuesta.**

## Requisitos del assessment

| Parte | Requisito | Implementación y evidencia |
|---|---|---|
| **A · Backend (§4–5)** | Arquitectura, modelos y decisiones | [Arquitectura](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura) |
| A | Procesar el PDF y preservar cifras, unidades y procedencia | [Ingesta](https://github.com/SamuelCharry/serie76-assistant/wiki/Pipeline-de-ingesta) |
| A | PostgreSQL local y pgvector | [Base de datos y Docker](https://github.com/SamuelCharry/serie76-assistant/wiki/Base-de-datos-y-Docker) · [Modelo de datos](https://github.com/SamuelCharry/serie76-assistant/wiki/Modelo-entidad-relacion) |
| A | LangChain, herramientas, consulta por código y recomendación | [Agente LangChain](https://github.com/SamuelCharry/serie76-assistant/wiki/Agente-LangChain) |
| A | FastAPI, sesiones, seguimiento e historial persistente | [API REST](https://github.com/SamuelCharry/serie76-assistant/wiki/API-REST-FastAPI) |
| **B · Mobile App (§6)** | App nativa y conexión al backend | [Configuración Android](https://github.com/SamuelCharry/serie76-assistant/wiki/Configuracion-base-Android) |
| B | Listar, abrir y crear conversaciones | [Conversaciones](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Conversaciones) |
| B | Chat con sesión y datos claros y comparables | [Chat](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Chat-activo) |
| B | Herramientas, parámetros y datos por respuesta; acceso oculto | [Developer Debug](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Developer-Debug) |
| **C · Optional Features (§7)** | Login, hashes, usuarios demo e historial aislado | [Login](https://github.com/SamuelCharry/serie76-assistant/wiki/Parte-C1-Login) |
| C | Entrada por voz y decisiones de transcripción | [Mensajes de voz](https://github.com/SamuelCharry/serie76-assistant/wiki/Parte-C2-Mensajes-de-voz) |
| **Entregables (§8–9)** | Código, datos, Docker, configuración y reproducción | [Documentación y entrega](https://github.com/SamuelCharry/serie76-assistant/wiki/Documentacion-y-entrega) |
| **Evaluación** | Casos límite, calidad, carga/errores de UI y alcance de pruebas | [Resultados y límites](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites) |

## Estado de la entrega

- **Implementado:** OCR local, catálogo SQL, agente de una decisión, Android nativo, login e historial por usuario.
- **Verificado en su alcance:** reproducción desde la etiqueta, 10/10 pasos; 795 pruebas Python aprobadas y 2 omitidas; 126 pruebas JVM Android aprobadas.
- **Límite principal:** el candidato medido aprobó en promedio 79,4 % de las conversaciones v17. Las reparaciones posteriores tienen evidencia offline, sin una nueva medición pagada independiente.
- **Confirmado manualmente por el autor (2026-11-06):** micrófono y reconocimiento real funcionando en el emulador; sin artefacto automatizado adicional.
- **Pendiente:** validación física y cobertura completa de errores/permisos; acceso de evaluadores y correo.

[Checklist del assessment](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/SUBMISSION.md) · [Inicio rápido](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.es.md)
