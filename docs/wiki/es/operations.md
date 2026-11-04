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
| `OPENROUTER_FALLBACK_MODEL` | _vacío_ | Modelo alternativo opcional en el mismo endpoint/clave; vacío lo desactiva. Solo fallos transitorios. |
| `AGENT_TURN_DEADLINE_S` | `60` | Plazo compartido entre intentos primarios y fallback, menor que los 70/75 s de Android. |
| `AGENT_RETRY_MIN_REMAINING_S` | `10` | Margen mínimo para iniciar intento; si falta, registra deadline_skipped sin reserva. |
| `AGENT_MAX_TOKENS` | `2048` | Máximo de tokens generados por decisión. |
| `AGENT_REASONING_EFFORT` | `low` | Esfuerzo de razonamiento; vacío omite parámetro. |
| `AGENT_TOOL_CHOICE` | `required` | Tool choice de bind_tools; vacío deja decidir al proveedor. |
| `AGENT_TIMEOUT_S` | `45` | Máximo por intento, reducido al plazo restante; SDK max_retries=0, LangChain controla retry acotado. |
| `AGENT_TEMPERATURE` | _vacío_ | Vacío usa muestreo predeterminado del proveedor. |
| `LANGSMITH_TRACING` | `false` | Trazas externas opt-in; requiere también clave. |
| `LANGSMITH_API_KEY` | _vacío_ | Credencial privada de trazas; nunca va a Android. |
| `LANGSMITH_PROJECT` | `serie76-assistant` | Proyecto de trazas. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Endpoint de trazas; configurar host UE para workspace UE. |
| `DEV_DEBUG` | `false` | Endpoint de trazas del propietario; false devuelve 404. |
| `OPENROUTER_EMBEDDING_MODEL` | _vacío_ | Modelo opcional; Google `gemini-embedding-2`, OpenRouter `google/gemini-embedding-2`. |
| `EMBEDDINGS_ENABLED` | `true` | ON solo con modelo configurado; `false` fuerza OFF. |
| `EMBEDDING_DIM` | `768` | Única dimensión admitida por esquema/cliente. |
| `EMBEDDING_BASE_URL` | _vacío_ | Hereda `OPENROUTER_BASE_URL` si vacío. |
| `EMBEDDING_API_KEY` | _vacío_ | Hereda `OPENROUTER_API_KEY` si vacío. |
| `EMBEDDING_EXCLUDE_SOURCES` | _vacío_ | IDs separados por comas; excluye procedencias retenidas antes de ranking/LIMIT. |
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
El modelo se evaluó mediante el endpoint Google compatible con OpenAI; la aceptación OpenRouter está pendiente. ready=200 comprueba catálogo/glosario, no credenciales, routing ni saldo. LangSmith permanece apagado salvo tracing=true y clave; activarlo envía prompts/texto/herramientas/filas externamente. Ver [agente](agent.md).

## pgvector

Compose y CI fijan `pgvector/pgvector:pg17-trixie@sha256:01215e09bd4bd582d20230e025b6c971deeeffee49ceef1aae167e839cb62a7e`. La migración 007 habilita vector y crea `series76.example_bank`/`concept_anchor`; 008 añade versiones, actividad y manifiesto inmutable. Las cifras de catálogo siguen en tablas relacionales.

Antes de cambiar la imagen de un volumen PG17 existente, haz backup y verifica versión real de collation/glibc. El volumen verificado se creó con glibc 2.41; el primer tag pg17 traía 2.36. Trixie conserva 2.41 y se verificaron collations y conteos tras el cambio. No borres el volumen ni cambies su contraseña para actualizar; nunca `docker compose down -v`. Una discrepancia requiere un plan de migración/reindexación, no ocultarla con un refresh de versión. [Backup y comprobaciones T9](../../../reports/submission/T9-embeddings.md).

## Example bank

