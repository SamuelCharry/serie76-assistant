# Correcciones verificadas de la referencia visual

Durante la comparación OCR se detectaron tres errores de la transcripción anterior. Se volvió al PDF eléctrico original; no se corrigieron cifras por conversiones ni por mayoría de motores.

Documento: `data/raw/series_76_electric_data.pdf`, SHA-256 `4c28023929183df8e2a763e759cc84572b44604b30837a21e22c1166f88267e0`, página 4. Revisión visual: 2 de noviembre de 2026. CSV y JSON de referencia se actualizaron juntos.

| Tabla / fila | Referencia completa | Campo | Antes | PDF / corregido |
|---|---|---|---:|---:|
| p4_t1 / 7 | 764X30-11300000/A | motor_power_w | 180 | 90 |
| p4_t2 / 7 | 764X30-11320000/A | modulating_torque_nm | 620 | 640 |
| p4_t2 / 8 | 764Y30-11320000/A | cycles_per_hour | 160 | 140 |

Evidencia renderizada directamente del PDF, a 300 DPI:

- [Potencia de la tabla de 110 V](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/ocr/reference_review/p4-top-power.png), rectángulo PDF en puntos `(70, 245, 520, 312)`.
- [Torque y ciclos de la tabla de 220 V](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/ocr/reference_review/p4-bottom.png), rectángulo `(70, 433, 520, 495)`.

La celda de 90 W de 110 V incluye 763Y30 y 764X30. En 220 V, 90 W solo corresponde a 763Y30 y la celda de 180 W empieza en 764X30. La plantilla respeta esa diferencia: no copia el mismo alcance entre tablas.

Estas correcciones no certifican las demás celdas por extensión. La métrica final compara contra la referencia revisada; sigue siendo una referencia manual falible, sin segunda transcripción independiente de todo el catálogo.

También se volvió a comparar visualmente la primera tabla de 110 V (p1_t1): sus 11 códigos y los 15 campos numéricos por fila coinciden con la referencia actual. Esa revisión acotada no se extiende automáticamente a las otras seis tablas.
