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

## Behavior evaluation

Las rondas T8/T9 usan conjuntos retenidos congelados antes de leer respuestas, seis personas y revisión estricta independiente por conversación completa. La tabla y comparación de modelos fueron suministradas por el coordinador para esta entrega; los informes enlazados documentan las reparaciones y verificaciones locales posteriores. No confundir sus replays scripted con nuevas mediciones del proveedor.

Las rondas se solapan en el método, pero no en las conversaciones. Rondas 1–2 usaron una revisión más laxa y no se mezclan con esta tabla. ON/OFF compara los mismos casos dentro de cada ronda; cambiar de ronda cambia el conjunto y no aísla causalmente una mejora de código. La revisión estricta considera interpretación, conservación/cobertura de requisitos, seguridad del contexto y utilidad de la respuesta, además de las cifras.

| Round | Config | Strict pass |
|---|---|---|
| 3 | rules | 21/45 (47 %) |
| 4 | rules | 24/45 (53 %) |
| 5 | rules | 21/44 (48 %) |
| 6 | rules | 28/43 (65 %) |
| 7 | rules | 24/43 (56 %) |
| 8 | ON / OFF | 25/41 (61 %) / 26/41 (63 %) |
| 9 | ON / OFF | 30/41 (73 %) / 29/41 (71 %) |
| 10 | retrieval ON, after round-9 fixes | 28/41 (68 %) |

Ronda 9 deja una diferencia de **una conversación** (73 % frente a 71 %); ronda 8 favoreció OFF. Ronda 10, con retrieval ON después de las reparaciones de ronda 9, obtuvo **28/41 (68 %)**. Por tanto, la calidad observada en conversaciones inéditas retenidas es **68–73 % estricto (rondas 9–10)**, no una mejora causal demostrada ni superioridad estadística de embeddings. Todas las respuestas de esas dos rondas estuvieron bajo **10 s**, con **p95 3.7–5.1 s**. Según la revisión del coordinador, no hubo cifras de catálogo incorrectas en ninguna ronda.

Persisten cuatro clases de fallo: señales parafraseadas o españolas de servicio/cerramiento omitidas que se convierten en aclaraciones; retractaciones o límites añadidos a mitad de conversación que a veces no se fusionan; juicio de peligro con errores en ambos sentidos, por lo que se solicita confirmación y siempre se muestra el cerramiento; y exceso de detalle ante preguntas de un campo o fuera de alcance. El ingeniero debe confirmar **filtros activos, servicio, cerramiento y clasificación del área peligrosa antes de ordenar**. El informe T9 registra 6/7 fallos de integridad ON/OFF en ronda 9: integridad incluye requisitos/selección, no solo cifras. La ronda 10 es evidencia en vivo posterior a las reparaciones; OpenRouter sigue pendiente y las pruebas offline no amplían esa aceptación.


### Selección de modelos

Cliente compatible OpenAI, medido a través de Google; OpenRouter es el destino de entrega pendiente. En las mismas **44 conversaciones**, `gemini-3.6-flash` obtuvo **21/44**, `gemini-3.8-flash` **25/44** y `gemini-3.1-pro` **28/44**. Pro tuvo **p95 7.1 s**, incluido un turno de **11 s**. Después de ronda 6 se mantuvo 3.6 Flash: **28/43** frente a **26/43** de 3.8 Flash. Es una decisión calidad/latencia en estos conjuntos, no un ranking universal. Embeddings usan `gemini-embedding-2`; ID de OpenRouter `google/gemini-embedding-2`, con compatibilidad en vivo pendiente.

### Procedencia y fuga de evaluación

El banco v7 guarda frases/interpretaciones y todos los IDs de origen, nunca las respuestas evaluadas ni cifras del catálogo como conocimiento. Usa un conjunto nuevo o `EMBEDDING_EXCLUDE_SOURCES` para excluir todas las asociaciones de casos retenidos antes de distancia/LIMIT. Las versiones/manifiestos inmutables impiden sustituir silenciosamente etiquetas; los conflictos se desactivan y la procedencia histórica se conserva. Al incorporar un caso fallido al replay/banco, pasa a ser regresión/calibración: no vuelve a contarse como aceptación inédita. El replay de ronda 9 conserva consultas/decisiones y hashes, no está cargado en el banco. [Detalle T9](../../../reports/submission/T9-embeddings.md).

