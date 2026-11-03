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
| POST `/api/conversation` | `{query,session_id?}` → `{session_id,answer,message_id,products,clarification,terms,assumptions,suggested_replies,comparison}` |
| GET `/api/sessions?limit=50&offset=0` | `{sessions:[{id,title,created_at,updated_at,preview}],limit,offset}`; limit 1..100, offset 0..1000000 |
| GET `/api/sessions/{session_id}/messages?limit=100&before=SEQUENCE` | `{session_id,title,messages,has_more,next_before}`; chronological page, limit 1..100; optional before >=1 |
| GET `/api/messages/{message_id}/debug` | `{message_id,session_id,tool_calls}`; owner only, DEV_DEBUG=true, absent from OpenAPI |
| GET `/docs`, `/redoc`, `/openapi.json` | Framework-generated API documentation; public |
| GET `/docs/oauth2-redirect` | Framework Swagger OAuth redirect helper; public |

`query` must contain 1..4000 characters and cannot be blank; extra request fields are rejected. Omit session_id for a new conversation; supply its UUID to continue. Public messages contain id, sequence, role, content, products and created_at; no internal context or tool calls. Product cards consume `products`, not numbers parsed from answer.

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

With a valid token and no configured model, conversation returns HTTP 503:

```json
{"detail":"Conversation service unavailable. Check backend configuration and try again.","error_code":"not_configured"}
```

Success shape (illustrative UUID placeholders, not a captured response):

```json
{"session_id":"<UUID>","answer":"<rendered SQL answer>","message_id":"<UUID>","products":[],"clarification":null,"terms":[],"assumptions":[]}
```

## Search contract

Technical fields and enums match the [agent filters](agent.md#typed-tools), plus public `limit=20` (1..100), `offset=0` (0..1000000). Public search directly validates contradictory filters with 422; the conversational tool turns them into questions first. Torque/duty/rate without service, or frequency-dependent current/time without an unambiguous frequency, can return needs_clarification. AC/DC-compatible entries may match AC or DC; requesting AC/DC demands published combined compatibility. N/A entries are retrievable but excluded from recommendations. Empty results are 200, not a fabricated substitute.

## Error model

`detail` may be a string or a validation array. Only model failures carry error_code; other errors do not promise that field.

| HTTP | error_code | Meaning | Android presentation |
|---|---|---|---|
| 401 | absent | Missing/expired/invalid token; invalid login | Session expired / login failure; protected screens cleared |
| 404 | absent | Missing/foreign conversation or debug disabled | Conversation not found; return and refresh |
| 409 | absent | Session is already processing | Reload before sending again |
| 422 | absent | Invalid request, UUID, code or filters | Check message/request |
| 429 | absent | Login throttling; Retry-After | Wait before retrying |
| 503 | not_configured | Missing key/model or provider 401/403 | Assistant is not configured on the server |
| 503 | timeout, rate_limited, budget_exhausted, provider_unreachable, provider_error | Provider timeout, 429, 402, connection or other failure | Assistant temporarily unavailable |
| 503 | rate_limited_local | Process rolling-hour call guard reached | Assistant temporarily unavailable |
| 503 | absent | DB unavailable, four-turn capacity full, other service unavailable | Assistant temporarily unavailable (login has its own error state) |
| no HTTP | absent | Network/connection failure | Cannot reach backend; check address |


## T6 response additions

Answers, fixed messages and suggestions are English-only; Spanish user input is supported. Every new successful conversation response includes `suggested_replies` (exactly 3 short, distinct English messages generated by code) and nullable `comparison`. Public history messages include both fields. Additive migration 004 gives older messages [] replies and null comparison; clients must handle those defaults.

`comparison` has `models` (exactly two complete codes), `rows` of `{field,label,a,b,better}` and `identical_fields_hidden`. Only differences are included. a/b are SQL-formatted display strings; better is a, b or null, assigned only where direction is unambiguous. Answer stays plain text without Markdown tables. Tapping a suggested-reply chip sends its exact text; Android's difference card has three wrapping columns and no horizontal scroll.

Direct search magnitude filters accept `{value,op}` with gt/gte/lt/lte; legacy scalars remain inclusive. `sort_by` is an ordered list of fastest/lowest_power/highest_torque/lowest_current. The agent applies the count/narrowing/closest-value policy documented in [agent](agent.md#t6-conversation-policy); direct `/api/actuators/search` remains a paginated catalogue route.

## Where in the code

- [backend/app/main.py](../../../backend/app/main.py#L1)
- [backend/auth/api.py](../../../backend/auth/api.py#L55)
- [backend/conversation/api.py](../../../backend/conversation/api.py#L51)
- [backend/app/contracts.py](../../../backend/app/contracts.py#L1)
- [mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt#L61)

## Known limits

Provider failure rolls back the whole turn. A client timeout does not prove the server cancelled: reload history before retrying a POST. No automatic POST retries, account registration, password recovery or refresh-token endpoint exists.
