# Series 76 Technical Assistant
[English](README.md) · [Español](README.es.md)

Una app Android para consultar actuadores Series 76, comparar modelos y retomar conversaciones. El modelo interpreta las preguntas; PostgreSQL aporta los valores técnicos.

## Inicio rápido

1. **Requisitos:** Git, Docker con contenedores Linux; Android Studio, **JDK 17**, SDK Platform 36 y un emulador API 26+ encendido. Ejecuta desde la raíz del repositorio; configura `JAVA_HOME` con JDK 17 y `ANDROID_HOME` con tu SDK Android.
2. **Configurar:** `cp .env.example .env` (Windows: `copy .env.example .env`), solo si no existe `.env`. Pega tu clave OpenRouter en `OPENROUTER_API_KEY` para interpretación de pago; déjala vacía para arrancar sin clave. Para ver detalles de debug local, configura `DEV_DEBUG=true` antes de arrancar.
3. **Arrancar:** `docker compose up -d --build` (ambos sistemas). El arranque carga el catálogo y crea las cuentas TEST ONLY de abajo sin restablecer contraseñas existentes.
4. **Comprobar el arranque:** abre [http://localhost:8000/ready](http://localhost:8000/ready) y espera una respuesta HTTP 200. Esto confirma que la base de datos, el catálogo y el glosario están listos. Para explorar la API, abre [Swagger](http://localhost:8000/docs). La disponibilidad de OpenRouter se comprueba por separado.
5. **Login:** usa cualquiera de estas cuentas públicas **TEST ONLY**:

| Correo | Contraseña pública de prueba |
|---|---|
| demo@series76.test | Series76-Demo-1 |
| reviewer@series76.test | Series76-Demo-2 |

6. **Compilar + instalar en el emulador encendido** (elige tu sistema):
   - macOS/Linux: `sh mobile/android/gradlew -p mobile/android :app:installDebug -PbackendUrl=http://10.0.2.2:8000/`
   - Windows PowerShell: `./mobile/android/gradlew.bat -p mobile/android :app:installDebug -PbackendUrl=http://10.0.2.2:8000/`
   - Abre **Series 76**, inicia sesión y prueba `What is the motor power of 761A00-11300000/A?` (sin clave). El emulador accede al backend en **http://10.0.2.2:8000/**.
7. **Debug:** toca el nombre/correo del perfil **7 veces en 3 segundos** y luego **ⓘ** en una respuesta. Requiere `DEV_DEBUG=true`; si lo cambias después del arranque, aplica con `docker compose up -d backend`.


## Setup y backend

Ejecuta los pasos anteriores desde la raíz del repositorio. Docker carga el catálogo incluido: no necesitas repetir el OCR. Conserva el `.env` y el volumen PostgreSQL existentes. **No ejecutes `docker compose down -v`.**

Sin clave OpenRouter funcionan login, historial y consultas/comparaciones directas. La interpretación libre devuelve `503 not_configured` hasta configurarla. `/ready` comprueba la base y sus datos, no el proveedor del modelo.

La plantilla completa está en [.env.example](.env.example). Las opciones principales son:

- `OPENROUTER_API_KEY`: tu clave para interpretar lenguaje; vacía para probar sin modelo.
- `OPENROUTER_CHAT_MODEL=google/gemini-3.6-flash`; `OPENROUTER_FALLBACK_MODEL=` deja el respaldo desactivado.
- `OPENROUTER_EMBEDDING_MODEL=google/gemini-embedding-2`; `EMBEDDING_DIM=768` debe coincidir con el esquema.
- `DEV_DEBUG=true` habilita el endpoint autenticado de debug.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` y `API_PORT` configuran los servicios locales. Conserva la contraseña de un volumen existente.

Aplica cambios con `docker compose up -d backend`. Para otro checkout aislado o conflictos de puertos, sigue la [guía de operaciones](docs/wiki/es/operations.md). [Peticiones y respuestas de la API](docs/wiki/es/api.md#curl).

## Usuarios demo (TEST ONLY)

Las dos cuentas públicas del inicio rápido son solo para pruebas. Cada una ve sus propias conversaciones. El arranque crea las que falten sin restablecer contraseñas; `DEMO_USERS_JSON=[]` desactiva nuevas cuentas demo.

## Android

Usa **JDK 17**, SDK Platform 36 y un emulador API 26+. Comprueba `java -version` antes de compilar. El emulador accede al equipo en `http://10.0.2.2:8000/`; para otra dirección, compila con `-PbackendUrl=https://tu-host/`. [Configuración del SDK, dispositivos USB y compilación](docs/wiki/es/android.md).

**Debug:** activa `DEV_DEBUG=true`, toca el nombre/correo del perfil siete veces en tres segundos y abre **ⓘ** en una respuesta. Muestra herramientas, parámetros y datos; `llm_called` indica si se usó el modelo.

**Voz:** toca el micrófono, revisa la transcripción y pulsa Send. Android reconoce el audio; este backend no lo recibe. Se prefiere reconocimiento local, pero el servicio alternativo puede usar red. El reconocimiento real se confirmó manualmente en el emulador; falta validación física. [Detalles de voz y debug](mobile/android/README.md).

## Ingestión

Los datos validados están en [data/extracted/series76](data/extracted/series76). Para regenerarlos, usa un entorno Python 3.12 separado y una carpeta de salida nueva:

```sh
# macOS/Linux
python3 -m venv .venv-ingest
. .venv-ingest/bin/activate
pip install -r requirements-ingest.lock.txt
python scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/new-import
```

```powershell
# Windows PowerShell
python -m venv .venv-ingest
.\.venv-ingest\Scripts\Activate.ps1
pip install -r requirements-ingest.lock.txt
python scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/new-import
```

La primera ejecución descarga pesos públicos; después el OCR corre localmente. CSV/JSON/HTML y el manifiesto quedan en una subcarpeta por documento dentro de la salida. Las dudas de extracción bloquean la exportación validada. [Pipeline, validación y carga](docs/wiki/es/ingestion.md).

## Modelos, diseño y límites

Android usa Kotlin/Compose y llama a FastAPI. LangChain toma una decisión de herramienta cuando hace falta interpretar lenguaje; las consultas directas y acciones estructuradas omiten el modelo. El código valida, consulta SQL y construye la respuesta. Así las cifras siguen ligadas al PDF, a cambio de mantener reglas explícitas; aún puede haber errores de interpretación.

Se conservó Flash por el equilibrio de calidad y latencia observado en la [comparación de modelos](docs/wiki/es/testing.md#selección-de-modelo-en-openrouter). No hay modelo de respaldo. pgvector recupera ejemplos de interpretación, no cifras de productos. [Arquitectura](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura) · [Decisiones de diseño](https://github.com/SamuelCharry/serie76-assistant/wiki/Decisiones).

El candidato medido aprobó una media de **79,4 %** de conversaciones frente al **61,1 %** anterior. Las reparaciones posteriores pasaron pruebas offline, sin una nueva medición pagada independiente. El gasto registrado fue **USD 6,17 de 10**, no un saldo actual. [Resultados y límites conocidos](reports/submission/P2-A.md).

## Banco de ejemplos

Los ejemplos semánticos son opcionales y ayudan a interpretar frases. El arranque no genera sus vectores; cargarlos consume crédito del proveedor. [Dry-run, carga y configuración](docs/wiki/es/operations.md#example-bank).

## Pruebas de reproducción

[T18](reports/submission/T18-tag-clean-clone.md) registra la prueba de un clon de `v1.0-submission`: 10/10 pasos, 795 pruebas Python aprobadas con 2 omitidas y 126 pruebas JVM Android aprobadas. Son comprobaciones acotadas, no una garantía para cualquier entrada o dispositivo.

Para ejecutar pruebas locales, prepara primero el [entorno Python](docs/wiki/es/testing.md). Con Compose encendido:

```text
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
python scripts/check_tool_schemas.py
python scripts/verify_catalog_db.py
```

## Mapa del repositorio

[Backend](backend/) · [Android](mobile/android/) · [OCR](catalog_ingest/) · [Pruebas](tests/) · [Configuración del asistente IA](.claude/)

[Wiki](https://github.com/SamuelCharry/serie76-assistant/wiki) · [Checklist del assessment](docs/SUBMISSION.md) · [Enunciado](docs/assessment-en.pdf)
