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

Inicia Compose desde el [README](../../../README.es.md); crea y activa un entorno Python 3.12 desde la raíz. Ejecuta solo el bloque de tu shell:

```sh
# macOS/Linux
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
SERIES76_TEST_DB=1 python -m unittest discover -s tests
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
python -m unittest discover -s tests
```

## Conexión PostgreSQL

Las pruebas conectan al servicio Compose `db` por loopback del host `127.0.0.1:5432`, no por hostname Docker `db`. `backend.catalog.cli.local_environment()` lee .env desde la raíz sin mostrarlo: PGHOST predeterminado 127.0.0.1; POSTGRES_PORT → PGPORT (5432), POSTGRES_DB → PGDATABASE (series76), POSTGRES_USER → PGUSER (series76), POSTGRES_PASSWORD → PGPASSWORD. Prevalecen las PG* del proceso. Usa los valores que inicializaron el volumen Compose; cambiar .env no restablece su contraseña. CI define PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD directamente en el workflow. Sin SERIES76_TEST_DB=1 se omiten las pruebas DB.

En el entorno backend activado:

```sh
python scripts/verify_catalog_db.py
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v4.json
```

OCR utiliza otro entorno: sigue la [preparación de ingestión](ingestion.md#reejecutar) y ejecuta con ese entorno OCR activo:

```sh
python -m unittest discover -s tests -p test_dynamic_geometry.py
python -m unittest discover -s tests -p test_pipeline_safety.py
python scripts/verify_ingestion.py
```

Android (Windows; en macOS/Linux sustituye el wrapper .bat por `sh mobile/android/gradlew`):

```powershell
./mobile/android/gradlew.bat -p mobile/android testDebugUnitTest assembleDebug assembleRelease
./mobile/android/gradlew.bat -p mobile/android connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest
```

La instrumentación exige emulador activo. El helper live-auth excluido necesita cuentas de prueba explícitas; ver [`verify_android_auth.py`](../../../scripts/verify_android_auth.py). [`verify_mobile_backend.py`](../../../scripts/verify_mobile_backend.py) prueba HTTP/reinicio controlado; ninguno acredita comprensión del modelo real. Conserva volumen DB. El selfcheck valida expectativas, no calidad del modelo.

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

## Preflight del esquema antes de cualquier cohorte

Ejecutar primero `python scripts/check_tool_schemas.py` sin red. Construye las cuatro herramientas reales sin base de datos ni credenciales e imprime bytes compactos, valores enum, arrays, campos obligatorios, profundidad, restricciones numéricas y arrays de objetos de lookup. Los límites offline para enums/arrays/obligatorios/profundidad son los anteriores a T6 (108/6/5/7); rechaza rangos numéricos, uniones/referencias y arrays de objetos en get_actuator. El tamaño en bytes por sí solo no predijo el límite acumulado del proveedor.

Solo con aprobación explícita de gasto, ejecutar `python scripts/check_tool_schemas.py --live` con OPENROUTER_API_KEY, OPENROUTER_CHAT_MODEL y OPENROUTER_BASE_URL opcional ya en el entorno del proceso. Nunca carga .env ni imprime la clave, la respuesta del proveedor o el cuerpo de errores; envía exactamente una petición con las cuatro herramientas y el prompt/glosario de producción, desactiva trazas, no ejecuta herramientas/SQL y no reintenta. Un 400 u otro fallo devuelve salida no cero: detenerse antes de la cohorte. Un preflight exitoso comprueba aceptación del esquema, no calidad de conversación. Repetir después de cambiar esquemas; la comprobación real del esquema compacto queda pendiente del coordinador.

Dónde: [script de preflight](../../../scripts/check_tool_schemas.py), [pruebas de complejidad y una llamada](../../../tests/test_tool_schema_budget.py), [comprobación solo de metadatos](../../../scripts/check_openrouter.py).