### Evidencia local vigente

[T8](../../../reports/submission/T8-backend.md), [T8b](../../../reports/submission/T8b-backend.md), [T8c](../../../reports/submission/T8c-backend.md), [T8d](../../../reports/submission/T8d-backend.md), [T8e](../../../reports/submission/T8e-backend.md), [T8f](../../../reports/submission/T8f-backend.md), [T8g](../../../reports/submission/T8g-backend.md) y [T8h](../../../reports/submission/T8h-backend.md) documentan la evolución determinista, no una aprobación acumulada del modelo.

[T9 embeddings](../../../reports/submission/T9-embeddings.md): **484 pruebas Python, 2 omisiones opcionales; 446 escenarios scripted sin fallos**, replay de 41 conversaciones por modo/138 turnos totales, SQL local, esquema y scanner. [T8 Android](../../../reports/submission/T8-android.md): 51 JVM; [T9 Android](../../../reports/submission/T9-android.md): **74 JVM y APK debug/release**, sin dispositivo ni voz real. Son resultados de esos informes, no suites reejecutadas por la tarea documental. Las secciones T7/v6 siguientes son históricas; sus cohortes sí pueden solaparse y no se suman a T8/T9.


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

Gate offline vigente: **v7, 453/453 escenarios programados**. En el entorno Python backend activado, después de iniciar Compose:

```text
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
python scripts/check_tool_schemas.py
python scripts/verify_catalog_db.py
```

Los siete escenarios T9-R1 cubren recomendaciones después de comparaciones y listas visibles, requisitos nuevos, intención en español, empates y ningún modelo admisible. El [informe de recomendaciones](../../../reports/submission/T9-R1-recommendation.md) conserva las tres respuestas completas; las [regresiones](../../../tests/test_shown_recommendation.py) comprueban el texto exacto y rechazan ganadores inválidos o no mostrados. El replay comprueba el cumplimiento mediante el CSV validado, independientemente del ordenamiento SQL.

El verificador del catálogo inicia sesión con la cuenta demo pública TEST ONLY y envía su token Bearer a las rutas protegidas. Usa `http://127.0.0.1:${API_PORT:-8000}`, priorizando `API_PORT` del proceso sobre la configuración local; `--base-url http://127.0.0.1:18000` lo sustituye explícitamente. SQL, suite completa con DB y HTTP deben aprobar para salir con 0. Nunca restablece contraseñas demo existentes.

El selfcheck v6 es histórico: sus expectativas de presentación son anteriores a T8 y ya no aprueba esta versión. Se conservan sus archivos y el resultado archivado 103/103; no son el gate vigente. Las pruebas programadas no acreditan calidad de interpretación del proveedor.

## Conexión PostgreSQL

Las pruebas conectan al servicio Compose `db` por loopback del host `127.0.0.1:5432`, no por hostname Docker `db`. `backend.catalog.cli.local_environment()` lee .env desde la raíz sin mostrarlo: PGHOST predeterminado 127.0.0.1; POSTGRES_PORT → PGPORT (5432), POSTGRES_DB → PGDATABASE (series76), POSTGRES_USER → PGUSER (series76), POSTGRES_PASSWORD → PGPASSWORD. Prevalecen las PG* del proceso. Usa los valores que inicializaron el volumen Compose; cambiar .env no restablece su contraseña. CI define PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD directamente en el workflow. Sin SERIES76_TEST_DB=1 se omiten las pruebas DB.

En el entorno backend activado:

