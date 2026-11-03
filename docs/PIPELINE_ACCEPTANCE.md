# Criterios del pipeline OCR real

Objetivo acordado: PDF -> OCR -> reconstrucción/limpieza -> validación -> CSV/JSON, con crecimiento del volumen previsto. La transcripción manual solo participa en evaluación.

## Evidencia exigida antes de cerrar

1. Ejecutar desde el PDF original y generar valores desde las lecturas OCR. El proceso de producción no puede leer data/manual, data/reference, data/reviewed ni el ledger de correcciones.
2. Detectar tablas, filas, columnas, servicio, frecuencia y celdas combinadas por encabezados, posiciones y líneas visibles. Sin hash obligatorio del catálogo, número fijo de páginas/filas, coordenadas por página ni valores por referencia.
3. Conservar códigos completos, ambas unidades publicadas, mediciones compartidas y sin frecuencia, cuatro N/A explícitos, cinco marcas CSA y texto/procedencia de las notas. Reintentar recortes en la imagen, sin convertir O en 0 o quitar puntos globalmente.
4. Medir el resultado contra la revisión visual mediante una herramienta separada. Publicar códigos, celdas, N/A, discrepancias y filas, sin confundir concordancia con garantía universal.
5. Probar un PDF con datos modificados y posiciones/reordenación diferentes: la salida debe seguir el documento nuevo, no reproducir el catálogo guardado.
6. Procesar varios documentos y páginas incrementalmente, con modelo reutilizado, lotes de reconocimiento limitados y límites explícitos de píxeles/páginas/celdas. Medir un ensayo de 100 páginas sin acumular todas las imágenes o filas en RAM.
7. Aislar errores por documento. Un esquema desconocido, lectura ambigua, dato físicamente inconsistente o conflicto de identidad debe generar una cola de revisión y un estado incompleto, sin publicarse como CSV/JSON final válido.
8. Conservar SHA-256, cajas de origen, candidatos OCR, método de selección y versiones. Usar caché de inferencia con checksums y escritura transaccional; verificar integridad al reusar una ejecución.
9. Ejecutar en un entorno de ingestión independiente sin librerías del notebook ni servicios remotos. Cero OpenRouter y ninguna subida de PDF.
10. Documentar comandos, dependencias, diseños soportados, límites, rendimiento y pendientes. Mantener estados honestos. PostgreSQL/agente/app siguen fuera de este bloque.

## Límite de generalización

Se soportan las familias de tabla técnica detectables por sus unidades y encabezados. No se promete extraer correctamente cualquier diseño de cualquier PDF. Los nuevos diseños deben ser detectados como no soportados y añadirse mediante parsers y pruebas, sin contaminar la lógica con números esperados.