El loader usa `config/agent_acceptance_cases_v7.json` y `config/concept_anchors.json`: 649 frases/interpretaciones únicas más 100 anclas. No almacena respuestas ni cifras publicadas como conocimiento; las cantidades presentes en una frase son requisitos de ese ejemplo, no requisitos de una nueva consulta. Conserva todos los IDs de procedencia, excluye etiquetas ambiguas/conflictivas y permite excluir fuentes retenidas. El banco incluye casos históricos v7: su replay es regresión, no aceptación retenida. [Método](testing.md#behavior-evaluation).

Configura modelo/endpoint/clave en `.env`, según la tabla, y arranca Compose. Comandos desde la raíz para PowerShell y macOS/Linux; el montaje suministra config sin alterar la imagen ni el entrypoint normal:

```text
docker compose run --rm --no-deps --entrypoint python -v ./config:/app/config:ro backend scripts/load_example_bank.py --dry-run
```

Solo después de autorizar la inferencia:

```text
docker compose run --rm --no-deps --entrypoint python -v ./config:/app/config:ro backend scripts/load_example_bank.py
docker compose up -d backend
```

La carga Google inicial estimó USD 0.004911 (aproximadamente USD 0.005), 749 textos en 24 requests; no es factura ni coste garantizado de OpenRouter. La repetición comprobada no tenía textos pendientes ni coste estimado adicional. Los vectores se separan por nombre de modelo: cambiar a `google/gemini-embedding-2` necesita una carga autorizada nueva, nunca renombrar vectores viejos. La carga es transaccional/idempotente; un fallo no devuelve cargos ya incurridos. `--replace-dataset --dataset-version VERSION` reemplaza explícitamente el conjunto completo, desactiva ausentes/conflictivos y conserva procedencia histórica; no uses un subconjunto como reemplazo completo.

Sin modelo, el loader falla antes de cargar; con modelo y sin clave, `--dry-run` puede calcular pendientes con DB disponible, pero una carga nueva falla sin inferencia válida. En conversación, OFF/configuración ausente/timeout/fallo SQL omite retrieval y mantiene el parser determinista; sin chat configurado, una consulta que requiere interpretación devuelve 503. El arranque solo prepara el cliente, nunca paga embeddings; las rutas deterministas tampoco los invocan. No se carga el banco automáticamente al arrancar. [Código loader](../../../scripts/load_example_bank.py), [cliente y deadline](../../../backend/conversation/embeddings.py).

**Voz/debug:** la voz se configura por permiso Android, sin clave de backend. Para trazas usa `DEV_DEBUG=true`, recrea backend y activa el gesto de siete toques; vuelve a `false` al terminar la revisión. El GET es perezoso y limitado al propietario. [Instrucciones Android](android.md#developer-debug).

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

### Falla el primer toque tras inactividad

El desajuste T7 era un socket del pool OkHttp que sobrevivía al antiguo keep-alive de 5 s de Uvicorn. Actualizar/reconstruir backend y APK: el pool cliente expira ahora a 30 s y el servidor a 75 s. Confirmar `--timeout-keep-alive 75`; no activar retries POST para ocultar el fallo. Si no se sabe si llegó el envío, recargar historial antes de repetir. [Regresión local y límites](android.md#fallo-del-primer-toque-por-conexión).

Ante respuestas lentas del proveedor, distinguir keep-alive del plazo de decisión de 60 s. Solo 503/timeout/conexión pueden reintentarse (dos intentos por modelo); nunca 4xx. El fallback opcional comparte plazo y cada intento real consume cuota local. `turn_deadline` / `deadline_skipped` indica que no quedaba margen para otro intento; subir timeouts sin control puede exceder el timeout de la app. Ver [agente](agent.md#retry-fallback-y-plazo-total).

### Android no conecta

Usa 10.0.2.2 para emulador o adb reverse para USB; recompila al cambiar backendUrl. Release requiere HTTPS.

Para administrar cuentas, `python -m backend.auth.cli create-user --email user@example.com --name Name` pide contraseña; no pongas credenciales privadas en el historial. `assign-legacy --session UUID --email user@example.com --confirm` asigna solo una conversación sin dueño tras revisión explícita. No hay asignación automática del historial antiguo. Login limita 10 intentos/correo y 30/IP por cinco minutos y dos verificaciones simultáneas por proceso; el proxy de confianza debe diseñarse antes de exponer públicamente.

## Dónde está en el código

- [docker/entrypoint.sh](../../../docker/entrypoint.sh#L1)
- [backend/conversation/agent.py](../../../backend/conversation/agent.py#L224)
- [backend/catalog/db.py](../../../backend/catalog/db.py#L15)
- [backend/auth/cli.py](../../../backend/auth/cli.py#L34)

## Límites conocidos

Cuatro turnos simultáneos por proceso; otro turno en la misma sesión recibe 409. La transacción DB sigue abierta durante el modelo. No se acredita cola distribuida, límite monetario global, TLS público, recuperación de contraseña ni campaña de backup/restauración. A 100× tráfico, guardas locales y transacciones largas requieren rediseño y medición.

## Preflight del esquema antes de cualquier cohorte

Ejecutar primero `python scripts/check_tool_schemas.py` sin red. Construye las cuatro herramientas reales sin base de datos ni credenciales e imprime bytes compactos, valores enum, arrays, campos obligatorios, profundidad, restricciones numéricas y arrays de objetos de lookup. Los límites offline para enums/arrays/obligatorios/profundidad son los anteriores a T6 (108/6/5/7); rechaza rangos numéricos, uniones/referencias y arrays de objetos en get_actuator. El tamaño en bytes por sí solo no predijo el límite acumulado del proveedor.

Solo con aprobación explícita de gasto, ejecutar `python scripts/check_tool_schemas.py --live` con OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL y OPENROUTER_BASE_URL opcional ya en el entorno del proceso. Nunca carga .env ni imprime la clave, la respuesta del proveedor o el cuerpo de errores; envía exactamente una petición con las cuatro herramientas y el prompt/glosario de producción, desactiva trazas, no ejecuta herramientas/SQL y no reintenta. Un 400 u otro fallo devuelve salida no cero: detenerse antes de la cohorte. Un preflight exitoso comprueba aceptación del esquema, no calidad de conversación. Repetir después de cambiar esquemas; la comprobación real del esquema compacto queda pendiente del coordinador.

Dónde: [script de preflight](../../../scripts/check_tool_schemas.py), [pruebas de complejidad y una llamada](../../../tests/test_tool_schema_budget.py), [comprobación solo de metadatos](../../../scripts/check_openrouter.py).
