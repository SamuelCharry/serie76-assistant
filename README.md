# Series 76 Technical Assistant

Continuación en otro agente: [carpeta de contexto](contexto/00_EMPEZAR_AQUI.md).

Repositorio para el assessment de Konecto. **Etapa actual: OCR/PostgreSQL verificados; app Android y conversaciones implementadas. Falta evaluar/configurar el LLM real.**

**Android:** [compilación, ejecución, URL, debug y arquitectura](docs/ANDROID.md). Kotlin/Compose, tres pantallas, diseño claro/lila aprobado; sin Firebase, login ni voz. Hay pruebas de UI en emulador y persistencia HTTP tras reiniciar DB/backend con interpretación controlada. Eso no equivale a validar un modelo real. Evidencia: [reports/mobile](reports/mobile).

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL y consultas técnicas ya están verificados; agente y Android siguen pendientes. Ver docs/POSTGRES.md.

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

Con Docker Desktop activo y una contraseña local propia en .env:

```powershell
docker compose up -d --build db backend
docker compose exec -T backend python -m backend.catalog.cli migrate
docker compose exec -T backend python -m backend.catalog.cli load data/extracted/series76
```

Si .env no existe, copiar .env.example y reemplazar POSTGRES_PASSWORD; no sobrescribir configuración existente. No se requiere OpenRouter. PostgreSQL: 127.0.0.1:5432; backend: 127.0.0.1:8000. Puertos configurables.

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

POST /api/conversation recibe query y session_id opcional; devuelve session_id, answer, message_id y products estructurados. La interpretación necesita OPENROUTER_API_KEY y OPENROUTER_CHAT_MODEL. Sin configuración devuelve 503; no inventa respuestas. El candidato recomendado tras ensayar Google es google/gemini-3.6-flash; su configuración y validación OpenRouter siguen pendientes.

GET /api/sessions y GET /api/sessions/{id}/messages permiten listar y reabrir historial. GET /api/messages/{id}/debug solo funciona con DEV_DEBUG=true. [Contrato, paginación, acceso y límites](docs/ANDROID.md).

## Variables

| Variable | Uso |
|---|---|
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | Base local en Compose. Usar contraseña local propia. |
| API_PORT | Puerto local publicado, por defecto 8000. |
| OPENROUTER_API_KEY | Futuro agente, nunca versionar una clave real. |
| OPENROUTER_BASE_URL | Endpoint OpenRouter del agente futuro. |
| OPENROUTER_CHAT_MODEL | ID configurable; candidato google/gemini-3.6-flash evaluado en Google, pendiente de validación OpenRouter. |
| DEV_DEBUG | false por defecto; habilita las trazas separadas en el backend local. |
| OPENROUTER_EMBEDDING_MODEL | Solo si posteriormente se justifica búsqueda vectorial. |
| TESSERACT_CMD | Ejecutable local opcional; exportar como variable de proceso o usar argumento. |

## Arquitectura prevista y límites

- PDF -> extracción -> validación -> PostgreSQL. El resumen aporta contexto; solo el PDF eléctrico aporta cifras.
- Un agente LangChain interpreta consultas y llama herramientas con parámetros validados.
- Consultas deterministas buscan referencias y filtran requisitos. No se necesita búsqueda vectorial en el primer alcance.
- get_actuator y search_actuators consultan PostgreSQL y cuentan con wrappers LangChain; código valida argumentos y construye la información técnica desde SQL.
- FastAPI persiste conversaciones y snapshots en PostgreSQL; herramientas y resultados se recuperan aparte para debug.
- Android implementa conversaciones, chat con fichas/tabla y debug mediante source sets debug/release separados.
- OCR: comparar Tesseract, EasyOCR y PP-OCR/RapidOCR localmente, sin gasto de OpenRouter. Ver notebooks, configuración seleccionada y métricas en el laboratorio. La selección no equivale a validar todas las cifras ni las notas.
- Comparación Google completada; candidato recomendado3.6 Flash, con validación OpenRouter pendiente. LangChain y adaptador estándar Chat Completions están implementados; pruebas con interpretación controlada, no con un LLM real. Dependencias adicionales en requirements-conversation.lock.txt.
- Login y voz excluidos del primer alcance por ser opcionales.

## App y configuración del asistente

mobile/android contiene el proyecto Android compilable. [docs/ANDROID.md](docs/ANDROID.md) explica SDK, compilación, emulador/dispositivo, URL, debug, patrones, pruebas y límites. La maqueta C fue aprobada antes de programar; las imágenes de diseño no se usan como fondos de la app.

.codex/ contiene la configuración de proyecto de Codex; AGENTS.md define las instrucciones de trabajo. No se copian credenciales ni configuración privada global.

## Reproducibilidad y entrega

Los paquetes directos figuran en requirements.txt y el backend usa requirements-backend.lock.txt. Python/PostgreSQL están fijados por digest; OCR conserva su lock independiente. No se afirma reproducibilidad completa del producto todavía.

Antes de enviar: completar docs/REQUISITOS.md, probar desde un entorno limpio, verificar app/DB/reinicio, seleccionar modelos y documentar costos. Repositorio privado publicado en https://github.com/SamuelCharry/serie76-assistant. Milestones e issues: ver docs/SEGUIMIENTO.md. El envío final y el acceso de evaluadores permanecen pendientes.
