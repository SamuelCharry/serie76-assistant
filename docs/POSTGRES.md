# Catálogo PostgreSQL y consultas deterministas

Este bloque implementa almacenamiento y consultas técnicas. No incluye todavía agente LangChain, modelos OpenRouter, conversaciones persistentes ni Android. El PDF eléctrico sigue siendo la única fuente de cifras. El resumen explica conceptos como servicio, recorrido, FLA/LRA y potencia del motor; no rellena mediciones ausentes.

## Arranque reproducible con Docker

Requisitos: Docker Desktop con contenedores Linux, Git y este repositorio completo. Las imágenes base Python y PostgreSQL 17 están fijadas por digest; las dependencias del backend están congeladas en requirements-backend.lock.txt.

Desde la raíz, PowerShell:

```powershell
Copy-Item .env.example .env
# Editar POSTGRES_PASSWORD: reemplazar el placeholder por una contraseña local propia.
docker compose up -d --build db backend
docker compose exec -T backend python -m backend.catalog.cli migrate
docker compose exec -T backend python -m backend.catalog.cli load data/extracted/series76
docker compose exec -T backend python -m backend.catalog.cli status
```

No sobrescribir un .env existente. Este archivo está ignorado por Git. La ejecución de desarrollo creó uno local con contraseña aleatoria; no se guarda ni muestra en informes. No hace falta configurar OpenRouter. El CLI dentro de Docker utiliza las variables PG* de Compose; en Windows carga únicamente la configuración de conexión de .env, y las variables del proceso tienen prioridad. DATABASE_URL puede proporcionar una conexión explícita; no se imprime.

PostgreSQL se publica únicamente en 127.0.0.1:5432 y el backend en 127.0.0.1:8000. POSTGRES_PORT y API_PORT permiten cambiar esos puertos. Si se cambia la contraseña en .env tras inicializar un volumen, PostgreSQL no cambia automáticamente la contraseña de su usuario: debe administrarse explícitamente, sin borrar datos.

Los datos persisten en el volumen del proyecto. `docker compose restart db backend` conserva el catálogo. No usar down -v para reiniciar. No se requieren otros servicios ni pgvector.

## Del PDF al catálogo consultado

El directorio data/extracted/series76 contiene una salida real OCR ya validada. Para generar otra, seguir docs/INGESTION.md y pasar su directorio al comando load. El backend no instala el motor OCR ni lee referencias manuales.

Antes de escribir en PostgreSQL, el cargador comprueba:

- Manifest ready, cero incidencias/notas pendientes, values_from_ocr=true y reference_values_loaded=false.
- Hash del PDF eléctrico original y todos los artefactos; cola de revisión vacía y esquema compatible.
- Coherencia entre valores, estados, tabla, fila y evidencia de cada celda, incluidas identidades con asterisco.

La carga y la activación ocurren dentro de una transacción, con bloqueo asesor para serializar importaciones. Un error revierte toda la versión nueva. Las secuencias de PostgreSQL pueden dejar huecos de ID después de un rollback; eso no implica filas parciales.

Una misma pareja SHA del PDF/firma del pipeline es una versión: repetirla con los mismos hashes devuelve already_loaded. Cambiar sus artefactos conservando esa identidad se rechaza. Una nueva firma conserva la versión anterior; por defecto se activa al terminar. `load ... --no-activate` la deja inactiva. `activate <import_id>` permite volver a una versión completa existente. Las consultas fijan el ID activo al empezar y conservan resultados de una misma versión durante cada operación.

No se borran versiones automáticamente. Para esta familia, el cargador admite catalog.json de hasta 64 MiB; es un importador del catálogo Serie 76, no una plataforma genérica de documentos. Los artefactos siguen disponibles en disco y la evidencia estructurada se guarda en la base.

## Esquema y decisiones

Namespace series76. Las migraciones SQL versionadas se aplican transaccionalmente, con bloqueo y checksum del SQL. Una migración ya aplicada no debe editarse: añadir otra. Una discrepancia bloquea migrate y readiness. Las tablas auxiliares registran las migraciones y un puntero único al catálogo activo.

| Entidad | Responsabilidad |
|---|---|
| documents | Identidad del documento por SHA y tipo. |
| imports | Versión de extracción, hashes, manifiesto y fecha de importación. |
| source_tables | Tabla/página original, encabezados, notas y condiciones compartidas. |
| entries | Cada aparición de una referencia: código completo, alimentación, carcasa, potencia y estados. |
| service_specs | Torque in-lb/Nm, S4 y tasas por On/Off, modulación o alcance compartido. |
| frequency_specs | Tiempo de operación, FLA y LRA por frecuencia, o sin desglose publicado. |
| source_cells | Texto, lecturas alternativas, unidades y geometría originales por celda. |

Las cifras consultables son columnas NUMERIC; tasas por hora son enteros. JSONB guarda evidencia y metadatos de estructura variable. No se consulta el JSON original para obtener magnitudes. SQL parametrizado, claves foráneas, unicidad y restricciones de rango protegen la carga. Índices cubren versión/código, alimentación y torque por servicio.

