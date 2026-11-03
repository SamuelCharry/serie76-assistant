# Pruebas

[Wiki](index.md) · [English](../en/testing.md) · [Español](../es/testing.md)

Qué prueba cada suite y qué necesita todavía aceptación con proveedor real.

Un modelo programado devuelve herramientas predeterminadas; las herramientas reales ejecutan validación, SQL y renderizado. Prueba comportamiento determinista y persistencia, no comprensión del lenguaje. Las cohortes reales prueban interpretación aparte. Ningún comando siguiente autoriza inferencia pagada.

- [test_reviewed_catalog.py](../../../tests/test_reviewed_catalog.py): Referencia manual y correcciones exactas, solo evaluación.
- [test_dynamic_geometry.py](../../../tests/test_dynamic_geometry.py): Filas nuevas, desplazamientos y reconstrucción de tablas.
- [test_pipeline_safety.py](../../../tests/test_pipeline_safety.py): Aislamiento de fallos, integridad, bloqueo de referencia/red e ingestión acotada.
- [test_catalog_db.py](../../../tests/test_catalog_db.py): Filtros SQL reales, alcance de mediciones, procedencia y cargas.
- [test_agent_policy.py](../../../tests/test_agent_policy.py): Fundamentación, códigos, contradicciones y fusión de filtros.
- [test_agent_scenarios.py](../../../tests/test_agent_scenarios.py): Ejecución de herramientas con decisiones programadas y catálogo real.
- [test_conversations.py](../../../tests/test_conversations.py): Contrato API, rollback, instantáneas e historial.
- [test_auth.py](../../../tests/test_auth.py): Autenticación con hash, revocación, aislamiento y contrato de login.
- [test_submission_readiness.py](../../../tests/test_submission_readiness.py): require_parameters, guarda por proceso y cuentas demo idempotentes.

## Ejecutar localmente

Inicia Compose primero. Crea un entorno Python 3.12 e instala `requirements-dev.txt`; OCR requiere aparte `requirements-ingest.lock.txt`. Estos comandos usan el entorno local de verificación; créalo en un checkout nuevo:

```sh
python -m venv .venv-model-eval
# macOS/Linux
.venv-model-eval/bin/python -m pip install -r requirements-dev.txt
SERIES76_TEST_DB=1 .venv-model-eval/bin/python -m unittest discover -s tests
# Windows PowerShell
.venv-model-eval/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
```
Para completar los controles OCR locales instala también el runtime de [ingestión](ingestion.md); ejecuta sus dos suites y verificadores. En macOS/Linux sustituye las rutas Windows siguientes por `.venv-ingest/bin/python`.

```powershell
.venv-ingest/Scripts/python.exe -m unittest discover -s tests -p test_dynamic_geometry.py
.venv-ingest/Scripts/python.exe -m unittest discover -s tests -p test_pipeline_safety.py
.venv-ingest/Scripts/python.exe scripts/verify_ingestion.py
.venv-model-eval/Scripts/python.exe scripts/verify_catalog_db.py
.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v4.json
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
./mobile/android/gradlew.bat -p mobile/android connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest
```
En macOS/Linux usa `sh mobile/android/gradlew` en vez del wrapper .bat. Instrumentación exige emulador; el helper live auth excluido necesita backend/cuentas preparados. [`scripts/verify_android_auth.py`](../../../scripts/verify_android_auth.py) y [`scripts/verify_mobile_backend.py`](../../../scripts/verify_mobile_backend.py) prueban HTTP/reinicio con interpretación controlada y crean registros de verificación; no prueban LLM real. Conserva el volumen PostgreSQL. Sin SERIES76_TEST_DB=1 las pruebas DB se omiten explícitamente. El selfcheck valida expectativas, no calidad del modelo.

## Evidencia de modelo real

[Cohortes v1–v4](../../evidence/agent_acceptance.md), cliente A+ de producción sobre API Google compatible con OpenAI, cero llamadas OpenRouter:

| Cohorte | Aprobados/escenarios | Fallos de calidad | Fallos solo de proveedor |
|---|---:|---:|---:|
| v1 | 25/27 | 2 | 0 |
| v2 | 38/43 | 2 | 3 |
| v3 | 46/51 | 3 | 2 |
| v4 | 50/55 | 1 | 4 |

Las cohortes se solapan: no sumarlas como muestras independientes. La corrección del límite estricto v4 no se revalidó con modelo real; cuatro casos quedaron sin evaluar por proveedor. La selección inicial Google nativa usó otro corpus congelado y la [comparación histórica](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval). Sugirió Gemini 3.6 Flash por fidelidad técnica cualitativa; no valida disponibilidad, precio ni routing actuales.

Método: congelar hashes de corpus/código/configuración/catálogo antes de inferencia; excluir expectativas del prompt; evaluar herramienta/argumentos, filtros extra, hechos SQL y aclaraciones autorizadas. Separar tokens, latencia y fallos de proveedor. Reservar presupuesto antes de llamadas, conservar reserva si falta uso, usar un controlador y no reintentar automáticamente. Restaurar experimentos archivados en otro checkout para reproducir; inferencia pagada exige aprobación. La [comparación A–E](../../evidence/architecture_comparison.md) es inconclusa, no un ranking.

## CI

El [workflow CI](../../../.github/workflows/ci.yml) prepara PostgreSQL, instala dependencias dev, migra, carga catálogo/glosario y ejecuta unittest; Android ejecuta pruebas JVM con JDK 17. No hace inferencia pagada, OCR completo ni instrumentación con emulador. Tener workflow demuestra implementación, no la última ejecución remota. Esta tarea solo corre controles locales.

## Dónde está en el código

- [tests/test_agent_scenarios.py](../../../tests/test_agent_scenarios.py#L1)
- [scripts/agent_acceptance.py](../../../scripts/agent_acceptance.py#L1)
- [scripts/verify_ingestion.py](../../../scripts/verify_ingestion.py#L1)

## Límites conocidos

Ninguna prueba automática acredita lenguaje arbitrario ni precisión OCR heterogénea. Las pruebas DB pueden crear registros acotados o revertir transacciones. Aceptación OpenRouter y recorrido Android → modelo real → SQL → Android pendientes.
