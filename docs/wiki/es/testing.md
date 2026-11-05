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


### Vista por turno y uso cotidiano

Un revisor independiente volvió a puntuar la ronda 10 (`gemini-3.6-flash`, recuperación ON): las mismas 41 conversaciones inéditas, con 68 turnos. Son resultados suministrados de otra revisión de las respuestas registradas, no una nueva ejecución del proveedor; los intervalos siguientes son Wilson del 95%.

| Medida | Resultado | Intervalo/límite Wilson 95% |
|---|---:|---:|
| Turnos correctos | 56/68 = 82,4% | 71,6–89,6% |
| Fallos de integridad | 7/68 = 10,3% | 5,1–19,8% |
| Fallos de forma | 4/68 = 5,9% | No suministrado |
| Fallos de memoria | 1/68 = 1,5% | No suministrado |
| Conversaciones TÍPICAS completamente correctas | 18/19 = 94,7% | 75,4–99,1% |
| Conversaciones ADVERSARIALES completamente correctas | 12/22 = 54,5% | 34,7–73,1% |
| Cifras de catálogo incorrectas | 0/491 valores comprobados | Error ≤0,78%; exactitud ≥99,2% |

**TÍPICA** significa una consulta por código o su seguimiento, un requisito claro en términos del catálogo (se permiten abreviaturas), una comparación o recomendación, o una corrección simple. **ADVERSARIAL** significa un requisito expresado solo mediante paráfrasis, con errores ortográficos o mezcla de idiomas, un juicio implícito de peligro o de sitio seguro, una petición fuera de alcance o una inyección, una solicitud de reformulación o una retractación durante la conversación.

Todos los fallos de integridad fueron restricciones no aplicadas, nunca cifras incorrectas; cinco de siete correspondieron a servicio expresado mediante paráfrasis o en español. Todas las respuestas tardaron menos de 10 s, con un máximo de **5,03 s**. El límite de exactitud numérica usa los supuestos de muestreo de la revisión; no garantiza resultados en conversaciones nuevas.

La revisión por turno aceptó algunos casos dudosos y obtuvo **30/41 conversaciones**, frente al resultado anterior más estricto de **28/41 (68,3%)**; se conservan ambos porque cambia el criterio de puntuación.

### Selección de modelos

Cliente compatible OpenAI, medido a través de Google; OpenRouter es el destino de entrega pendiente. En las mismas **44 conversaciones**, `gemini-3.6-flash` obtuvo **21/44**, `gemini-3.8-flash` **25/44** y `gemini-3.1-pro` **28/44**. Pro tuvo **p95 7.1 s**, incluido un turno de **11 s**. Después de ronda 6 se mantuvo 3.6 Flash: **28/43** frente a **26/43** de 3.8 Flash. Es una decisión calidad/latencia en estos conjuntos, no un ranking universal. Embeddings usan `gemini-embedding-2`; ID de OpenRouter `google/gemini-embedding-2`, con compatibilidad en vivo pendiente.

### Procedencia y fuga de evaluación

El banco v7 guarda frases/interpretaciones y todos los IDs de origen, nunca las respuestas evaluadas ni cifras del catálogo como conocimiento. Usa un conjunto nuevo o `EMBEDDING_EXCLUDE_SOURCES` para excluir todas las asociaciones de casos retenidos antes de distancia/LIMIT. Las versiones/manifiestos inmutables impiden sustituir silenciosamente etiquetas; los conflictos se desactivan y la procedencia histórica se conserva. Al incorporar un caso fallido al replay/banco, pasa a ser regresión/calibración: no vuelve a contarse como aceptación inédita. El replay de ronda 9 conserva consultas/decisiones y hashes, no está cargado en el banco. [Detalle T9](../../../reports/submission/T9-embeddings.md).

### Evidencia local vigente

[T8](../../../reports/submission/T8-backend.md), [T8b](../../../reports/submission/T8b-backend.md), [T8c](../../../reports/submission/T8c-backend.md), [T8d](../../../reports/submission/T8d-backend.md), [T8e](../../../reports/submission/T8e-backend.md), [T8f](../../../reports/submission/T8f-backend.md), [T8g](../../../reports/submission/T8g-backend.md) y [T8h](../../../reports/submission/T8h-backend.md) documentan la evolución determinista, no una aprobación acumulada del modelo.