```sh
python scripts/verify_catalog_db.py
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
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

## Aceptación offline T7 / v6

Sección histórica: las expectativas de presentación v6 son anteriores a T8 y ya no aprueban esta versión; ejecuta v7 arriba. Los casos y la configuración v6 permanecen intactos.

[Casos v6](../../../config/agent_acceptance_cases_v6.json) conserva los 63 escenarios v5 y añade los 40 EC de la [especificación de casos límite](../../evaluation/edge-case-suite.es.md). Los archivos históricos v5 no cambian; v6 registra cambios aprobados de presentación y políticas exploratorias. Las expectativas usan el CSV validado; las decisiones controladas no entran al prompt del modelo real.

[Evidencia backend](../../../reports/submission/T7-backend.md): 202 pruebas Python, 2 omisiones de módulos opcionales OCR/geometría; 103/103 escenarios selfcheck; seis mutaciones; reconstrucción sin claves y `/ready` 200. [Evidencia Android](../../../reports/submission/T7-android.md): 40 pruebas JVM y APK debug compilado, sin aceptación visual en dispositivo. Son resultados registrados por los workers, no una afirmación de que esta edición documental repitió esas suites.

Con PostgreSQL activo y el entorno Python backend preparado:

```sh
python -m unittest discover -s tests -p test_acceptance_v6.py -v
python scripts/check_tool_schemas.py
```

El oráculo CSV independiente comprueba valores, N/A, ámbitos, candidatos completos, unidades/ganadores y contrato público. Las mutaciones primero aceptan un resultado válido y después exigen fallo ante `gt → gte`, N/A → cero, unidad incorrecta, requisito eliminado, código sustituido (aunque tenga igual valor numérico) y pérdida del límite superior. Prueban detección de esos fallos concretos; no detección universal ni comprensión del modelo. [Evaluador](../../../scripts/acceptance_contract.py), [mutaciones](../../../tests/test_acceptance_v6.py), [ejemplos capturados](../../../reports/submission/T7-scenarios.json).

Antes de una cohorte real, ejecutar el control offline del esquema; solo con autorización explícita de gasto ejecutar el preflight real de una llamada. Congelar código/casos/catálogo/configuración, contar cada intento de transporte en el ledger y separar fallo de proveedor de fallo semántico. El tope USD 1,00 de v6 no autoriza gastar. Los retries productivos tienen plazo compartido; el preflight de esquema nunca reintenta.

**Resultado v6 con modelo real (coordinador, Google `gemini-3.6-flash`, 2026-11-03):** 102/103 escenarios aprobados tras las correcciones, en las cohortes `v6` (los 103: 88 aprobados, 9 fallos, 6 solo de proveedor), `v6b` (15 repeticiones tras corregir código: 10 aprobados) y `v6c` (4 repeticiones: 4 aprobados). Queda `t6_manual_03`, una diferencia de interpretación aceptada (una búsqueda nueva para exteriores después de "at least 70 Nm" se leyó como refinamiento que conserva 70 Nm y pregunta el servicio). Fallos de integridad (cifras, unidades, N/A, operadores, códigos): 0. Coste por uso: USD 0,1837 (v6 + v6b + v6c); llamadas a OpenRouter: 0. Cada repetición real usó una cohorte nueva; nunca se editaron resultados registrados. Evidencia: `reports/agent_acceptance/v6*/summary.json` (local, ignorado por git) y [T7-v6-repair.md](../../../reports/submission/T7-v6-repair.md), [T7-v6b-repair.md](../../../reports/submission/T7-v6b-repair.md).

## Evidencia de modelo real

[Cohortes v1–v4](../../evidence/agent_acceptance.md), cliente A+ de producción sobre API Google compatible con OpenAI, cero llamadas OpenRouter:

| Cohorte | Aprobados/escenarios | Fallos de calidad | Fallos solo de proveedor |
|---|---:|---:|---:|
| v1 | 25/27 | 2 | 0 |
| v2 | 38/43 | 2 | 3 |
| v3 | 46/51 | 3 | 2 |
| v4 | 50/55 | 1 | 4 |

Las cohortes se solapan: no sumarlas como muestras independientes. La corrección del límite estricto v4 no se revalidó con modelo real; cuatro casos quedaron sin evaluar por proveedor. La selección inicial Google nativa usó otro corpus congelado y la [comparación histórica](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/model_eval). Sugirió Gemini 3.6 Flash por fidelidad técnica cualitativa; no valida disponibilidad, precio ni routing actuales.

Método: congelar hashes de corpus/código/configuración/catálogo antes de inferencia; excluir expectativas del prompt; evaluar herramienta/argumentos, filtros extra, hechos SQL y aclaraciones autorizadas. Separar tokens, latencia y fallos de proveedor. Reservar presupuesto antes de llamadas, conservar reserva si falta uso y usar un controlador. La configuración histórica no es la política de retries de transporte T7. Restaurar experimentos archivados en otro checkout para reproducir; inferencia pagada exige aprobación. La [comparación A–E](../../evidence/architecture_comparison.md) es inconclusa, no un ranking.

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
