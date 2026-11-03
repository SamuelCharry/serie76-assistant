# Ingestión real desde PDF con OCR

Este es el flujo de producción del bloque de datos. No utiliza la transcripción manual, CSV de referencia ni correcciones por número de parte. Esos archivos solo sirven para evaluación.

## Ejecutar

Python 3.12 de 64 bits. Desde la raíz, PowerShell:

```powershell
python -m venv .venv-ingest
./.venv-ingest/Scripts/python.exe -m pip install -r requirements-ingest.lock.txt
./.venv-ingest/Scripts/python.exe scripts/ingest.py data/raw/series_76_electric_data.pdf --out data/processed/mi-importacion
```

Para varios documentos, pasar archivos o directorios. El directorio se recorre incrementalmente:

```powershell
./.venv-ingest/Scripts/python.exe scripts/ingest.py "C:/catalogos" --out data/processed/lote --no-images --threads 2
```

La primera inferencia descarga pesos públicos de PP-OCRv5 móvil (detector multilingüe y reconocedor inglés) y verifica sus hashes mediante RapidOCR. Luego funciona con los modelos locales. No solicita ni lee claves OpenRouter, no carga .env y no sube los PDF. El runtime no instala PyTorch, EasyOCR, pandas, ydata ni el servidor backend.

Cada documento tiene un directorio propio identificado por nombre, hash del PDF y firma del pipeline. Un archivo repetido ya terminado solo se reutiliza después de comprobar todos los hashes de sus resultados. Una ejecución incompleta o fallida no se declara lista: usar una raíz --out nueva para reintentarla, conservando evidencia y reutilizando la caché de inferencia. No se elimina ni sobrescribe evidencia previa de documentos terminados.

## Qué produce

Solo si el documento pasa las reglas y no tiene discrepancias sin resolver:

- catalog.csv: filas del catálogo, con campos que distinguen servicio, frecuencia y unidad.
- catalog.json: las mismas filas, estados de ausencia, suministro, encabezados y notas por página.
- catalog.html: tablas navegables por página/diseño, con unidades explícitas.

En todos los casos:

- manifest.json: estado ready, needs_review o failed; hashes, versiones, parámetros, contadores y tiempos.
- cells.jsonl: texto original, lecturas alternativas, valor elegido, unidad, servicio/frecuencia cuando la fuente los separa, cajas y alcances combinados.
- review_queue.jsonl: lecturas ambiguas, estructuras no soportadas o contradicciones. Un documento con estos problemas no publica catalog.csv/catalog.json como resultado válido.
- evidence/page-NNNNNN.json: OCR y estructura inferida por página. Las imágenes se conservan por defecto; --no-images reduce disco, manteniendo cajas, DPI y hash del PDF para volver a renderizar.
- work.sqlite3: spool temporal de filas y detección de duplicados; no es la base de datos de negocio.

La raíz del lote contiene un resumen y logs JSONL de cada ejecución. El código de salida es 0 si todos los documentos están listos; 2 si alguno requiere revisión o falló. Los demás documentos continúan procesándose.

## Cómo se generan los valores

1. Renderizado de una página del PDF con PyMuPDF. No se carga todo el documento renderizado en RAM.
2. Detección/reconocimiento de texto con RapidOCR, conservando posiciones y confidencias.
3. Detección de tablas por Base Part Number y título de suministro. Las filas proceden de identificadores reconocidos; sus posiciones no están predefinidas.
4. Inferencia de columnas por unidades y encabezados: In-Lbs frente a Nm, servicio, ciclos/arranques y frecuencia. No se asignan unidades por el tamaño del número.
5. Detección de límites de celdas combinadas mediante líneas de la imagen. Los valores de potencia se expanden solo dentro del grupo visible. N/A se conserva como ausencia explícita; no como cero.
6. Relecturas locales por celda: imagen original, contraste, contexto completo o región de texto detectada. Se registran todas las alternativas. Los lotes de reconocimiento están limitados a 32 imágenes; el modelo se reutiliza.
7. Selección según acuerdo entre lecturas y calidad. Las variantes de un mismo reconocedor están correlacionadas: su acuerdo no garantiza exactitud. Una alternativa fuerte en conflicto genera revisión. La trazabilidad distingue acuerdo de varias lecturas de una lectura primaria muy confiable sin confirmación suficiente.
8. Validación: formato numérico, precisión representable sin redondeo silencioso, porcentajes, conteos enteros y coherencia dimensional amplia entre torques. Las reglas señalan un problema; nunca convierten unidades para reemplazar una cifra publicada.
9. Exportación incremental desde el spool de disco, únicamente cuando el documento puede publicarse como ready.

El dato exportado procede de lecturas OCR. No hay tabla de números esperados, offsets por página ni un filtro que solo permita el hash del PDF original.

## Limpieza limitada por contexto

