# Operación

[Wiki](index.md) · [English](../en/operations.md) · [Español](../es/operations.md)

Valores de configuración y recuperación sin destruir catálogo ni historial.

Docker Compose es la ruta de backend admitida. Copia el ejemplo solo si no hay configuración local; no sobrescribas un .env operativo. El arranque migra, carga catálogo/glosario validados y provisiona usuarios TEST ONLY idempotentemente antes de Uvicorn. El volumen persiste tras reinicio y compose down normal; nunca ejecutes `docker compose down -v`.

## Referencia de configuración

Los valores provienen de [.env.example](../../../.env.example) y [Compose](../../../docker-compose.yml), no del entorno privado local.

| Variable | Predeterminado | Propósito |
|---|---|---|
| `POSTGRES_DB` | `series76` | Base PostgreSQL al inicializar. |
| `POSTGRES_USER` | `series76` | Rol PostgreSQL al inicializar. |
| `POSTGRES_PASSWORD` | `replace-with-local-password` | Placeholder local; elegir valor privado antes de usar fuera de TEST ONLY. Compose lo exige; cambiarlo no restablece la contraseña del volumen. |
| `POSTGRES_PORT` | `5432` | Puerto DB en loopback del host; contenedor sigue en 5432. |
| `API_PORT` | `8000` | Puerto HTTP en loopback del host; contenedor sigue en 8000. |
| `OPENROUTER_API_KEY` | _vacío_ | Credencial privada de modelo; vacía desactiva interpretación. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Endpoint chat compatible OpenAI; predeterminado OpenRouter. |
| `OPENROUTER_CHAT_MODEL` | _vacío_ | ID explícito de modelo con herramientas; sin selección automática. |
| `AGENT_MAX_TOKENS` | `2048` | Máximo de tokens generados por decisión. |
| `AGENT_REASONING_EFFORT` | `low` | Esfuerzo de razonamiento; vacío omite parámetro. |
| `AGENT_TOOL_CHOICE` | `required` | Tool choice de bind_tools; vacío deja decidir al proveedor. |
| `AGENT_TIMEOUT_S` | `45` | Timeout del modelo en segundos; max_retries=0. |
| `AGENT_TEMPERATURE` | _vacío_ | Vacío usa muestreo predeterminado del proveedor. |
| `LANGSMITH_TRACING` | `false` | Trazas externas opt-in; requiere también clave. |
| `LANGSMITH_API_KEY` | _vacío_ | Credencial privada de trazas; nunca va a Android. |
| `LANGSMITH_PROJECT` | `serie76-assistant` | Proyecto de trazas. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Endpoint de trazas; configurar host UE para workspace UE. |
| `DEV_DEBUG` | `false` | Endpoint de trazas del propietario; false devuelve 404. |
| `OPENROUTER_EMBEDDING_MODEL` | _vacío_ | Sin uso en A+ operativo; sin vectores. |
| `TESSERACT_CMD` | _vacío_ | Ruta OCR local histórica, no ingestión RapidOCR; no se pasa al backend. |
| `GOOGLE_API_KEY` | _vacío_ | Solo evaluación; no se pasa al backend productivo. No autoriza gasto por sí sola. |
| `OPENROUTER_REQUIRE_PARAMETERS` | `true` | Añade provider.require_parameters al routing openrouter.ai. |
| `AGENT_MAX_CALLS_PER_HOUR` | `120` | Tope de intentos por hora móvil/proceso; reinicio lo borra; no límite monetario/global. |
| `DEMO_USERS_JSON` | _vacío_ | Vacío provisiona cuentas públicas TEST ONLY; [] desactiva nuevas; nunca restablece contraseñas. Override: array JSON de email/name/password. |

Compose transmite directamente estas variables de conexión backend (no son opciones adicionales de .env.example):

| Variable | Compose value | Purpose / Propósito |
|---|---|---|
| PGHOST | db | DB service / servicio DB |
| PGPORT | 5432 | Container DB port / puerto interno DB |
| PGDATABASE | POSTGRES_DB, fallback series76 | Database / base |
| PGUSER | POSTGRES_USER, fallback series76 | Role / rol |
| PGPASSWORD | POSTGRES_PASSWORD, required | Private connection password / contraseña privada |

