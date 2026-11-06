# Las decisiones más importantes

Estas son las decisiones que más cambiaron el proyecto. Algunas vinieron del assessment; otras aparecieron al probar la app y encontrar fallos.

## 1. Primero resolver los datos

Antes de ajustar el agente, hacía falta saber que el catálogo estaba bien. El PDF mezcla servicios, frecuencias y celdas compartidas: copiar un número sin su contexto puede cambiar su significado. Por eso la ingesta conserva página, tabla, unidades y notas. Si una celda no se puede interpretar con seguridad, se deja para revisión.

PostgreSQL era un requisito del assessment. Lo usé para separar las especificaciones por servicio y frecuencia, y para consultar valores exactos. N/A no se convierte en cero. [Ingesta](https://github.com/SamuelCharry/serie76-assistant/wiki/Pipeline-de-ingesta).

## 2. Darle al modelo una tarea acotada

El modelo interpreta la petición y propone una herramienta con argumentos. El código valida esos argumentos, consulta SQL y arma la respuesta. Así, el modelo no tiene que recordar ni redactar las cifras del catálogo.

Eso tiene un coste: hay más reglas y plantillas que mantener. Y no elimina todos los errores; entender mal un requisito puede llevar a seleccionar el producto equivocado aunque sus cifras sean correctas. [Agente](https://github.com/SamuelCharry/serie76-assistant/wiki/Agente-LangChain).

## 3. No llamar al modelo cuando ya sabemos qué hacer

Consultar un campo de un código completo o enviar opciones elegidas en un formulario no necesita otra interpretación. Esas rutas se resuelven directamente. Para las preguntas abiertas quedó un solo agente y una decisión completada por turno.

La razón fue reducir llamadas, espera y puntos de fallo dentro de un presupuesto pequeño. No es una conclusión de que un agente siempre sea mejor que varios. Flash quedó por el equilibrio observado entre calidad y latencia; el fallback se dejó desactivado para mantener una configuración clara. [Comparación de modelos](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/wiki/en/testing.md#openrouter-model-selection).

## 4. Usar similitud para entender frases, no para buscar cifras

pgvector recupera ejemplos de cómo interpretar una petición. El catálogo numérico sigue en SQL. Los ejemplos pueden ayudar con un campo sin resolver, pero no deben borrar una condición explícita del usuario.

También se probaron variantes de recuperación que no dieron una mejora suficiente. No se incorporaron solo por ser más elaboradas. [Comparación de recuperación](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/wiki/es/testing.md#mejorar-la-recuperación).

## 5. Descartar una idea cuando la prueba salió mal

Se probó que el modelo devolviera todo el estado de la conversación en cada turno, en lugar de cambios sobre los filtros anteriores. Parecía una forma de reducir reglas, pero esa implementación aprobó 8 de 60 conversaciones frente a 42 de la anterior. Se conservó como experimento y no se llevó a la entrega.

La lección fue concreta: un esquema más pequeño no hace más sencilla la tarea del modelo. [Experimento de estado completo](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/SV2-experiment.md).

## 6. Separar una corrección de su medición

Los fallos encontrados se convirtieron en pruebas de regresión. Pero una vez usado un caso para corregir código, ya no sirve como prueba nueva de generalización. Por eso los resultados del candidato medido y las reparaciones posteriores se documentan por separado.

La mejora final se aceptó aun con regresiones nuevas, como excepción explícita al criterio inicial. Después se corrigieron offline; no se les atribuyó una puntuación real que no se volvió a medir. [Evaluación final](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-A.md).

## 7. Mantener el control en la interfaz

Las tarjetas facilitan comparar productos; el debug permite revisar de dónde salió una respuesta sin llenar el chat de detalles internos. La voz pasa primero por un editor: el usuario puede corregir la transcripción antes de enviarla. Android se encarga del reconocimiento y el backend recibe texto.

El [diseño de la app](https://github.com/SamuelCharry/serie76-assistant/wiki/Diseno-de-la-app) desarrolla estas decisiones, los patrones de código y dos ejemplos de cambios guiados por pruebas.

[Chat](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Chat-activo) · [Debug](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Developer-Debug) · [Voz](https://github.com/SamuelCharry/serie76-assistant/wiki/Parte-C2-Mensajes-de-voz).
