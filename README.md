# Series 76 Technical Assistant

Continuación en otro agente: [carpeta de contexto](contexto/00_EMPEZAR_AQUI.md).

Repositorio inicial para el assessment de Konecto. **Etapa actual: preparar y validar OCR.**

Implementado: estructura del proyecto, endpoint de salud FastAPI, esquemas mínimos del contrato, configuración Docker/PostgreSQL y ensayo de renderizado/OCR local. Pendiente: extracción tabular validada, ingestión en PostgreSQL, agente LangChain, conversaciones persistentes y aplicación Android.

La existencia de archivos Docker, carpetas o contratos no significa que la aplicación final esté implementada. Estado comprobado en docs/VERIFICACION_INICIAL.md.

## Requisitos y decisiones

- Lista completa, con referencias al enunciado: [docs/REQUISITOS.md](docs/REQUISITOS.md).
- Enunciado original: [docs/assessment-en.pdf](docs/assessment-en.pdf).
- Campos y particularidades de las tablas: [docs/DATOS.md](docs/DATOS.md).
- Python 3.12, Git; Docker Desktop con motor Linux activo para la ruta Docker.
- Para ejecutar OCR directamente en Windows: Tesseract con idioma inglés, además de Python. No hace falta instalarlo en Windows si se usa el servicio Docker OCR.
- Para la app futura: Android Studio. Se elige Kotlin/Jetpack Compose; aún no hay proyecto Android compilable.

## Primer ensayo: sin OpenRouter

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

No existe aún ingest.py: este ensayo no pretende sustituir el pipeline final que deberá leer el PDF, validar tablas y cargar PostgreSQL sin duplicados.

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
Compose mantiene un volumen PostgreSQL persistente. Todavía no hay esquema, ingestión ni almacenamiento de conversaciones. `docker compose down` conserva el volumen; no usar `down -v` si se quieren conservar datos.

La imagen se construye desde Python, siguiendo el enfoque de FastAPI: https://fastapi.tiangolo.com/deployment/docker/

## Contrato de conversación pendiente

POST /api/conversation recibirá query y session_id opcional. Devolverá session_id y answer, más datos de producto y trazas de depuración por definir. Los modelos mínimos están en backend/app/contracts.py; la ruta no está implementada y no devuelve respuestas simuladas.

Listar sesiones y recuperar mensajes será necesario para la app. Los nombres sugeridos del assessment se conservan en la lista de requisitos.

## Variables

| Variable | Uso |
|---|---|
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | Base local en Compose. Usar contraseña local propia. |
| API_PORT | Puerto local publicado, por defecto 8000. |
| OPENROUTER_API_KEY | Futuro agente, nunca versionar una clave real. |
| OPENROUTER_BASE_URL | Endpoint OpenRouter del agente futuro. |
| OPENROUTER_CHAT_MODEL | Modelo futuro configurable, pendiente de evaluación. |
| OPENROUTER_EMBEDDING_MODEL | Solo si posteriormente se justifica búsqueda vectorial. |
| TESSERACT_CMD | Ejecutable local opcional; exportar como variable de proceso o usar argumento. |

## Arquitectura prevista y límites

- PDF -> extracción -> validación -> PostgreSQL. El resumen aporta contexto; solo el PDF eléctrico aporta cifras.
- Un agente LangChain interpreta consultas y llama herramientas con parámetros validados.
- Consultas deterministas buscan referencias y filtran requisitos. No se necesita búsqueda vectorial en el primer alcance.
- Herramientas previstas: get_actuator y search_actuators, todavía no implementadas.
- FastAPI gestionará conversaciones persistentes y respuestas estructuradas.
- Android presentará conversaciones, fichas comparables y depuración de desarrollador.
- Decisión de OCR inicial: Tesseract local, sin gasto de OpenRouter. Su calidad sobre estas tablas aún debe medirse.
- Selección de LLM pendiente; documentar resultados y costo antes de decidir. LangChain y su integración OpenRouter se incorporarán al implementar el agente, no están instalados ni implementados en este scaffold.
- Login y voz excluidos del primer alcance por ser opcionales.

## App y configuración del asistente

mobile/android/README.md registra el trabajo pendiente. Las instrucciones de compilación, URL del backend y acceso a debug se añadirán cuando exista una app real.

.codex/ contiene la configuración de proyecto de Codex; AGENTS.md define las instrucciones de trabajo. No se copian credenciales ni configuración privada global.

## Reproducibilidad y entrega

Los paquetes directos tienen versiones fijadas en requirements.txt; faltan congelar dependencias transitivas e imágenes por digest para la entrega final. No se afirma reproducibilidad completa del producto todavía.

Antes de enviar: completar docs/REQUISITOS.md, probar desde un entorno limpio, verificar app/DB/reinicio, seleccionar modelos y documentar costos. Repositorio privado publicado en https://github.com/SamuelCharry/serie76-assistant. Milestones e issues: ver docs/SEGUIMIENTO.md. El envío final y el acceso de evaluadores permanecen pendientes.