No se copió directamente el CSV ancho: servicio y frecuencia son condiciones de una medición, no atributos intercambiables. Tampoco se eligió un modelo EAV genérico: conocemos las magnitudes y necesitamos restricciones y filtros explícitos. Los índices se revisan con EXPLAIN sobre el catálogo y un ensayo sintético aislado; eso no prueba rendimiento de cargas reales arbitrarias.

Los valores compartidos se guardan una sola vez. Para permitir su uso por servicio en la tabla trifásica se exige el diseño shared, ambos encabezados cycles/starts y la nota común de duty On/Off/modulación. La respuesta identifica shared_as_published; no fabrica torque On/Off o modulante independiente. Sin esa evidencia, una tabla compartida no entra en filtros de servicio.

N/A explícito y campo ausente del diseño conservan sus estados separados. No se asigna frecuencia a DC: frequency_scope=not_applicable. La tabla AC/DC sin frecuencia publicada usa not_specified. Una búsqueda por 50/60 Hz exige ese dato publicado y no presupone una frecuencia en las tablas de 24 V. No se aplican tolerancias automáticamente.

Notas generales conservan alcance de página; asteriscos y excepciones se vinculan a su tabla y referencia. csa_required comprueba lo publicado en el encabezado y excluye excepciones expresas; no es una certificación independiente ni permite inferir ATEX/IECEx.

## API y contratos

- GET /health: proceso vivo; no certifica DB.
- GET /ready: 200 si migraciones y catálogo activo están listos; 503 sin detalles privados si faltan.
- GET /api/actuators/{part_number}: código completo, incluido /A; 422 mal formado, 404 inexistente, 503 base no disponible.
- POST /api/actuators/search: objeto JSON de filtros; 422 para campos desconocidos, valores inválidos o combinaciones incompatibles.

La búsqueda exacta devuelve identidad, alimentación, measurements, field_status, services, frequencies, certification, notes, provenance, evidence y occurrences. measurements conserva los nombres con unidad del catálogo y sus null. Las cifras JSON se emiten como números solo si la conversión desde NUMERIC es exacta respecto a su representación decimal; si no, se rechaza la respuesta. La evidencia incluye valores originales con asterisco, no solo el código normalizado.

Filtros de búsqueda:

| Grupo | Campos |
|---|---|
| Alimentación y entorno | enclosure, supply_voltage_v, supply_current, phase_count |
| Condiciones | service: on_off/modulating; frequency_hz: 50/60; csa_required |
| Mínimos | min_torque_nm, min_duty_s4_percent, min_cycles_per_hour, min_starts_per_hour |
| Máximos | max_operating_time_s, max_fla_a, max_lra_a, max_motor_power_w |
| Paginación | limit: 1..100, por defecto20; offset: 0..1000000 |

AC o DC pueden encontrar una referencia AC/DC; pedir AC/DC exige esa compatibilidad publicada. DC con fase/frecuencia, ciclos para modulación o arranques para On/Off son combinaciones rechazadas. Los filtros se combinan con AND; tiempo y corrientes deben cumplirse en la misma fila de frecuencia. Un dato desconocido nunca satisface un umbral.

Un umbral de torque/duty/tasas sin servicio devuelve status=needs_clarification y fields=[service]. Un límite de tiempo/corriente sin frecuencia devuelve aclaración si quedan candidatos con valores distintos entre 50/60 Hz. No se escoge la frecuencia más favorable. Los demás resultados usan status=ok, total, limit, offset y products; sin coincidencias se devuelve lista vacía. El orden es estable por código, no una clasificación comercial. Las filas enteramente N/A se recuperan por código, pero se excluyen de recomendaciones. Duplicados idénticos conservan sus apariciones y se muestran una vez en búsqueda.

Ejemplo PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/actuators/764B00-11300000/A
$body = @{ service='on_off'; supply_voltage_v=24; supply_current='AC'; min_torque_nm=70 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/actuators/search -Method Post -ContentType application/json -Body $body
```

OpenAPI: http://127.0.0.1:8000/docs. Estas rutas y funciones son la base de las futuras herramientas; no implementan POST /api/conversation ni LangChain. La app futura debe separar presentación de producto de evidencia/debug.

## Pruebas y reproducción

Para desarrollo local con todas las pruebas, mantener .venv-ingest como runtime OCR separado y usar .venv:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:SERIES76_TEST_DB='1'
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe scripts/verify_catalog_db.py --restart
```

La variable habilita pruebas reales de PostgreSQL. Sin ella se omiten explícitamente esas pruebas; no se presentan como éxitos. Las pruebas usan rollback y no borran esquema/volúmenes. El driver reconstruye CSV desde SQL, compara todas las cifras y contexto, prueba HTTP real, verifica persistencia tras reiniciar y examina tablas temporales sintéticas de 100.000 filas. La referencia manual se usa exclusivamente en el evaluador posterior.

Resultados: reports/postgres/summary.json, roundtrip_evaluation.json, query_plans.json y RESULTADOS.md. Para exportar manualmente: `python -m backend.catalog.cli export --out .cache/catalog-from-postgres.csv`. Para ejecutar el backend fuera de Docker, exportar las variables PG* de conexión antes de iniciar uvicorn; el servidor no carga .env automáticamente.
