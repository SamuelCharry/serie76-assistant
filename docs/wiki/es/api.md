# API

[Wiki](index.md) · [English](../en/api.md) · [Español](../es/api.md)

Superficie HTTP completa y fallos que debe manejar el cliente.

Todas las rutas `/api/*`, excepto login, requieren `Authorization: Bearer <TOKEN>`. El token caduca en 12 horas y logout revoca el actual. Se comprueba propietario antes del modelo; conversaciones ajenas o en cuarentena devuelven 404. La API usa `Cache-Control: no-store`. Ejecuta ejemplos desde la raíz; usa `curl.exe` en Windows PowerShell para evitar el alias. TOKEN, SESSION_ID y MESSAGE_ID son marcadores, nunca credenciales públicas.

## Mapa de endpoints

| Método y ruta | Solicitud / respuesta |
|---|---|
| GET `/health` | Proceso vivo, público: `{"status":"ok","stage":"conversation-api"}` |
| GET `/ready` | DB/migraciones/catálogo activo/glosario, público; 200 o 503; no prueba el modelo |
| POST `/api/auth/login` | `{email,password}` → `{access_token,token_type,expires_at,user:{id,email,name}}` |
| GET `/api/auth/me` | Perfil actual `{id,email,name}` |
| POST `/api/auth/logout` | Revoca token actual; 204 sin cuerpo |
| GET `/api/actuators/{part_number}` | Código completo con `/A`; producto con measurements, field_status, services, frequencies, certification, notes, provenance, evidence, occurrences |
| POST `/api/actuators/search` | JSON SearchFilters → `{status,total,limit,offset,products}` o needs_clarification con fields |
| POST `/api/conversation` | `{query,session_id?}` → `{session_id,answer,message_id,products,clarification,terms,assumptions}` |
| GET `/api/sessions?limit=50&offset=0` | `{sessions:[{id,title,created_at,updated_at,preview}],limit,offset}`; limit 1..100, offset 0..1000000 |
| GET `/api/sessions/{session_id}/messages?limit=100&before=SEQUENCE` | `{session_id,title,messages,has_more,next_before}`; página cronológica, limit 1..100; before opcional >=1 |
| GET `/api/messages/{message_id}/debug` | `{message_id,session_id,tool_calls}`; propietario, DEV_DEBUG=true, fuera de OpenAPI |
| GET `/docs`, `/redoc`, `/openapi.json` | Documentación generada por el framework; pública |
| GET `/docs/oauth2-redirect` | Helper público de redirección OAuth Swagger del framework |

`query` tiene 1..4000 caracteres y no admite solo espacios; se rechazan campos extra. Omite session_id para una conversación nueva y envía su UUID para continuar. Los mensajes públicos contienen id, sequence, role, content, products y created_at; sin contexto interno ni herramientas. Las fichas consumen `products`, no extraen cifras de answer.

## curl

Estas cuentas públicas son **TEST ONLY**. Copia access_token del login a TOKEN localmente; no publiques tokens reales.

```sh
curl -sS http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@series76.test","password":"Series76-Demo-1"}'
curl -sS http://localhost:8000/api/auth/me -H 'Authorization: Bearer TOKEN'
curl -i http://localhost:8000/api/conversation -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"query":"What is the motor power of 761A00-11300000/A?"}'
curl -sS http://localhost:8000/api/actuators/761A00-11300000/A -H 'Authorization: Bearer TOKEN'
curl -sS http://localhost:8000/api/actuators/search -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"service":"on_off","supply_voltage_v":110,"min_torque_nm":70}'
curl -sS http://localhost:8000/api/sessions -H 'Authorization: Bearer TOKEN'
curl -sS http://localhost:8000/api/sessions/SESSION_ID/messages -H 'Authorization: Bearer TOKEN'
curl -sS http://localhost:8000/api/messages/MESSAGE_ID/debug -H 'Authorization: Bearer TOKEN'
curl -i -X POST http://localhost:8000/api/auth/logout -H 'Authorization: Bearer TOKEN'
```

En Windows PowerShell sustituye curl por curl.exe y usa archivos JSON para evitar diferencias de comillas nativas:

```powershell
'{"email":"demo@series76.test","password":"Series76-Demo-1"}' | Set-Content -Encoding ascii login.json
curl.exe -sS http://localhost:8000/api/auth/login -H "Content-Type: application/json" --data-binary "@login.json"
'{"query":"What is the motor power of 761A00-11300000/A?"}' | Set-Content -Encoding ascii query.json
curl.exe -i http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@query.json"
Remove-Item login.json, query.json
```

Con token válido y sin modelo configurado, conversation devuelve HTTP 503:

```json
{"detail":"Conversation service unavailable. Check backend configuration and try again.","error_code":"not_configured"}
```

Forma de éxito (UUID ilustrativos, no respuesta capturada):

```json
{"session_id":"<UUID>","answer":"<rendered SQL answer>","message_id":"<UUID>","products":[],"clarification":null,"terms":[],"assumptions":[]}
```

## Contrato de búsqueda

Los campos y enumeraciones coinciden con los [filtros del agente](agent.md#herramientas-tipadas), más `limit=20` (1..100) y `offset=0` (0..1000000). La búsqueda pública rechaza contradicciones con 422; la herramienta conversacional las transforma antes en preguntas. Torque/duty/tasa sin servicio, o corriente/tiempo dependiente de frecuencia sin selección inequívoca, pueden devolver needs_clarification. AC/DC puede coincidir con AC o DC; pedir AC/DC exige compatibilidad combinada publicada. N/A se recupera por código pero no se recomienda. Sin coincidencias devuelve 200, sin inventar sustitutos.

## Modelo de errores

`detail` puede ser texto o lista de validación. Solo los fallos de modelo llevan error_code; los demás no prometen ese campo.

| HTTP | error_code | Significado | Presentación Android |
|---|---|---|---|
| 401 | ausente | Token ausente/caducado/inválido; login incorrecto | Sesión caducada / fallo login; limpia pantallas protegidas |
| 404 | ausente | Conversación inexistente/ajena o debug desactivado | No encontrada; volver y actualizar |
| 409 | ausente | Sesión procesándose | Recargar antes de reenviar |
| 422 | ausente | Request, UUID, código o filtros inválidos | Revisar mensaje/solicitud |
| 429 | ausente | Límite de login; Retry-After | Esperar antes de reintentar |
| 503 | not_configured | Falta clave/modelo o proveedor 401/403 | Assistant is not configured on the server |
| 503 | timeout, rate_limited, budget_exhausted, provider_unreachable, provider_error | Timeout, 429, 402, conexión u otro fallo del proveedor | Asistente temporalmente no disponible |
| 503 | rate_limited_local | Guarda horaria por proceso agotada | Asistente temporalmente no disponible |
| 503 | ausente | DB no disponible, capacidad de cuatro turnos llena u otro servicio | Asistente temporalmente no disponible (login tiene estado propio) |
| sin HTTP | ausente | Fallo de red/conexión | No conecta al backend; revisar dirección |


## Dónde está en el código

- [backend/app/main.py](../../../backend/app/main.py#L1)
- [backend/auth/api.py](../../../backend/auth/api.py#L55)
- [backend/conversation/api.py](../../../backend/conversation/api.py#L51)
- [backend/app/contracts.py](../../../backend/app/contracts.py#L1)
- [mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt#L61)

## Límites conocidos

El fallo del proveedor revierte el turno completo. Un timeout del cliente no prueba cancelación en servidor: recarga historial antes de repetir POST. No hay reintento POST automático, registro, recuperación de contraseña ni endpoint de refresh.
