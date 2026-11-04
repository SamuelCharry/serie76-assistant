# API

[Wiki](index.md) · [English](../en/api.md) · [Español](../es/api.md)

The complete HTTP surface and the failures a client must handle.

All `/api/*` routes require `Authorization: Bearer <TOKEN>` except login. Tokens expire after 12 hours and logout revokes the current token. Ownership is checked before model invocation; foreign or quarantined conversations return 404. API responses use `Cache-Control: no-store`. Copy examples from the repository root; use `curl.exe` on Windows PowerShell (avoid the `curl` alias). TOKEN, SESSION_ID and MESSAGE_ID below are placeholders, never public credentials.

## Endpoint map

| Method and path | Request / response |
|---|---|
| GET `/health` | Public process liveness: `{"status":"ok","stage":"conversation-api"}` |
| GET `/ready` | Public DB/migrations/active catalogue/glossary readiness; 200 or 503; does not probe the model |
| POST `/api/auth/login` | `{email,password}` → `{access_token,token_type,expires_at,user:{id,email,name}}` |
| GET `/api/auth/me` | Current `{id,email,name}` |
| POST `/api/auth/logout` | Revoke current token; 204, empty body |
| GET `/api/actuators/{part_number}` | Exact full code including `/A`; product with measurements, field_status, services, frequencies, certification, notes, provenance, evidence, occurrences |
| POST `/api/actuators/search` | SearchFilters JSON → `{status,total,limit,offset,products}` or needs_clarification with fields |
| POST `/api/conversation` | `{query,session_id?,answers?,remove_filters?,action?}` → `{session_id,answer,message_id,products,lead,interaction,suggestions,suggested_replies,active_filters,comparison,clarification,terms,assumptions,recommendation,debug}` |
| GET `/api/sessions?limit=50&offset=0` | `{sessions:[{id,title,created_at,updated_at,preview}],limit,offset}`; limit 1..100, offset 0..1000000 |
| GET `/api/sessions/{session_id}/messages?limit=100&before=SEQUENCE` | `{session_id,title,messages,has_more,next_before}`; chronological page, limit 1..100; optional before >=1 |
| DELETE `/api/sessions/{session_id}` | Owner-scoped soft deletion; 204; missing/foreign session: 404 |
| GET `/api/messages/{message_id}/debug` | `{message_id,session_id,tool_calls,debug}`; owner only, DEV_DEBUG=true, absent from OpenAPI |
| GET `/docs`, `/redoc`, `/openapi.json` | Framework-generated API documentation; public |
| GET `/docs/oauth2-redirect` | Framework Swagger OAuth redirect helper; public |

`query` must contain 1..4000 characters and cannot be blank; extra request fields are rejected. Omit session_id for a new conversation; supply its UUID to continue. Public messages contain id, sequence, role, content, products and created_at; no internal context or tool calls. Product cards consume `products`, not numbers parsed from answer.

## T8/T9 contract

`POST /api/conversation` adds `action` to `{query,session_id?,answers?,remove_filters?}`. Suggestions may be legacy strings or `{label,action}` objects; send the label as `query` and the received action without reconstructing it. `compare_top`, `show_all` and `rank_by` validate the persisted set and invoke neither chat nor embeddings. Invalid actions return 422 `invalid_action`; incompatible answers return 422 `empty_combination`, without persisting a turn.

Responses add `recommendation:{ranked_by,total,shown,items}` and `debug`; options can include `count` and `description`. Comparisons include `key_fields_reason`. The planner chooses shape/fields and the guard checks quantities/filters before presenting products; the client displays server values. Migration 006 persists these fields and soft deletion; [contracts](../../../backend/app/contracts.py), [interactions](../../../backend/conversation/interactions.py).

History does not embed full traces. `GET /api/messages/{id}/debug` lazily loads `{message_id,session_id,tool_calls,debug}`; `latency_ms`, `attempts`, `llm_called` and `retrieval` are nested under `debug`. Token, ownership and `DEV_DEBUG=true` are required; disabled, missing or foreign answers return 404. Android's hidden gesture is not authorization. Voice only fills the composer: there is no audio endpoint or automatic send. [Android usage](android.md).

## curl

These public accounts are **TEST ONLY**. Copy access_token from the login response into TOKEN locally; do not put real tokens in documentation.

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

For Windows PowerShell, replace curl with curl.exe and use file input for JSON (avoids native quote handling differences):

```powershell
'{"email":"demo@series76.test","password":"Series76-Demo-1"}' | Set-Content -Encoding ascii login.json
curl.exe -sS http://localhost:8000/api/auth/login -H "Content-Type: application/json" --data-binary "@login.json"
'{"query":"What is the motor power of 761A00-11300000/A?"}' | Set-Content -Encoding ascii query.json
curl.exe -i http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@query.json"
Remove-Item login.json, query.json
```

With a valid token but no configured model, a turn requiring language interpretation returns HTTP 503; greetings and valid structured submissions do not need the model:

```json
{"detail":"Conversation service unavailable. Check backend configuration and try again.","error_code":"not_configured"}
```

The T7 examples below are historical; the T8/T9 contract above adds the current fields.

## Search contract

