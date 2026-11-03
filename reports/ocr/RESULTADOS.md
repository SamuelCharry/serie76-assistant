# Resultado del laboratorio OCR

Ejecución local, 2 de noviembre de 2026 (America/Bogota). Ninguna llamada a OpenRouter ni envío del PDF a un servicio OCR. Se descargaron paquetes y pesos públicos.

| Motor/configuración | Códigos completos | Cifras exactas / 869 | N/A explícitos | Filas completas / 68 | Discrepancias primarias | Inferencia, 4 páginas |
|---|---:|---:|---:|---:|---:|---:|
| RapidOCR / PP-OCRv5 inglés, sin giro | 68/68 | 863 | 4/4 | 63 | 6 | 64.0 s |
| EasyOCR / inglés, CPU | 13/68 | 701 | 0/4 | 12 | 228 | 463.1 s |
| Tesseract 5.5.3 / PSM 11 | 30/68 | 662 | 0/4 | 12 | 252 | 13.2 s |

La plantilla geométrica es común a los tres motores. Las discrepancias primarias incluyen códigos, cifras, estado N/A y valores inesperados en el bloque N/A. Por eso el número total de comparaciones puede variar entre motores; los denominadores de códigos y cifras son los mismos. Los asteriscos CSA se evalúan aparte: RapidOCR conserva los cinco; los otros dos, ninguno.

**Se seleccionó RapidOCR**, con 935/941 coincidencias (99.36 %) contra la referencia revisada. No es una tasa de exactitud independiente ni una clasificación universal de motores. Hubo ajuste de configuración sobre este mismo catálogo y una única medición de tiempo. RapidOCR carga modelos de forma diferida, por lo que la primera página incluye parte de su carga.

Una ejecución adicional usando config/ocr.json completó las cuatro páginas y produjo exactamente las mismas celdas reconstruidas: ver runtime_verification.json. Sigue marcada como datos no validados.

## Seis discrepancias que siguen abiertas

| Tabla / fila | Campo | OCR | Referencia revisada |
|---|---|---|---|
| p1_t2 / 1 | Torque On/Off, Nm | 8:0 | 80 |
| p1_t2 / 8, 9 y 11 | Arranques/h | 8:40 | 840 |
| p2_t1 / 7 | Ciclos/h | 3:2 | 32 |
| p2_t1 / 7 | Tiempo a 60 Hz, s | 3.2 | 32 |

No se repararon automáticamente ni se rellenaron desde la referencia. La última discrepancia es especialmente peligrosa: 3.2 es un número válido pero equivale a una décima parte del valor de referencia.

## Exploración ydata ejecutada

Se generaron dos HTML, con 11 columnas y 68 filas cada uno. Referencia y OCR conservan 68 códigos distintos y cuatro estados N/A. Un token de torque no numérico se convirtió en nulo únicamente para el perfil; los errores crudos permanecen en la evidencia. El subconjunto perfilado no incluye todos los campos: no sustituye la comparación de 869 cifras. Ver latest_profile.json para rutas y conteos.

Tres celdas de la referencia manual se corrigieron después de volver al PDF: [registro y recortes](../../docs/OCR_REFERENCE_REVIEW.md). La primera tabla de 11 filas se volvió a revisar visualmente sin diferencias contra la referencia actual. Las otras tablas todavía no tienen una segunda transcripción independiente completa.

## Verificación y límites

- Los dos notebooks se ejecutaron y guardaron sus salidas, sin celdas con errores de ejecución.
- Ocho pruebas de integridad pasan; los entornos OCR y backend pasan pip check. La instalación con el lockfile se verificó mediante pip dry-run en el entorno instalado.
- No hay importación a PostgreSQL. Falta cerrar seis discrepancias y normalizar/revisar encabezados y notas.
- Plantilla específica de este PDF, protegida por SHA-256. El servicio Docker OCR original sigue siendo el ensayo Tesseract; el laboratorio seleccionado funciona localmente.

Reproducción y comandos: [docs/OCR.md](../../docs/OCR.md).
