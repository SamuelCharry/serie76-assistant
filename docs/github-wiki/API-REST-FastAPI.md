# API REST · FastAPI

Android envía texto o acciones estructuradas y recibe datos listos para presentar. Las rutas de conversación requieren Bearer; la propiedad se comprueba en el servidor.

| Ruta | Función |
|---|---|
| `POST /api/auth/login` | Autenticar y obtener token |
| `POST /api/conversation` | Crear o continuar un turno |
| `GET /api/sessions` | Listar conversaciones propias |
| `GET /api/sessions/{id}/messages` | Recuperar historial propio |
| `DELETE /api/sessions/{id}` | Borrado lógico de conversación propia |
| `GET /api/messages/{id}/debug` | Traza propia, con `DEV_DEBUG=true` |
| `GET /ready` | Estado de base de datos, catálogo y glosario |

Petición mínima:

```json
{"query":"What is the motor power of 761A00-11300000/A?"}
```

La respuesta incluye `session_id` y `answer`, además de productos, comparación, preguntas o recomendaciones según el caso. El siguiente turno envía el mismo `session_id`; omitirlo inicia otra conversación.

Se comprueba propietario antes del modelo y se bloquea la sesión durante el turno. Mensajes y snapshots se guardan juntos; un fallo del proveedor revierte el turno. Hay capacidad limitada por proceso, no una cola distribuida.

**Errores esperados:** falta de configuración del modelo → `503 not_configured`; combinación estructurada vacía → `422 empty_combination`; sesión ajena o inexistente → 404. Las trazas internas no deben aparecer como respuesta pública.

[Código](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/api.py) · [Contrato y ejemplos](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/wiki/es/api.md)