[T9 embeddings](../../../reports/submission/T9-embeddings.md): **484 pruebas Python, 2 omisiones opcionales; 446 escenarios scripted sin fallos**, replay de 41 conversaciones por modo/138 turnos totales, SQL local, esquema y scanner. [T8 Android](../../../reports/submission/T8-android.md): 51 JVM; [T9 Android](../../../reports/submission/T9-android.md): **74 JVM y APK debug/release**, sin dispositivo ni voz real. Son resultados de esos informes, no suites reejecutadas por la tarea documental. Las secciones T7/v6 siguientes son históricas; sus cohortes sí pueden solaparse y no se suman a T8/T9.


## Cómo sabemos si una diferencia es real

Un intervalo bootstrap del 95% describe la variación al remuestrear estas conversaciones; no cubre sesgos del evaluador ni garantiza resultados en otros dominios.
McNemar compara aprobaciones/fallos pareados: **solo cuentan las conversaciones donde las dos configuraciones discrepan**.
Remuestreamos conversaciones completas 10.000 veces con semilla 20261104, intervalos percentiles y McNemar exacto bilateral.

| Configuración | Aprobación estricta | IC95% | p de McNemar pareado |
|---|---:|---:|---:|
| Ronda 9 recuperación ON | 30/41 (73,2%) | 58,5–85,4% | 1,000 vs OFF |
| Ronda 9 recuperación OFF | 29/41 (70,7%) | 56,1–82,9% | misma comparación |
| Ronda 10 Flash | 28/41 (68,3%) | 53,7–82,9% | 1,000 vs Pro |
| Ronda 10 Pro | 28/41 (68,3%) | 53,7–82,9% | misma comparación |

ON/OFF tiene 2 frente a 1 pares discordantes; ON−OFF es +2,44 puntos porcentuales (IC95% −4,9 a +12,2). Flash/Pro tiene 3 frente a 3; Flash−Pro es 0 puntos (−12,2 a +12,2).
La conclusión honesta es **cerca del 70% de aprobación estricta**, con incertidumbre amplia: ninguna comparación se distingue estadísticamente con n=41; eso no demuestra equivalencia. Flash se elige por la gran ventaja de latencia observada, p95 de unos **4 s frente a 7,4 s** (observaciones suministradas por el coordinador, no una prueba estadística de latencia).
Con n=41, seis discrepancias todas a favor de una configuración y acuerdo en los demás casos dan p=0,03125; cinco dan p=0,0625. Es el mínimo favorable de discordancias, no un cálculo de potencia/tamaño muestral.
[Script y resultados de todas las rondas](../../../reports/submission/T9-S1-stats.md); [veredictos](../../../reports/behavior/verdicts.json), [JSON estadístico](../../../reports/behavior/stats.json). Rondas 3–8 tienen solo intervalos agregados; no inventamos parejas ni sumamos rondas.

### Diagnóstico del recuperador

Leave-one-out sobre **649 ejemplos activos almacenados**, sin embeddings nuevos, excluyendo el propio ejemplo y texto idéntico. Relevancia exige igual herramienta, servicio, carcasa, voltaje y operadores de torque, incluidos campos ausentes; magnitudes/unidades del torque y códigos/términos de otras herramientas quedan fuera de esta métrica de patrones. P@k divide vecinos relevantes entre k (huecos cuentan como fallo); MRR@5 promedia 1/posición del primer relevante, o cero. Cobertura significa recibir algún ejemplo, no necesariamente relevante.

| Corte de coseno | P@1 | P@3 | P@5 | MRR@5 | Cobertura |
|---|---:|---:|---:|---:|---:|
| Ninguno | 47,6% | 41,1% | 38,2% | 0,563 | 100% |
| Actual 0,70 | 47,0% | 39,3% | 35,6% | 0,551 | 98,3% |

