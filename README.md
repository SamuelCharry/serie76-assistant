# Series 76 Technical Assistant

Continuación en otro agente: [carpeta de contexto](contexto/00_EMPEZAR_AQUI.md).

Repositorio para el assessment de Konecto. **Etapa actual:** OCR y PostgreSQL verificados. El agente definitivo A+ está implementado y aceptado con un LLM real (Google, endpoint OpenAI-compatible, mismo cliente de producción). La aceptación final con OpenRouter sigue pendiente. [Arquitectura](docs/ARQUITECTURA.md) · [ADR 0001](docs/adr/0001-arquitectura-agente.md) · [aceptación con LLM real](reports/agent_acceptance/RESULTADOS.md).

**Android:** [compilación, ejecución, URL, debug y arquitectura](docs/ANDROID.md). Kotlin/Compose, login nativo, chat e historial aislado por usuario; diseño claro/oscuro aprobado, sin Firebase ni voz. [Autenticación, cuentas de prueba y migración](docs/AUTH.md). Hay pruebas de UI en emulador y persistencia HTTP con interpretación controlada. Eso no equivale a validar un modelo real. Evidencia: [reports/mobile](reports/mobile).

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL y consultas técnicas ya están verificados; la aceptaci?n final OpenRouter sigue pendiente. Ver docs/POSTGRES.md.

**Salida del pipeline:** [tablas HTML](data/extracted/series76/catalog.html), [CSV](data/extracted/series76/catalog.csv), [JSON](data/extracted/series76/catalog.json). [Resultados y límites](reports/pipeline/RESULTADOS.md).

## Ejecutar la ingestión

```powershell
python -m venv .venv-ingest
./.venv-ingest/Scripts/python.exe -m pip install -r requirements-ingest.lock.txt
./.venv-ingest/Scripts/python.exe scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/mi-importacion
```

Acepta archivos o directorios. Usa RapidOCR/PP-OCRv5 local; no requiere Tesseract ni OpenRouter. Reconstruye columnas por encabezados/unidades y celdas combinadas por geometría. Las dudas bloquean la exportación validada. [Instalación, formatos, lotes, caché y reproducción](docs/INGESTION.md).

`data/reviewed/catalog-v1` y `extract_reviewed_catalog.py` conservan la referencia manual histórica; no generan esta salida. `config/ocr.json` pertenece al laboratorio anterior y no gobierna `scripts/ingest.py`. El Docker OCR existente conserva el ensayo Tesseract; el pipeline nuevo se verificó directamente en Windows, no en ese contenedor.

## PostgreSQL y API técnica

Con Docker Desktop activo, desde un checkout limpio:

```powershell
Copy-Item .env.example .env  # Solo si no existe; no sobrescribir configuraci?n local.
docker compose up --build -d
curl.exe http://127.0.0.1:8000/ready
```

El entrypoint migra, carga el cat?logo, carga el glosario y provisiona usuarios de
prueba de forma idempotente antes de arrancar Uvicorn. Los datos est?n montados en
solo lectura; el volumen PostgreSQL se conserva. `/ready` 200 verifica cat?logo y
glosario, no disponibilidad del LLM. No ejecutar `docker compose down -v`.

**Cuentas p?blicas SOLO DE PRUEBA**, precargadas para el evaluador:

| Email | Contrase?a de prueba |
|---|---|
| demo@series76.test | Series76-Demo-1 |
| reviewer@series76.test | Series76-Demo-2 |

Login Android o `POST /api/auth/login` con JSON `email` y `password`. No usar estas
cuentas en producci?n. `python -m backend.auth.cli ensure-demo-users` omite usuarios
existentes y nunca restablece sus contrase?as (tampoco si est?n desactivados).
`DEMO_USERS_JSON` permite sustituir la lista por objetos `email`, `name`, `password`;
`[]` desactiva la provisi?n y un valor vac?o usa las cuentas de prueba anteriores.
No publicar overrides privados. `seed-demo` conserva contrase?as aleatorias para
aprovisionamiento privado expl?cito.