Technical fields and enums match the [agent filters](agent.md#typed-tools), plus public `limit=20` (1..100), `offset=0` (0..1000000). Public search directly validates contradictory filters with 422; the conversational tool turns them into questions first. Torque/duty/rate without service, or frequency-dependent current/time without an unambiguous frequency, can return needs_clarification. AC/DC-compatible entries may match AC or DC; requesting AC/DC demands published combined compatibility. N/A entries are retrievable but excluded from recommendations. Empty results are 200, not a fabricated substitute.

## Error model

`detail` may be a string or a validation array. Model failures and T7 interaction validation carry error_code; other errors do not promise it.

| HTTP | error_code | Meaning | Android presentation |
|---|---|---|---|
| 401 | absent | Missing/expired/invalid token; invalid login | Session expired / login failure; protected screens cleared |
| 404 | absent | Missing/foreign conversation or debug disabled | Conversation not found; return and refresh |
| 409 | absent | Session is already processing | Reload before sending again |
| 422 | invalid_answers / invalid_filter | Invalid structured answers/removals | Review current questions/filters |
| 422 | absent | Invalid request, UUID, code or filters | Check message/request |
| 429 | absent | Login throttling; Retry-After | Wait before retrying |
| 503 | not_configured | Missing key/model or provider 401/403 | Assistant is not configured on the server |
| 503 | timeout, turn_deadline, rate_limited, budget_exhausted, provider_unreachable, provider_error | Provider timeout, 429, 402, connection or other failure | Assistant temporarily unavailable |
| 503 | rate_limited_local | Process rolling-hour call guard reached | Assistant temporarily unavailable |
| 503 | absent | DB unavailable, four-turn capacity full, other service unavailable | Assistant temporarily unavailable (login has its own error state) |
| no HTTP | absent | Network/connection failure | Cannot reach backend; check address |


## T7 conversation contract

Historical T7 captures; actions, recommendations and debug follow the T8/T9 contract above.

The additive request is `{session_id?,query,answers?,remove_filters?}`. `answers` maps pending question IDs to exact option strings; `remove_filters` lists active filter names. Defaults are `{}` and `[]`. Code applies these changes and reruns SQL with no LLM call; `query` remains the readable user-history entry. An unknown/nonmatching answer returns 422 `invalid_answers`; an inactive/invalid removal returns 422 `invalid_filter`, including malformed field types. Rejected submissions persist nothing.

Responses retain `session_id`, `message_id`, full plain-text `answer`, `products`, `clarification`, `terms` and `assumptions`, and add:

| Field | Contract |
|---|---|
| `lead` | One sentence for product/comparison display, otherwise null |
| `interaction` | Null or `{kind:"question",questions:[{id,prompt,options:[{value,label}]}]}` |
| `suggestions` | 0–3 optional executable messages; empty while interaction is present |
| `suggested_replies` | Deprecated alias containing the same list |
| `active_filters` | Removable `{field,label}` tags; [] without an active search |
| `comparison` | Null, or table/cards with models, summary, assumptions, rows, hidden_rows and key_fields |

Two-model rows are `{field,label,values:[A,B],better:0|1|null}`; only differences appear in `rows`, equal rows in `hidden_rows`. Three/four models use cards, four `key_fields`, one value per model, `better:null`, and no hidden rows/arrows. Display labels and SQL strings, never internal field IDs. See the [real comparison row and preference rules](agent.md#comparisons-and-lead).

Captured response excerpt (IDs omitted; full payload in [T7-interactions.json](../../../reports/submission/T7-interactions.json)):

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

### Submit answers and remove a filter

These requests use the captured service/frequency question and filters above. Replace SESSION_ID with that pending conversation's ID and TOKEN locally; do not reuse the evidence's rollback-only UUIDs. Submit first, then remove the still-active torque filter:

```sh
curl -sS http://localhost:8000/api/conversation -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"session_id":"SESSION_ID","query":"On/Off · 60 Hz","answers":{"service":"on_off","frequency_hz":"60"}}'
curl -sS http://localhost:8000/api/conversation -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"session_id":"SESSION_ID","query":"Remove torque","remove_filters":["min_torque_nm"]}'
```

Windows PowerShell uses file input; escaped Unicode preserves the exact readable summary:

```powershell
'{"session_id":"SESSION_ID","query":"On/Off \u00b7 60 Hz","answers":{"service":"on_off","frequency_hz":"60"}}' | Set-Content -Encoding ascii answers.json
curl.exe -sS http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@answers.json"
'{"session_id":"SESSION_ID","query":"Remove torque","remove_filters":["min_torque_nm"]}' | Set-Content -Encoding ascii remove.json
curl.exe -sS http://localhost:8000/api/conversation -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" --data-binary "@remove.json"
Remove-Item answers.json, remove.json
```

The recorded Submit retained torque and FLA, added On/Off/60 Hz, and asked for enclosure; removal then retained service, frequency and FLA. No model reservation was allowed in either test.

### History and compatibility

Assistant history messages persist lead, interaction, both suggestion lists, active_filters and comparison beside existing `id`/`content`. Additive migration 005 leaves older rows readable with null/[] for new fields; it does not invent missing history. New clients use explicit `suggestions`, falling back to `suggested_replies` only when absent. Android also reads legacy comparison `a`/`b`, string winner and hidden-count fields; without lead it displays answer/content. `answer` stays complete for curl/API consumers.

Direct search supports numeric `{value,op}` bounds and paired lower/upper bounds; legacy scalars remain inclusive. `sort_by` and service/frequency scope follow [agent policy](agent.md#t7-conversation-policy). This route remains paginated.

## Where in the code

- [backend/app/main.py](../../../backend/app/main.py#L1)
- [backend/auth/api.py](../../../backend/auth/api.py#L55)
- [backend/conversation/api.py](../../../backend/conversation/api.py#L51)
- [backend/app/contracts.py](../../../backend/app/contracts.py#L1)
- [mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt#L61)

## Known limits

Provider failure rolls back the whole turn. A client timeout does not prove the server cancelled: reload history before retrying a POST. No automatic POST retries, account registration, password recovery or refresh-token endpoint exists.
