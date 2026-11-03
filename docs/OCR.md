> Historical experiment documentation. Source and commands are in [archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/). Current verification summaries: [evidence](evidence/).

# Laboratorio OCR local

Se comparan Tesseract mediante tesserocr, EasyOCR y PP-OCRv5 mediante RapidOCR/ONNX. Son tres candidatos prácticos para este catálogo en CPU, no una clasificación universal del mercado.

Los experimentos no cargan `.env`, no necesitan claves y no llaman a OpenRouter. La primera instalación descarga paquetes y pesos públicos; el reconocimiento del PDF se ejecuta localmente. Docker no es necesario para este bloque.

## Ejecutar en Windows

Desde la raíz, con Python 3.12 de 64 bits:

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


El primer comando crea `.venv-ocr`, instala las versiones de `https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/requirements-ocr.lock.txt`, verifica el modelo inglés de Tesseract y registra un kernel dentro de ese entorno. La instalación puede tardar: EasyOCR depende de PyTorch. No modifica el entorno `.venv` del backend. El pin de setuptools conserva `pkg_resources`, que esta versión de ydata-profiling todavía importa.

También se pueden abrir y ejecutar las celdas con VS Code/Jupyter seleccionando `.venv-ocr`:

1. [Comparación de los tres OCR](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/notebooks/01_comparar_ocr.ipynb).
2. [Exploración breve con ydata-profiling](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/notebooks/02_exploracion_ydata.ipynb).

El notebook 01 crea una carpeta de evidencia nueva para los tres motores y guarda `https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/config/ocr.json`. El notebook 02 usa esa ejecución y genera dos HTML pequeños: referencia y OCR. Para volver a mostrar resultados existentes, sin repetir la inferencia:

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


No se selecciona ganador si falta un motor, una página, una celda del esquema o un manifiesto completo. Una ejecución parcial conserva evidencia y falla de forma visible.

## Usar la configuración seleccionada

[Historical commands and dependencies in archive/pre-cleanup](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/).


Elegir una carpeta de salida nueva en cada ejecución. El script rechaza sobrescribir evidencia. También rechaza PDF con una huella distinta: la plantilla solo se evaluó para este catálogo.

Cada ejecución produce imágenes, texto, JSON de coordenadas por página, `cells.json` con texto crudo por tabla/fila/campo y un manifiesto con versiones, configuración, hash del documento, hashes de modelos y tiempos. Las celdas combinadas conservan el alcance utilizado. No se corrigen códigos ni números usando la referencia.

## Qué mide el ensayo

- Cuatro páginas, siete tablas y 68 posiciones de producto; se incluyen cuatro filas N/A.
- Comparación exacta por tabla/fila/campo contra la referencia visual revisada. La normalización admite formato numérico y espacios, pero no sustituye O/0, I/1 ni cifras sospechosas.
- Celdas vacías de las filas N/A no regalan aciertos. Se evalúan los cuatro N/A explícitos y cualquier valor numérico inesperado.
- Selección por menor número de celdas desiguales; desempate por filas completas y tiempo. Los asteriscos de excepción CSA se miden aparte.
- Tiempos de constructor e inferencia se registran por separado. RapidOCR carga modelos de forma diferida: parte de su carga cae en la primera página. Es una medición local, no un estudio estadístico de latencia.

Las configuraciones se ajustaron sobre el mismo catálogo. No hay conjunto independiente ni afirmación de generalización a documentos nuevos. El clasificador de orientación de RapidOCR se desactiva porque todas estas páginas están derechas; en ensayos preliminares giraba algunos números. Se usa reconocimiento inglés. Tesseract usa PSM 11: en una comprobación preliminar de página 1 produjo menos discrepancias que PSM 3 y 6.

La plantilla de filas, columnas y celdas combinadas se midió visualmente. Es específica de este PDF; los motores reconocen texto, no resuelven por sí solos el dominio de servicio/frecuencia. Las notas y encabezados permanecen en la evidencia cruda; todavía falta su normalización completa para la ingestión.

## Revisar los resultados

`https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/ocr/metrics.csv` contiene la comparación; `discrepancies.csv`, los fallos individuales; los manifiestos, las versiones/configuraciones observadas. `latest_profile.json` apunta a los dos informes HTML de ydata.

El perfil se limita a 11 columnas. Desactiva correlaciones costosas y no imputa datos. Los tokens numéricos inválidos se convierten en nulos **solo para el perfil** y se contabilizan aparte; el texto original permanece en `cells.json` y en las discrepancias. Una distribución plausible no demuestra que la cifra sea correcta.

La referencia también tenía errores: ver [revisión con recortes del PDF](OCR_REFERENCE_REVIEW.md). No se considera un oráculo infalible. La métrica mide coincidencia contra la referencia revisada, no una validación independiente de todo el catálogo.

Este bloque no carga PostgreSQL ni implementa el agente. Los manifiestos siguen indicando `validated_table_data=false`. Resolver las discrepancias y las notas es necesario antes de importar datos de negocio.

## Revisión visual posterior y catálogo corregido

Se completó una nueva transcripción de las cuatro páginas, siete tablas, celdas combinadas y notas. Ver [auditoría visual](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/manual_review/AUDIT.md) y [tablas revisadas](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/data/reviewed/catalog-v1/review.html). El OCR crudo conserva sus seis errores; una capa distinta aplica solo las correcciones exactas revisadas y rechaza cualquier diferencia no autorizada. Los cuatro nulos de potencia de la exportación son los N/A explícitos del trifásico, no omisiones de celdas combinadas.

```powershell
./.venv-ocr/Scripts/python.exe scripts/extract_reviewed_catalog.py --ocr-dir data/ocr/nueva-ejecucion --out data/reviewed/nueva-exportacion
```

La exportación incluye CSV/JSON del catálogo, estados de campos, procedencia por celda, notas, tabla HTML, decisiones de revisión y hashes. No lee el viejo CSV para completar valores. Es OCR más revisión explícita, no OCR autónomo infalible ni carga PostgreSQL.

## Fuentes de los candidatos

- [Tesseract: limitaciones con tablas y segmentación](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html).
- [tesserocr: motor empaquetado en wheels y datos de idioma](https://pypi.org/project/tesserocr/).
- [EasyOCR: API, CPU y descarga de modelos](https://github.com/JaidedAI/EasyOCR).
- [RapidOCR: configuración y resultados con coordenadas](https://rapidai.github.io/RapidOCRDocs/main/quickstart/).
- [YData: perfil mínimo](https://docs.profiling.ydata.ai/latest/features/big_data/).