No se convierte BOO en 800 ni se quitan puntos/colones globalmente. Un tiempo publicado como 3.2 s conserva el decimal; una lectura dudosa de 32 debe resolverse releyendo su imagen.

Se permiten normalizaciones léxicas específicas y registradas en notas: un identificador numérico después de IEC y los numerales romanos de un grupo de gas después de Ex d/AEx d. Antes/después y regla quedan guardados; el texto OCR original se conserva. Estas reglas no se aplican a mediciones ni a números de parte.

## Diseños soportados y rechazo explícito

Se soportan los cuatro diseños técnicos presentes en el catálogo:

- Torque/duty separados para On/Off y modulación, con mediciones por frecuencia.
- Torque/duty compartidos en una tabla con mediciones por frecuencia.
- On/Off sin desglose de frecuencia.
- Modulación sin desglose de frecuencia.

Se detectan por sus encabezados, no por página, cantidad fija de filas, voltaje concreto o lista de referencias. Se soportan títulos de suministro con otros valores y tasas por hora/minuto reconocibles. El formato de identificador admitido es seis caracteres alfanuméricos, guion, ocho caracteres y /A, con asterisco opcional.

No se promete extraer cualquier PDF del mundo. Un idioma/diseño desconocido, código ilegible, tabla sin unidades claras, ausencia parcial sin alcance deducible, orientación física no reconocible o líneas combinadas no detectables debe pasar a revisión. No existe fallback al catálogo manual para ocultar el fallo. Añadir otro diseño requiere parser y pruebas propios.

Los vacíos numéricos de catalog.json distinguen source_NA de not_in_layout. La clasificación de dato ausente no se confunde con cero ni con un error OCR.

## Volumen, memoria y costos

- Un modelo por proceso, no uno por página ni por referencia.
- Lectura de archivos/páginas y logs incremental, lotes pequeños y spool de filas/índice de identidades en disco. La RAM no contiene todo el corpus.
- Caché de inferencia en un SQLite local con transacciones, firma del motor, hash de la imagen y checksum del resultado. Evita millones de archivos diminutos. --cache permite elegir su ubicación; su consumo de disco crece con contenido único y debe presupuestarse.
- Duplicados idénticos conservan cada procedencia; un mismo código con datos diferentes dentro del documento se rechaza para revisión. Entre documentos se preservan versiones independientes. La política de consolidación en PostgreSQL queda para el siguiente bloque.
- Límites por defecto: 2.000 páginas/PDF, 512 MiB/PDF, 20 millones de píxeles/página, 30.000 tokens/página, 1.000 filas/tabla y 128 campos distintos. Hay presupuestos adicionales para notas y relecturas. Cambiar DPI/píxeles/páginas es explícito en CLI.
- OCR local no implica cómputo gratis: el trabajo nuevo sigue costando CPU aproximadamente en proporción a sus páginas. La caché acelera repeticiones; no elimina el costo de PDF distintos.
- El CLI procesa documentos secuencialmente y aplica backpressure natural. La unidad de trabajo es el documento y puede repartirse en procesos con raíces de salida separadas. No hay una cola distribuida, autoscaling ni rendimiento prometido para cargas heterogéneas; reservar RAM por worker requiere medir los modelos y resolución elegidos.

SQLite aquí solo es caché/spool, no la base consultada por las herramientas del assessment. La base de negocio y las conversaciones deberán ser PostgreSQL.

## Evaluación independiente y pruebas

```powershell
./.venv-ingest/Scripts/python.exe scripts/evaluate_ingestion.py --catalog <directorio-del-documento>/catalog.csv --reference data/reference/serie76_tablas_extraidas.csv --out reports/pipeline/evaluation.json
./.venv-ingest/Scripts/python.exe -m unittest discover -s tests -v
```

La evaluación lee la referencia después de la extracción. El proceso de producción no la importa. El resultado compara contra una revisión visual falible, no certifica exactitud universal.

Para reproducir la suite real (instalar requirements-ingest-dev.txt en un entorno de desarrollo separado, o usar .venv-ocr para el driver):

```powershell
./.venv-ocr/Scripts/python.exe scripts/verify_ingestion.py --python .venv-ingest/Scripts/python.exe --out reports/pipeline/verified --scale
```

La suite bloquea lecturas de las carpetas manual/reference/reviewed y conexiones de red durante la ejecución original; comprueba datos nuevos, tres filas, desplazamiento, reordenación de páginas, aislamiento de archivos corruptos/no soportados, integridad al reutilizar resultados y un ensayo de 100 páginas.

El ensayo de 100 páginas repite cuatro páginas 25 veces. Es una prueba de volumen y caché; no una evaluación de precisión sobre 100 diseños nuevos. Los tiempos y RAM medidos se publican con ese alcance en reports/pipeline/RESULTADOS.md.

## Pendientes del assessment

Carga idempotente/transaccional en PostgreSQL, herramientas LangChain, agente, conversaciones persistentes y Android. No se declara implementado ese producto por tener CSV/JSON correctos.
