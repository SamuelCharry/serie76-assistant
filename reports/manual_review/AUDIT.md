# Auditoría visual completa de Series 76 Electrical Data

**Límite del resultado:** los archivos de catalog-v1 se construyen desde la transcripción manual. El OCR sirve como comprobación y sus seis diferencias se documentan; eso no demuestra que OCR con limpieza genere el catálogo por sí mismo. Esta entrega es la referencia visual revisada para evaluar el pipeline OCR final, que sigue pendiente.

Se revisaron visualmente las cuatro páginas, siete tablas, encabezados y notas del PDF eléctrico. Los recortes se renderizaron desde el documento original y se guardaron en esta carpeta. Se introdujeron de nuevo las 68 filas desde las imágenes, sin construirlas copiando el CSV anterior ni la salida OCR. Después se compararon ambas transcripciones: cero diferencias numéricas respecto a la referencia ya corregida.

Fuente SHA-256: `4c28023929183df8e2a763e759cc84572b44604b30837a21e22c1166f88267e0`.

## Datos contrastados con los ejemplos del usuario

| Modelo completo | On/Off In-Lbs. | On/Off Nm | Potencia del motor, W |
|---|---:|---:|---:|
| 764B00-11300000/A | 9,700 | 1,100 | 180 |
| 765A00-11300000/A | 17,700 | 2,000 | 180 |
| 761X30-11300000/A | 690 | 80 | 15 |
| 764X30-11300000/A | 6,900 | 800 | 90 |

Estos valores se leyeron en los recortes `p1_t1.png` y `p4_t1.png`. La salida seleccionada de RapidOCR en `data/ocr/selected-smoke-20261102/cells.json` ya conserva estos pares en las columnas correctas y lee 800 en el último ejemplo. No se encontró la inversión ni el literal BOO en esas celdas de ese archivo. No se supone cuál es el archivo que dio lugar a la observación del usuario.

El OCR crudo sí conserva seis errores confirmados en otras celdas; no se lo declara perfecto. Se corrigieron mediante decisiones explícitas en `data/manual/approved_ocr_corrections.json`, tras volver a las imágenes. No existe sustitución global de letras o signos.

## Celdas combinadas y vacíos

- En las tablas mixtas de página 1: 15 W corresponde a filas 1–2; 40 W, a 3–5 (tres filas); 90 W, a 6–7. Las siguientes agrupaciones se conservan por sus límites visibles.
- En la tabla de 110 V explosionproof, 90 W abarca 763Y30 y 764X30. En 220 V, 90 W solo abarca 763Y30; 764X30 pertenece a 180 W. No se copia el mismo forward-fill entre tablas.
- En ambas tablas de 24 V, 40 W abarca las cinco filas completas.
- Los cuatro valores nulos de motor_power_w corresponden exclusivamente a las cuatro referencias N/A de la tabla trifásica: 761A00, 761B00, 762A00 y 762B00 con sufijo completo -11330C00/A. No son cuatro omisiones por falta de forward-fill.
- Las otras 64 filas tienen potencia. Cada vacío de los datos normalizados tiene estado explícito: source_NA o not_in_layout. No queda un vacío numérico inexplicado por el esquema.

## Estructuras y notas preservadas

- Las tablas mixtas mantienen dos torques/duties por servicio y mediciones separadas para 60/50 Hz.
- La trifásica conserva Output Torque y Duty Cycle compartidos, sin inventar dos mediciones independientes.
- 24 V AC/DC On/Off (-11380000/A) y 24 V DC Modulating (-11370000/A) conservan identidades y columnas distintas. Los amperajes y tiempos no se duplican bajo frecuencias que el PDF no publica.
- Se conservan ambos torques tal como están impresos; no se recalculan mediante conversiones.
- Los cinco asteriscos CSA, encabezados de carcasa/marcados, clasificación de área, tolerancias, referencia IEC y condiciones FLA/LRA quedan en el JSON con alcance por tabla/página. Los números de nota de página 4 difieren de las otras páginas y se conservan.

## Entregables y método

- Transcripción de origen: `data/manual/series76_visual_transcription.json`, incluyendo orden de columnas, valores léxicos, bloques N/A y celdas combinadas.
- Catálogo exportado: `data/reviewed/catalog-v1/catalog.csv` y `catalog.json`.
- Procedencia por celda: `data/reviewed/catalog-v1/cells.csv`.
- Tabla HTML para revisión: `data/reviewed/catalog-v1/review.html`.
- Correcciones aplicadas y hashes: `review_log.json` y `manifest.json` del mismo directorio.

Se comprobaron 941 observaciones primarias: 68 códigos, 869 cifras (incluida la expansión documentada de potencia) y cuatro N/A. El OCR coincide en 935; las seis restantes están corregidas y documentadas. El catálogo revisado no contiene diferencias sin revisar respecto a la transcripción visual.

La revisión visual la hizo el asistente de IA, sin segunda firma humana ni aclaración del fabricante. Es OCR más revisión documentada, no extracción autónoma infalible. Las salidas crudas y las métricas históricas se conservan intactas. No hubo llamadas a OpenRouter.

## Reproducir

Desde la raíz, con `.venv-ocr` preparado:

```powershell
./.venv-ocr/Scripts/python.exe scripts/ocr_lab.py --config config/ocr.json --out data/ocr/nueva-lectura
./.venv-ocr/Scripts/python.exe scripts/extract_reviewed_catalog.py --ocr-dir data/ocr/nueva-lectura --out data/reviewed/nueva-exportacion
./.venv-ocr/Scripts/python.exe -m unittest discover -s tests -v
```

La exportación rechaza otro PDF, filas/celdas faltantes o repetidas, contenido numérico inesperado en N/A y cualquier diferencia OCR sin una decisión exacta ya revisada. No rellena datos desde el viejo CSV de referencia. La carga PostgreSQL sigue pendiente.

Reproducción ejecutada desde una lectura OCR nueva en data/ocr/manual-review-reproduction: los cinco archivos exportados resultaron idénticos byte por byte a catalog-v1. Evidencia: reproduction.json. Dieciocho pruebas pasan, incluyendo las inversiones y BOO introducidos deliberadamente para verificar su rechazo.