Sin corte, MRR sube 0,476/0,546/0,563/0,570 con k=1/3/5/8: k=5 limita contexto con ganancias decrecientes, pero no es un óptimo demostrado. Con 0,70, la precisión entre vecinos devueltos sigue en 38,2%; esta muestra **no justifica** el umbral como filtro de relevancia. El [barrido completo](../../../reports/behavior/retrieval.json) muestra el coste en cobertura. Quince consultas no tienen par relevante; pueden quedar paráfrasis relacionadas entre conjuntos y estas etiquetas no certifican recomendaciones correctas. Validar con consultas nuevas antes de ajustar; no se cambiaron parámetros de producción.

### Mejorar la recuperación

Comparamos cinco enfoques sobre el mismo banco de 649 ejemplos, dejando fuera cada consulta. **Estricto** exige igual herramienta, servicio, carcasa, voltaje y operadores de torque; **útil para el prompt** exige igual herramienta y conjunto de campos no nulos, manteniendo servicio/carcasa aunque cambien otros valores. Una semilla fija separa 129 consultas para ajustar y 520 para validar dentro del banco; no son conversaciones inéditas.

| Variante | Estricto P@1 / P@3 / P@5 | Estricto MRR@5 | Útil P@1 / P@3 / P@5 | Útil MRR@5 | ms extra/consulta | Llamadas API extra |
|---|---|---:|---|---:|---:|---:|
| A: denso | 47,6 / 41,1 / 38,2% | 0,563 | 47,5 / 41,2 / 37,8% | 0,554 | 0 | 0 |
| B: metadatos, w=0,02 | 51,8 / 43,4 / 40,1% | 0,598 | 47,5 / 40,8 / 37,8% | 0,552 | 0,42 | 0 |
| C: BM25 + denso, RRF 60 | 48,5 / 41,2 / 38,1% | 0,572 | 44,1 / 38,1 / 35,6% | 0,534 | 6,77 | 0 |
| D: MMR sobre A, λ=0,6 | 47,6 / 41,0 / 38,3% | 0,565 | 47,5 / 41,1 / 37,9% | 0,556 | 0,32 | 0 |
| E: cantidades enmascaradas | 43,0 / 40,1 / 37,5% | 0,524 | 48,1 / 43,1 / 39,2% | 0,557 | 0,01 | 0 |
| E + B, w=0,02 | 49,8 / 42,5 / 39,1% | 0,572 | 48,7 / 42,9 / 39,0% | 0,558 | 0,34 | 0 |

Todas las precisiones son porcentajes; no hay corte de coseno, igual que en el baseline original. Los tiempos miden sobrecoste local de ranking/enmascarado, sin DB ni proveedor; cero llamadas extra significa reutilizar/sustituir el embedding de consulta existente, no un servicio gratuito. Barridos: w=0,02/0,05/0,1/0,2/0,4 y λ=0,5–0,9. **Se mantiene denso:** ninguna variante gana los 5 puntos exigidos de P@5 útil y mejora también P@5 estricto; la mejor ganancia útil es solo 1,4 puntos y empeora precisión estricta. La partición de validación lleva a la misma decisión. No cambió ningún valor predeterminado y el banco enmascarado queda inactivo; el replay v7 programado con recuperación SQL densa real conserva en ON todos los filtros de OFF. [Experimento, límites y registro de uso Google](../../../reports/submission/T9-S2-retrieval.md).

### Impacto y por qué la integridad va primero

La idea de valor esperado de Provost pondera beneficio/coste de cada resultado por su probabilidad, en lugar de tratar todos los errores igual. Estas son **suposiciones ilustrativas en unidades relativas**, no dinero medido ni valores aprobados por el cliente; el cliente fija los costes reales y no hemos estimado retorno económico.

| Resultado | Beneficio/coste relativo ilustrativo | Motivo |
|---|---:|---|
| Recomendación correcta | +1 | Ahorra al ingeniero una búsqueda manual en tablas |
| Pregunta de aclaración | −0,1 | Pequeño coste de interacción adicional |
| Error de integridad: carcasa o servicio incorrecto | −100 | Selección equivocada potencialmente muy costosa |

La utilidad esperada sería `P(correcta) × 1 − P(aclaración) × 0,1 − P(error de integridad) × 100`; la aprobación estricta no estima esas probabilidades por separado. Por eso el diseño sacrifica algo de comodidad a cambio de verificación y confirmación.

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
