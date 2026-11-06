# Cómo usé IA durante el desarrollo

Usé IA para escribir código, preparar pruebas, revisar fallos y trabajar la documentación. Claude Code coordinó parte del trabajo y Codex implementó y revisó cmbios mediante Orca. La [configuración del proyecto](https://github.com/SamuelCharry/serie76-assistant/tree/main/.claude) está incluida en la entrega.

Aquí la IA aparece en dos lugares distintos: como ayuda para desarrollar el proyecto y como modelo que interpreta preguntas dentro de la app. Que un asistente escriba una prueba no demuestra que el producto funcione; por eso se guardaron resultados, comparaciones y reproducciones.

Esta cronología resume hitos del historial Git y de los informes. No reconstruye cada prompt ni atribuye cada línea de código a una persona o modelo.

## 2 de noviembre · Dividir el problema

El trabajo comenzó con la estructura del proyecto, un experimento de extracción y una división por hitos. Se dejó contexto para continuar con otro agente sin empezar de cero. La IA ayudó a convertir el assessment en tareas concretas: datos, backend, app y pruebas. También creamaos issues para poder seguir el trabajo en github.

[Inicio del proyecto](https://github.com/SamuelCharry/serie76-assistant/commit/d1604bd) · [Primer relevo](https://github.com/SamuelCharry/serie76-assistant/commit/a048e41).

## 3 de noviembre · Construir sobre datos verificables

Quedó implementada la ingesta OCR local y se conectaron catálogo, backend y Android. Se exploraron alternativas de arquitectura y se eligió el agente de una decisión, con validación y respuestas construidas por código. También se añadieron login e historial por usuario.

La IA ayudó con la implementación y las comprobaciones. El resultado importante era contrastar la extracción con el PDF, no aceptar la afirmación del asistente de que estaba bien.

[Ingesta validada](https://github.com/SamuelCharry/serie76-assistant/commit/b0c02ac) · [Agente elegido](https://github.com/SamuelCharry/serie76-assistant/commit/d87a25e).

## 4 de noviembre · Probar conversaciones, no solo preguntas sueltas

El foco pasó a conservar requisitos entre turnos, resolver referencias y mejorar preguntas, tarjetas, voz y debug. Se añadió recuperación de ejemplos de interpretación. Las revisiones encontraron casos donde esa ayuda podía interferir con condiciones explícitas; se ajustó para que solo completara lo que faltaba.

La IA se usó tanto para desarrollar como para buscar contraejemplos. Estos fallos se convirtieron en pruebas repetibles.

[Recuperación aditiva](https://github.com/SamuelCharry/serie76-assistant/commit/1b46e75) · [Revisión y correcciones](https://github.com/SamuelCharry/serie76-assistant/commit/9b61569).

## 5 de noviembre · Separar errores del modelo y errores del código

Se prepararon pruebas con decisiones ya fijadas: si el código falla incluso recibiendo una decisión correcta, cambiar el prompt no lo arregla. Esto permitió reparar filtros, referencias y ranking sin pagar una llamada al modelo por cada intento. También se documentó la elección del modelo y se probó el arranque desde un clon limpio.

[Pruebas para aislar fallos](https://github.com/SamuelCharry/serie76-assistant/commit/1e8551e) · [Correcciones posteriores](https://github.com/SamuelCharry/serie76-assistant/commit/859d560).

## 6 de noviembre · Comparar, descartar y cerrar

Se compararon variantes con casos congelados y respuestas mezcladas para revisión ciega. Una propuesta de estado completo salió peor y se descartó. La mejora del diseño anterior sí aumentó la aprobación, pero también dejó fallos: se registraron y corrigieron, sin presentar las pruebas offline como una nueva medición del modelo.

La revisión asistida por IA se complementócon auditorías de valores contra el catálogo. Después se reprodujo la entrega desde su etiqueta.

Mi parte tambien incluyó decidir qué adoptar, autorizar gastos y probar la app fisicamente para poder generar incluso más pruebas y una interacción natural; el reconocimiento real con micrófono lo confirmé manualmente en el emulador también.

[Experimento descartado](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/SV2-experiment.md) · [Comparación final y reparaciones](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-A.md) · [Reproducción de la entrega](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/T18-tag-clean-clone.md).

## Qué me dejó esta forma de trabajar

La IA permitió avanzar rápido y probar más alternativas, pero también produjo propuestas que hubo que corregir o descartar. El criterio para conservar un cambio fue la evidencia disponible, con sus límites, no lo convincente que sonara su explicación.