`POSTGRES_PASSWORD` no tiene fallback Compose: debe ser no vacía; el ejemplo copiado aporta placeholder TEST ONLY. El healthcheck usa POSTGRES_USER/POSTGRES_DB del contenedor. `DATABASE_URL` es override local opcional en `backend/catalog/db.py`, no transmitido por este Compose. El CLI local carga conexión mediante local_environment(); Uvicorn fuera de Docker necesita PG* exportadas. No volcar entorno/configuración en reportes.

## Activar interpretación de lenguaje

Solo con autorización explícita de inferencia, configura estos valores locales privados y recrea backend. Documenta configuración; no autoriza llamadas ni acredita aceptación OpenRouter.

```dotenv
OPENROUTER_API_KEY=<your-private-key>
OPENROUTER_CHAT_MODEL=google/gemini-3.6-flash
```

```sh
docker compose up -d backend
curl http://localhost:8000/ready
```
El ID es el candidato histórico, no una garantía de disponibilidad actual. ready=200 comprueba catálogo/glosario, no credenciales, routing ni saldo. LangSmith permanece apagado salvo tracing=true y clave; activarlo envía prompts/texto/herramientas/filas externamente. Ver [agente](agent.md).

## Solución de problemas

### Puerto 5432 ocupado

Configura POSTGRES_PORT=5433 y recrea db/backend; no detengas bases ajenas. PGPORT interno sigue en 5432.

### /ready 503

Revisa docker compose ps y docker compose logs --tail 100 backend db localmente. Debe completar migraciones/catálogo/glosario; ejecuta cli status. Falta de modelo sola no falla readiness.

### Docker detenido

Inicia Docker Desktop con contenedores Linux, verifica docker info y reintenta up --build -d. No requiere reset/reinstalar ni borrar volúmenes.

### Entrypoint con CRLF

docker/entrypoint.sh requiere LF (.gitattributes). Ante /bin/sh^M o exec format failure restaura LF y reconstruye backend; conserva volumen DB.

### 503 not_configured

Configura clave y modelo solo tras autorización y recrea backend. Credenciales inválidas también pueden producirlo. Historial/catálogo funcionan sin modelo.

### Otros códigos 503

Consulta tabla de errores: timeout/cuota/saldo/red, guarda local o capacidad. No repitas POST a ciegas; recarga historial.

### Login falla tras reinicio

El arranque nunca restablece contraseñas demo. Usa credenciales existentes o administración explícita; no borres volumen para imponer contraseña pública.

### Android no conecta

Usa 10.0.2.2 para emulador o adb reverse para USB; recompila al cambiar backendUrl. Release requiere HTTPS.

Para administrar cuentas, `python -m backend.auth.cli create-user --email user@example.com --name Name` pide contraseña; no pongas credenciales privadas en el historial. `assign-legacy --session UUID --email user@example.com --confirm` asigna solo una conversación sin dueño tras revisión explícita. No hay asignación automática del historial antiguo. Login limita 10 intentos/correo y 30/IP por cinco minutos y dos verificaciones simultáneas por proceso; el proxy de confianza debe diseñarse antes de exponer públicamente.

## Dónde está en el código

- [docker/entrypoint.sh](../../../docker/entrypoint.sh#L1)
- [backend/conversation/agent.py](../../../backend/conversation/agent.py#L194)
- [backend/catalog/db.py](../../../backend/catalog/db.py#L15)
- [backend/auth/cli.py](../../../backend/auth/cli.py#L34)

## Límites conocidos

Cuatro turnos simultáneos por proceso; otro turno en la misma sesión recibe 409. La transacción DB sigue abierta durante el modelo. No se acredita cola distribuida, límite monetario global, TLS público, recuperación de contraseña ni campaña de backup/restauración. A 100× tráfico, guardas locales y transacciones largas requieren rediseño y medición.