- [OpenAPI](http://127.0.0.1:8000/docs), GET /health y GET /ready.
- GET /api/actuators/{part_number}: código completo incluido /A.
- POST /api/actuators/search: filtros técnicos y aclaraciones explícitas.

Carga transaccional/idempotente, versiones y activación atómica. Magnitudes NUMERIC por servicio/frecuencia; evidencia OCR vinculada. [Esquema, filtros, instalación y pruebas](docs/POSTGRES.md). [Resultados ejecutados](reports/postgres/RESULTADOS.md): 941/941 y 272/272 contexto desde SQL, HTTP real y persistencia tras reinicio.

## Requisitos y decisiones

- [Arquitectura, ER y alternativas multiagente](docs/ARQUITECTURA.md), [visor de diagramas](docs/architecture.html) y [protocolo experimental](docs/ARCHITECTURE_EVALUATION.md). Experimento aislado en pgvector/Google; no cambia la arquitectura operativa ni cierra la aceptación OpenRouter. [Resultados](reports/architecture_eval/ANALISIS.md).

- Lista completa, con referencias al enunciado: [docs/REQUISITOS.md](docs/REQUISITOS.md).
- Enunciado original: [docs/assessment-en.pdf](docs/assessment-en.pdf).
- Campos y particularidades de las tablas: [docs/DATOS.md](docs/DATOS.md).
- Python 3.12, Git; Docker Desktop con motor Linux activo para la ruta Docker.
- El pipeline actual funciona en Windows con Python y requirements-ingest.lock.txt. Tesseract solo corresponde al ensayo histórico descrito más abajo.
- App Kotlin/Jetpack Compose en mobile/android, Gradle Wrapper incluido. [Ejecución y configuración](docs/ANDROID.md).

## Selección del modelo: comparación medida

**Candidato recomendado: `google/gemini-3.6-flash`.** En la API nativa de Google obtuvo17/18 casos estrictos; Flash Preview también17/18 y Flash-Lite3.5 obtuvo16/18. Elegiría3.6 por fidelidad técnica: su única discrepancia fue el enfoque de presentación de un N/A, mientras Preview añadió60Hz no solicitados y Lite confundió arranques con ciclos. Preview ganó el desempate mecánico por costo/latencia; la preferencia por3.6 es una decisión cualitativa explícita. No se cambiaron puntajes después de observarlos.

El usuario autorizó usar saldo Google tras los402 iniciales. Costo calculado con tokens: aproximadamente USD0,0653; reserva conservadora conjunta incluyendo errores sin consumo informado: USD0,2215, bajo el tope del cliente USD0,50. Hubo503 en varios candidatos; los modelos sin respuestas no reciben precisión cero. No se hicieron inferencias OpenRouter.

[Resultados, trazas y límites](reports/model_eval/RESULTADOS.md), [metodología y reproducción](docs/MODEL_EVALUATION.md). El ensayo usa thinking low, máximo2048tokens y muestreo predeterminado. **Falta alinear la configuración del cliente y validar el endpoint OpenRouter**, además del recorrido completo app→LLM→SQL→app. No se activó automáticamente un modelo de producción.

## Laboratorio OCR: tres motores, sin OpenRouter

Ver [instalación, comparación y ejecución](docs/OCR.md). Notebooks: [comparación](notebooks/01_comparar_ocr.ipynb) y [exploración breve con ydata-profiling](notebooks/02_exploracion_ydata.ipynb).

```powershell
./scripts/setup_ocr.ps1
./.venv-ocr/Scripts/python.exe scripts/run_ocr_notebooks.py
./.venv-ocr/Scripts/python.exe scripts/ocr_lab.py --config config/ocr.json --out data/ocr/nueva-ejecucion
```

El entorno `.venv-ocr` es independiente del backend. Descarga pesos públicos; no usa OpenRouter ni sube el PDF. La configuración elegida, las métricas y las discrepancias históricas se conservan en `config/ocr.json` y `reports/ocr`. El OCR crudo sigue sin validar por sí solo; el catálogo revisado es una salida distinta, con seis correcciones auditadas. Se corrigieron además tres celdas de la referencia inicial al volver al PDF: [evidencia](docs/OCR_REFERENCE_REVIEW.md).

**HTML de ydata-profiling:** abrir [informes de referencia y OCR](reports/ocr/index.html) en un navegador. El notebook 02 también enlaza ambos informes.

## Ensayo original de Tesseract: sin OpenRouter

Los comandos siguientes conservan la prueba inicial con el ejecutable Tesseract. El laboratorio anterior conserva la comparación de motores; para ingestión usar scripts/ingest.py. El servicio Docker `ocr` sigue siendo ese ensayo original; no ejecuta la configuración seleccionada del laboratorio.

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/ocr_probe.py --page 1 --render-only --out data/ocr/page1-render
```

Este comando solo genera una imagen. No realiza OCR ni consume APIs.

### OCR con Docker

Abrir Docker Desktop y esperar a que el motor esté listo. Copiar el ejemplo y configurar una contraseña local para PostgreSQL:

```powershell
Copy-Item .env.example .env
docker compose --profile ocr build ocr
docker compose --profile ocr run --rm --no-deps ocr --page 1 --psm 3 --out data/ocr/page1-psm3
docker compose --profile ocr run --rm --no-deps ocr --page 1 --psm 6 --out data/ocr/page1-psm6
```

No se requiere rellenar OPENROUTER_API_KEY ni elegir un modelo para estos ensayos. La configuración Compose requiere POSTGRES_PASSWORD aunque el servicio OCR no se conecta a PostgreSQL.

### OCR con Tesseract instalado localmente

Consultar la instalación oficial: https://tesseract-ocr.github.io/tessdoc/Installation.html

```powershell
.\.venv\Scripts\python.exe scripts/ocr_probe.py --page 1 --psm 3 --out data/ocr/page1-local
```

Si no está en PATH, añadir `--tesseract-cmd 'C:\Program Files\Tesseract-OCR\tesseract.exe'` con la ruta real. También acepta la variable de proceso TESSERACT_CMD. El script NO carga .env automáticamente: .env es para Compose y como plantilla de configuración futura.

Cada experimento debe usar una carpeta nueva. La herramienta rechaza sobrescribir evidencia. Opciones: --pdf, --page (desde 1), --dpi (72-600), --psm, --out y --render-only.

### Resultados del ensayo

- page.png: imagen utilizada.
- ocr.txt: texto reconocido, solo si se ejecutó OCR.
- ocr.tsv: palabras, coordenadas y confianza, solo si se ejecutó OCR.
- manifest.json: hash del PDF, página, DPI, modo, versiones y estado real.
- engine.log: mensajes del motor, si completó OCR.

El TSV conserva ubicación espacial; todavía falta reconstruir filas, columnas, celdas combinadas y notas. La confianza del motor NO demuestra exactitud. Documentación del formato: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html

## Cómo evaluar la primera tabla

1. Revisar primero la tabla de 110 V de la página 1. El ensayo procesa toda la página y preserva la imagen para inspección.
2. Comparar sus 11 filas con data/reference/serie76_tablas_extraidas.csv, filtrando source_table=p1_t1.
3. Comprobar código completo, cada cifra/unidad, asociación On/Off/modulante y 50/60 Hz.
4. Revisar potencia en celdas combinadas y notas. Ante discrepancias, volver al PDF; la referencia manual también puede contener errores.
5. Registrar fallos antes de elegir motor/configuración. No importar OCR crudo a producción.

El ensayo anterior es histórico. El pipeline actual es scripts/ingest.py; produce CSV/JSON validados. Su carga transaccional PostgreSQL está implementada; ver docs/POSTGRES.md.

## Backend inicial

Local, después de instalar dependencias:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Docker, tras configurar .env:

```powershell
docker compose up --build -d db backend
docker compose ps
docker compose down
```

API local: http://localhost:8000/health. Documentación: http://localhost:8000/docs.
`/health` verifica solo que el proceso responde; no certifica conexión a PostgreSQL ni un agente listo.
Compose mantiene un volumen PostgreSQL persistente. Catálogo, conversaciones y snapshots de respuesta están implementados mediante migraciones. `docker compose down` conserva el volumen; no usar `down -v` si se quieren conservar datos.

La imagen se construye desde Python, siguiendo el enfoque de FastAPI: https://fastapi.tiangolo.com/deployment/docker/

## Conversaciones

POST /api/conversation recibe `query` y un `session_id` opcional. Devuelve `session_id`, `answer`, `message_id` y `products` estructurados. Además incluye tres campos aditivos:

- `clarification`: el campo que falta, opciones o la contradicción detectada.
- `terms`: definiciones literales con su página.
- `assumptions`: palabras del usuario que el agente interpretó como un filtro.

La interpretación necesita OPENROUTER_API_KEY y OPENROUTER_CHAT_MODEL. Sin ellas, la respuesta es 503 con `error_code=not_configured` y el agente no inventa nada. Los errores del proveedor también devuelven 503 con un `error_code` (`timeout`, `rate_limited`, `budget_exhausted`, `provider_unreachable` o `provider_error`) y el turno no se guarda a medias.

**Glosario del resumen:** `python scripts/ingest_summary.py` genera `data/extracted/series76_summary/terms.json`, con 16 definiciones literales, página y sin OCR. Después, `python -m backend.catalog.cli load-context` las carga en `series76.context_terms`. Con Docker: `docker compose exec -T backend python -m backend.catalog.cli load-context`. `/ready` exige el glosario.

GET /api/sessions y GET /api/sessions/{id}/messages permiten listar y reabrir historial. GET /api/messages/{id}/debug solo funciona con DEV_DEBUG=true. [Contrato, paginación, acceso y límites](docs/ANDROID.md).

## Variables

| Variable | Uso |
|---|---|
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | Base local en Compose. Usar contraseña local propia. |
| API_PORT | Puerto local publicado, por defecto 8000. |
| OPENROUTER_API_KEY | Agente conversacional; nunca versionar una clave real. |
| OPENROUTER_BASE_URL | Endpoint OpenAI-compatible del agente. |
| OPENROUTER_CHAT_MODEL | ID configurable. El candidato es google/gemini-3.6-flash, aceptado con el endpoint de Google; falta validarlo en OpenRouter. |
| AGENT_MAX_TOKENS / AGENT_REASONING_EFFORT | 2048 / low, como en la evaluación. La llamada solo emite una tool call (36 tokens de salida de media). |
| AGENT_TOOL_CHOICE | `required` por defecto. Está documentado en OpenRouter y verificado en Google. |
| AGENT_TIMEOUT_S / AGENT_TEMPERATURE | 45 s. Una temperatura vacía usa el muestreo por defecto del proveedor. |
| DEV_DEBUG | false por defecto; habilita las trazas separadas en el backend local. |
| OPENROUTER_EMBEDDING_MODEL | No se usa. Las definiciones salen de un glosario estructurado (ADR 0001). |
| TESSERACT_CMD | Ejecutable local opcional; exportar como variable de proceso o usar argumento. |

## Arquitectura: decisiones y trade-offs

**A+: un agente, una decisión por turno y herramientas deterministas.** Decisión completa en el [ADR 0001](docs/adr/0001-arquitectura-agente.md).

- **LLM.** Interpreta el lenguaje y emite una tool call: `get_actuator`, `search_actuators`, `explain_terms` o `ask_clarification`.
- **Código.** Valida la llamada, fundamenta cada valor en la conversación, fusiona los seguimientos y convierte las contradicciones en preguntas. Después consulta SQL y redacta la respuesta con plantillas.
- **Garantía.** El LLM no escribe cifras ni definiciones. Las cifras salen del PDF eléctrico y las definiciones son citas literales del resumen.
- **Trade-off aceptado.** Las respuestas son menos fluidas que la prosa de un LLM, a cambio de exactitud demostrable.
- **Sin pgvector.** El resumen tiene 348 palabras y 16 definiciones; un glosario estructurado da recall completo y cita exacta. pgvector solo se justificaría con un corpus mayor.
- **Sin multiagente.** Los diseños C/D/E multiplican llamadas y costo. Un revisor del mismo modelo no sustituye la validación determinista. La comparación A–E quedó archivada como inconclusa en el tag `arch-eval-cohort-1`.
- **Evidencia con LLM real:** ver [reports/agent_acceptance](reports/agent_acceptance/RESULTADOS.md). Las pruebas con interpretación simulada (`tests/test_agent_scenarios.py`) validan la capa determinista, no la comprensión lingüística.

Notas de implementación:

- PDF -> extracción -> validación -> PostgreSQL. El resumen aporta contexto; solo el PDF eléctrico aporta cifras.
- get_actuator y search_actuators consultan PostgreSQL y cuentan con wrappers LangChain; código valida argumentos y construye la información técnica desde SQL.
- FastAPI persiste conversaciones y snapshots en PostgreSQL; herramientas y resultados se recuperan aparte para debug.
- Android implementa conversaciones, chat con fichas/tabla y debug mediante source sets debug/release separados.
- OCR: comparar Tesseract, EasyOCR y PP-OCR/RapidOCR localmente, sin gasto de OpenRouter. Ver notebooks, configuración seleccionada y métricas en el laboratorio. La selección no equivale a validar todas las cifras ni las notas.
- Comparación Google completada; candidato recomendado3.6 Flash, con validación OpenRouter pendiente. LangChain y adaptador estándar Chat Completions están implementados; pruebas con interpretación controlada, no con un LLM real. Dependencias de ejecuci?n en requirements.lock.txt.
- Login implementado; voz pendiente.

## App y configuración del asistente

mobile/android contiene el proyecto Android compilable. [docs/ANDROID.md](docs/ANDROID.md) explica SDK, compilación, emulador/dispositivo, URL, debug, patrones, pruebas y límites. La maqueta C fue aprobada antes de programar; las imágenes de diseño no se usan como fondos de la app.

.codex/ contiene la configuración de proyecto de Codex; AGENTS.md define las instrucciones de trabajo. No se copian credenciales ni configuración privada global.

## Reproducibilidad y entrega

Los paquetes directos figuran en requirements.txt y el backend usa requirements.lock.txt. Python/PostgreSQL están fijados por digest; OCR conserva su lock independiente. No se afirma reproducibilidad completa del producto todavía.

Antes de enviar: completar docs/REQUISITOS.md, probar desde un entorno limpio, verificar app/DB/reinicio, seleccionar modelos y documentar costos. Repositorio privado publicado en https://github.com/SamuelCharry/serie76-assistant. Milestones e issues: ver docs/SEGUIMIENTO.md. El envío final y el acceso de evaluadores permanecen pendientes.

### Dependencias y comprobaci?n gratuita de OpenRouter

Backend: `pip install -r requirements.lock.txt` (directas en requirements.txt).
Pruebas: `pip install -r requirements-dev.txt`; OCR: requirements-ingest.txt y
requirements-ingest.lock.txt, independientes. Los locks de experimentos son hist?ricos.

`python scripts/check_openrouter.py --models-only` consulta ?nicamente el cat?logo
p?blico y comprueba tools/tool_choice y precios. Sin ese flag, si existe una clave
en el entorno del proceso, tambi?n consulta GET /api/v1/key; nunca hace inferencia
ni carga claves de .env. OPENROUTER_CHAT_MODEL selecciona el modelo comprobado.

El cliente env?a `provider.require_parameters=true` solo al host openrouter.ai;
OPENROUTER_REQUIRE_PARAMETERS=false permite desactivarlo. Esto exige soporte de
todos los par?metros de la petici?n, seg?n la [documentaci?n de routing](https://openrouter.ai/docs/guides/routing/provider-selection).
AGENT_MAX_CALLS_PER_HOUR=120 limita intentos en una ventana m?vil por proceso;
503/error_code=rate_limited_local permite reintentar despu?s. Reinicios borran la
cuenta y m?ltiples procesos multiplican el l?mite: no es un tope monetario global.

La configuraci?n config/agent_acceptance_openrouter.json fija el candidato y un
cap de USD 1.00. scripts/agent_acceptance.py acepta --config y toma la clave del
entorno: OPENROUTER_API_KEY para OpenRouter, GOOGLE_API_KEY para Google.
Su ejecuci?n pagada sigue pendiente de aprobaci?n expl?cita; no se ha ejecutado.

.claude/ documenta Claude Code como coordinador y .codex/ a Codex como implementador
mediante Orca; no contienen configuraci?n global ni credenciales privadas.
