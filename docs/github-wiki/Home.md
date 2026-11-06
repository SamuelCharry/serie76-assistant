# Series 76 · Guía de sustentación

Un asistente Android para consultar y seleccionar actuadores de un catálogo técnico. **El modelo interpreta la petición; PostgreSQL y el código producen los valores y la respuesta.**

Actualizado al 6 de noviembre de 2026. Código entregado en `main`; la etiqueta `v1.0-submission` conserva la aplicación probada en `ac56dee`. Los cambios posteriores de entrega son documentación.

## Recorrido recomendado

| Paso | Qué explicar | Página |
|---|---|---|
| 1 | Problema, componentes y responsabilidades | [Arquitectura](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura) |
| 2 | De una pregunta a una respuesta verificable | [Agente LangChain](https://github.com/SamuelCharry/serie76-assistant/wiki/Agente-LangChain) |
| 3 | Cómo se obtienen y conservan los datos | [Ingesta](https://github.com/SamuelCharry/serie76-assistant/wiki/Pipeline-de-ingesta) y [modelo de datos](https://github.com/SamuelCharry/serie76-assistant/wiki/Modelo-entidad-relacion) |
| 4 | Qué ve y controla el usuario | [Chat](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Chat-activo), [historial](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Conversaciones) y [debug](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Developer-Debug) |
| 5 | Qué se midió y qué falta | [Resultados y límites](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites) |
| 6 | Demostración y preguntas de defensa | [Guion de sustentación](https://github.com/SamuelCharry/serie76-assistant/wiki/Guion-de-sustentacion) |

## Estado de la entrega

- **Implementado:** OCR local, catálogo SQL, agente de una decisión, Android nativo, login e historial por usuario.
- **Verificado en su alcance:** reproducción desde la etiqueta, 10/10 pasos; 795 pruebas Python aprobadas y 2 omitidas; 126 pruebas JVM Android aprobadas.
- **Límite principal:** el candidato medido aprobó en promedio 79,4 % de las conversaciones v17. Las reparaciones posteriores tienen evidencia offline, sin una nueva medición pagada independiente.
- **Pendiente:** reconocimiento de voz real y validación física; acceso de evaluadores y correo. El autor no dispone actualmente de un Android físico.

[Checklist del assessment](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/SUBMISSION.md) · [Inicio rápido](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.es.md#quick-start)
