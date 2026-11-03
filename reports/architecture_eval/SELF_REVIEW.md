# Revisión de entrega

Resultado: infraestructura experimental y diagramas entregados; evidencia insuficiente para promover una arquitectura. El defecto S4 sigue visible en la cohorte congelada y bloquea integrar esa presentación contextual.

| Eje | Nota / 5 | Evidencia y límite |
|---|---:|---|
| Exactitud | 4 | SQL experimental coincide con las 68 filas operativas; 73 columnas y 9 FK verificadas. Resultados originales sin deriva. El renderer elimina la definición S4 y algunas viñetas se extraen como carácter de sustitución. |
| Completitud | 3 | Cinco variantes implementadas, 24 escenarios definidos, 11 intentados, solo 1 común sin fallo proveedor. El presupuesto se respetó; no se completó la comparación. |
| Claridad | 4 | ER Mermaid, SVG y visor autocontenido con cinco flujos. Lógica de pestañas probada; el navegador de la sesión no estuvo disponible para una revisión interactiva real. |
| Acción | 4 | CLI, entorno separado, bloqueo, ledger, continuación validada y protocolo reproducible. OpenRouter y una cohorte nueva tras corregir presentación siguen pendientes. |
| Concisión | 4 | Informe final distingue resultados, fallos y reservas. Las trazas SQL originales son voluminosas porque conservan procedencia y evidencia. |

Media: 3,8/5. La nota de completitud no se corrige gastando más sin autorización: conservar la comparación parcial y preparar una cohorte nueva cuando se resuelvan los fallos compartidos y la disponibilidad del proveedor.

Prioridades:

1. Corregir segmentación/viñetas y presentación por término; distinguir identificadores como S4 de magnitudes, preservando procedencia. Añadir casos de definición y no repetir esta cohorte para mejorar sus puntuaciones.
2. Contabilizar embeddings por invocación y separar latencia de servicio del pacing antes de comparar costos o promover una variante. Guardar decisiones intermedias completas, sin razonamiento interno.
3. Completar escenarios emparejados con proveedor estable y luego verificar la candidata mediante OpenRouter, sin alterar el chat operativo por esta evidencia parcial.

Autocomprobación: el usuario puede inspeccionar el esquema real, las cinco implementaciones, los casos y las respuestas originales. No se sostiene que una arquitectura haya ganado, que los costos sean una factura ni que el experimento cierre Part A.
