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
| POST `/api/conversation` | `{query,session_id?,answers?,remove_filters?}` → `{session_id,answer,message_id,products,lead,interaction,suggestions,suggested_replies,active_filters,comparison,clarification,terms,assumptions}` |
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

Con token válido y sin modelo configurado, un turno que necesita interpretación devuelve HTTP 503; saludos y envíos estructurados válidos no necesitan modelo:

```json
{"detail":"Conversation service unavailable. Check backend configuration and try again.","error_code":"not_configured"}
```

Ver abajo los campos aditivos y una respuesta T7 capturada.

## Contrato de búsqueda

Los campos y enumeraciones coinciden con los [filtros del agente](agent.md#herramientas-tipadas), más `limit=20` (1..100) y `offset=0` (0..1000000). La búsqueda pública rechaza contradicciones con 422; la herramienta conversacional las transforma antes en preguntas. Torque/duty/tasa sin servicio, o corriente/tiempo dependiente de frecuencia sin selección inequívoca, pueden devolver needs_clarification. AC/DC puede coincidir con AC o DC; pedir AC/DC exige compatibilidad combinada publicada. N/A se recupera por código pero no se recomienda. Sin coincidencias devuelve 200, sin inventar sustitutos.

## Modelo de errores

`detail` puede ser texto o lista de validación. Los fallos de modelo y validación de interacción T7 llevan error_code; los demás no prometen ese campo.

| HTTP | error_code | Significado | Presentación Android |
|---|---|---|---|
| 401 | ausente | Token ausente/caducado/inválido; login incorrecto | Sesión caducada / fallo login; limpia pantallas protegidas |
| 404 | ausente | Conversación inexistente/ajena o debug desactivado | No encontrada; volver y actualizar |
| 409 | ausente | Sesión procesándose | Recargar antes de reenviar |
| 422 | invalid_answers / invalid_filter | Respuestas/eliminaciones estructuradas inválidas | Revisar preguntas/filtros actuales |
| 422 | ausente | Request, UUID, código o filtros inválidos | Revisar mensaje/solicitud |
| 429 | ausente | Límite de login; Retry-After | Esperar antes de reintentar |
| 503 | not_configured | Falta clave/modelo o proveedor 401/403 | Assistant is not configured on the server |
| 503 | timeout, turn_deadline, rate_limited, budget_exhausted, provider_unreachable, provider_error | Timeout, 429, 402, conexión u otro fallo del proveedor | Asistente temporalmente no disponible |
| 503 | rate_limited_local | Guarda horaria por proceso agotada | Asistente temporalmente no disponible |
| 503 | ausente | DB no disponible, capacidad de cuatro turnos llena u otro servicio | Asistente temporalmente no disponible (login tiene estado propio) |
| sin HTTP | ausente | Fallo de red/conexión | No conecta al backend; revisar dirección |


## Contrato conversacional T7

La solicitud aditiva es `{session_id?,query,answers?,remove_filters?}`. `answers` asocia IDs pendientes con textos exactos de opción; `remove_filters` enumera filtros activos. Los valores por defecto son `{}` y `[]`. El código aplica cambios y repite SQL sin LLM; `query` conserva el mensaje legible del usuario. Respuestas desconocidas/no coincidentes devuelven 422 `invalid_answers`; filtros inactivos/inválidos, 422 `invalid_filter`, incluidos tipos malformados. El rechazo no persiste mensajes.

La respuesta conserva `session_id`, `message_id`, `answer` completo en texto plano, `products`, `clarification`, `terms` y `assumptions`, y añade:

| Campo | Contrato |
|---|---|
| `lead` | Una frase para producto/comparación; null en otro caso |
| `interaction` | Null o `{kind:"question",questions:[{id,prompt,options:[{value,label}]}]}` |
| `suggestions` | 0–3 mensajes opcionales ejecutables; vacía con interacción |
| `suggested_replies` | Alias obsoleto con la misma lista |
| `active_filters` | Etiquetas removibles `{field,label}`; [] sin búsqueda activa |
| `comparison` | Null o tabla/tarjetas con models, summary, assumptions, rows, hidden_rows y key_fields |

Con dos modelos las filas son `{field,label,values:[A,B],better:0|1|null}`; `rows` contiene diferencias y `hidden_rows` los iguales. Tres/cuatro modelos usan tarjetas, cuatro `key_fields`, un valor por modelo, `better:null` y ninguna fila oculta/flecha. Mostrar etiquetas y textos SQL, nunca IDs internos. Ver [fila real y preferencias](agent.md#comparación-y-lead).

Extracto capturado (IDs omitidos; respuesta completa en [T7-interactions.json](../../../reports/submission/T7-interactions.json)):

```json
{
  "answer": "Which service? Which frequency?",
  "lead": null,
  "products": [],
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "service",
        "prompt": "Which service?",
        "options": [
          {
            "value": "on_off",
            "label": "On/Off"
          },
          {
            "value": "modulating",
            "label": "Modulating"
          }
        ]
      },
      {
        "id": "frequency_hz",
        "prompt": "Which frequency?",
        "options": [
          {
            "value": "50",
            "label": "50 Hz"
          },
          {
            "value": "60",
            "label": "60 Hz"
          }
        ]
      }
    ]
  },
  "suggestions": [],
  "suggested_replies": [],
  "active_filters": [
    {
      "field": "min_torque_nm",
      "label": "torque >= 70 Nm"
    },
    {
      "field": "max_fla_a",
      "label": "FLA < 1.5 A"
    }
  ],
  "comparison": null
}
```

### Enviar respuestas y eliminar un filtro

Estas peticiones usan la pregunta servicio/frecuencia y los filtros capturados arriba. Reemplaza SESSION_ID por la conversación pendiente y TOKEN localmente; no reutilices UUIDs de la evidencia, cuyas transacciones se revirtieron. Envía respuestas y después elimina el torque aún activo:

```sh
curl -sS http://localhost:8000/api/conversation -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"session_id":"SESSION_ID","query":"On/Off · 60 Hz","answers":{"service":"on_off","frequency_hz":"60"}}'
curl -sS http://localhost:8000/api/conversation -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"session_id":"SESSION_ID","query":"Remove torque","remove_filters":["min_torque_nm"]}'
```

En Windows PowerShell usa archivos; el escape Unicode conserva el resumen exacto:

```powershell
'{"session_id":"SESSION_ID","query":"On/Off \u00b7 60 Hz","answers":{"service":"on_off","frequency_hz":"60"}}' | Set-Content -Encoding ascii answers.json
curl.exe -sS http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@answers.json"
'{"session_id":"SESSION_ID","query":"Remove torque","remove_filters":["min_torque_nm"]}' | Set-Content -Encoding ascii remove.json
curl.exe -sS http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@remove.json"
Remove-Item answers.json, remove.json
```

El Submit registrado conservó torque/FLA, agregó On/Off/60 Hz y preguntó carcasa; la eliminación posterior mantuvo servicio, frecuencia y FLA. Ambas pruebas prohibían reservar una llamada al modelo.

### Historial y compatibilidad

El historial del asistente persiste lead, interaction, ambas listas de sugerencias, active_filters y comparison junto a `id`/`content`. La migración aditiva 005 deja null/[] en campos nuevos de filas antiguas; no inventa historial. El cliente usa `suggestions` explícita y solo recurre a `suggested_replies` si falta. Android también lee comparaciones antiguas con `a`/`b`, ganador textual y contador oculto; sin lead muestra answer/content. `answer` sigue completo para curl/API.

La búsqueda directa admite límites `{value,op}` y pares inferior/superior; los escalares antiguos siguen inclusivos. `sort_by` y los ámbitos siguen la [política del agente](agent.md#política-conversacional-t7). Esta ruta conserva paginación.

## Dónde está en el código

- [backend/app/main.py](../../../backend/app/main.py#L1)
- [backend/auth/api.py](../../../backend/auth/api.py#L55)
- [backend/conversation/api.py](../../../backend/conversation/api.py#L51)
- [backend/app/contracts.py](../../../backend/app/contracts.py#L1)
- [mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt#L61)

## Límites conocidos

El fallo del proveedor revierte el turno completo. Un timeout del cliente no prueba cancelación en servidor: recarga historial antes de repetir POST. No hay reintento POST automático, registro, recuperación de contraseña ni endpoint de refresh.
