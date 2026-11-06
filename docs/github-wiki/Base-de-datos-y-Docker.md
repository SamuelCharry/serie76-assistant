# Base de datos y Docker

PostgreSQL 17 conserva catálogo, procedencia, usuarios, conversaciones y ejemplos vectoriales. Docker Compose arranca base de datos y backend; Android se ejecuta aparte.

| Dato | Decisión |
|---|---|
| Cifras técnicas | `NUMERIC`, separadas por servicio y frecuencia |
| Catálogo | Importaciones y un puntero a la importación activa |
| Extracción | Página, tabla, fila, hashes y celdas de origen |
| Historial | Mensajes con snapshots de productos, contexto y trazas |
| Recuperación | pgvector de 768 dimensiones; ejemplos de interpretación |

El arranque aplica migraciones, carga catálogo/glosario y crea las cuentas demo que falten. **No restablece contraseñas existentes.** Repetir la carga validada no duplica la importación; cambiar el catálogo activo no reescribe respuestas antiguas.

La imagen pgvector está fijada por digest. Debe respetarse la compatibilidad del volumen y su collation; reiniciar no exige borrar datos. No ejecutar `docker compose down -v`.

`/ready` comprueba disponibilidad del catálogo y glosario, no OpenRouter. La reproducción final de Windows pasó sobre una base aislada nueva; no demuestra instalación en toda máquina posible.

[Modelo entidad-relación](https://github.com/SamuelCharry/serie76-assistant/wiki/Modelo-entidad-relacion) · [Compose](https://github.com/SamuelCharry/serie76-assistant/blob/main/docker-compose.yml) · [T18](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/T18-tag-clean-clone.md)
