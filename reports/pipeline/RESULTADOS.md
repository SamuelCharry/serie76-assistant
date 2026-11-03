# Resultado del pipeline OCR real

Estado: verificado sobre la versión d7e1c05b179f6b44dc77cda695cfd83a4b570e0db1ee2083d537fd709df70b27. Fuente SHA256: 4c28023929183df8e2a763e759cc84572b44604b30837a21e22c1166f88267e0.

## Salida y reproducción

[Tablas HTML](../../data/extracted/series76/catalog.html), [CSV](../../data/extracted/series76/catalog.csv), [JSON](../../data/extracted/series76/catalog.json), [manifiesto](../../data/extracted/series76/manifest.json). Copia byte-idéntica del resultado aislado doc-series_76_electric_data-4c28023929183df8-d7e1c05b17; todos los hashes comprobados. No se copió el spool temporal.

Comando e instalación en [docs/INGESTION.md](../../docs/INGESTION.md). El runtime usa OCR local PP-OCRv5/RapidOCR; no carga referencia manual, ledger ni valores esperados. La referencia solo se lee en otro proceso, después de exportar.

## Evidencia ejecutada

- [Suite completa](verified/summary.json): 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas CSA y 272/272 atributos de contexto. 941/941 comprobaciones primarias, cero diferencias; comparación contra referencia visual falible.
- [Aislamiento](verified/reference_isolation.json): autoprueba del bloqueo correcta, cero intentos de leer manual/reference/reviewed y cero conexiones de red. Runtime sin torch/pandas/ydata/EasyOCR. Los modelos ya estaban descargados.
- [Variantes](verified/variants.json): PDF sintético de tres filas con códigos/cifras nuevos y decimales reales como 3.2; variante desplazada; páginas originales reordenadas. No memoriza hash, coordenadas, número de filas o valores por código. Las variantes comprueban mecanismos, no diversidad documental amplia.
- [Errores de lote](verified/batch_failure_isolation.json): documento desconocido needs_review, corrupto failed y válido ready; un fallo no cancela los demás. Reutilización solo tras comprobar hashes.
- 43 pruebas unitarias/de integridad pasan; cobertura del paquete nuevo 85% en esa suite (no incluye integración OCR). Ruff F/E9 y pip check correctos. Dependencias transitivas runtime congeladas y verificadas en entorno nuevo.
- [Volumen actual](verified/scale-100.json): 100 páginas, 175 tablas, 1.700 filas, 100 N/A, cero incidencias; 43.39 s y pico RSS 428.6 MiB; 47050 aciertos de caché y 0 inferencias nuevas.
- [Ensayo previo con caché inicialmente sin esas lecturas](acceptance/scale-100.json): 175.83 s, pico 1.45 GiB, 1.872 fallos y 45.178 aciertos de caché. Versión previa del mismo flujo; no comparar tiempos como mejora algorítmica.

## Qué cambió

Columnas inferidas por encabezados/unidades, separación de servicio/frecuencia y potencia propagada solo dentro de la celda combinada medida. N/A explícito y campo ausente del diseño son estados distintos. Relecturas de imágenes y consenso resuelven errores sin sustituir letras o borrar decimales. Encabezados/certificaciones y excepciones se asocian a cada tabla. Notas con procedencia, lecturas alternativas y limpieza técnica contextual auditada para IEC/grupos de gas. Las discrepancias bloquean el catálogo validado y generan review_queue.jsonl.

Procesamiento por página, lotes acotados, modelo reutilizado y spool/caché SQLite en disco. SQLite es infraestructura transitoria; PostgreSQL de negocio sigue pendiente. No se usó OpenRouter ni se subieron PDFs.

## Límites y siguiente paso

Las 100 páginas repiten las cuatro originales 25 veces: demuestran volumen/caché, no precisión en cien diseños nuevos. Se soportan las cuatro familias de tablas y encabezados ingleses descritas en la documentación; diseños desconocidos requieren revisión/adaptación. El costo CPU crece con páginas únicas y la caché ocupa disco. No hay cola distribuida ni autoscaling probado; presupuestar memoria por proceso antes de paralelizar. Docker/Linux no verificados para este runtime. El siguiente bloque es carga PostgreSQL transaccional/idempotente y consultas técnicas; agente y app siguen pendientes.
