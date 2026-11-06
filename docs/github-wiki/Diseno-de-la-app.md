# Cómo diseñé la app

La app tenía que hacer algo más que mostrar respuestas en un chat. El escenario del assessment era un equipo de ingeniería que consulta tablas, compara actuadores y vuelve a preguntas anteriores. A partir de ahí, el diseño se centró en que los datos fueran fáciles de revisar y que el usuario no perdiera el hilo de lo que estaba buscando.

## Del problema a la interfaz

**Comparar sin leer párrafos largos.** Las cifras aparecen en tarjetas y, al comparar dos modelos, en una tabla con los mismos campos. Las filas iguales se pueden desplegar para no ocupar toda la pantalla. Una ventaja en una cifra no se presenta como una recomendación universal: el criterio de comparación importa.

**Completar requisitos sin mostrar un formulario enorme.** La app presenta una pregunta a la vez y permite revisar las respuestas antes de pulsar Submit. Elegir una opción no envía una petición por sí solo. Esto ayuda a organizar la consulta, aunque añade pasos cuando el usuario ya sabe exactamente lo que necesita.

**Retomar el trabajo.** El historial permite abrir una conversación anterior con sus mensajes y contexto. Así, una consulta sobre un modelo no obliga a volver a copiar el código completo cada vez.

**Poder corregir una acción.** El borrado ofrece Undo durante cinco segundos, antes de enviar la eliminación al servidor. La voz también pasa por una revisión: primero queda como texto editable y solo se envía cuando el usuario pulsa Send. Son dos formas de evitar que un gesto accidental o una transcripción incorrecta se conviertan inmediatamente en una acción definitiva.

**Separar uso normal e inspección técnica.** El chat muestra productos y explicaciones. El debug se abre por respuesta y queda oculto detrás del gesto documentado en el README. Eso mantiene limpia la conversación, a cambio de tener que explicar cómo acceder a él. Ocultarlo no lo protege por sí solo: el backend comprueba autenticación y propiedad.

## Los patrones que sí están en el código

### ViewModel y flujo de estado

La organización sigue un enfoque MVVM: Compose muestra la interfaz, `AppViewModel` maneja las acciones y el estado, y el repositorio se encarga de hablar con la API. No todas las decisiones están en el ViewModel; la transcripción tiene su propio controlador.

La pantalla observa un `StateFlow` de solo lectura. Un toque llama a una acción del ViewModel, la acción actualiza el estado y Compose vuelve a dibujar lo que cambió. Ese recorrido facilita entender cuándo mostrar carga, conservar el borrador o presentar un error, sin repartir esas decisiones entre botones.

[AppViewModel](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/ui/AppViewModel.kt) · [Pantallas Compose](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/ui/Screens.kt).

### Repository e inyección por constructor

El ViewModel recibe una interfaz `ConversationRepository`. En la app, su implementación usa Retrofit; en las pruebas se puede sustituir por una que devuelve respuestas o errores controlados. Esto permite probar, por ejemplo, una petición que tarda o falla sin depender de que el servidor falle justo en ese momento.

La separación tiene un coste: hay interfaces y modelos que mantener. En este caso aporta una ventaja concreta para las pruebas, sin necesitar un framework de inyección ni presentar el proyecto como una arquitectura limpia completa.

[Interfaz e implementación HTTP](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt).

### Controlador de estados para la voz

`VoiceController` distingue reposo, escucha y espera del resultado final. Recibe un reconocedor sustituible, así que se puede probar sin micrófono. Además, identifica cada sesión de reconocimiento: si llega un resultado de una sesión cancelada, lo ignora.

Esto resuelve un problema muy visible para el usuario: que aparezca texto antiguo después de cambiar de conversación o empezar a escribir otra cosa.

[Controlador de voz](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/ui/VoiceController.kt).

## Dos ejemplos de cómo se fue ajustando

**Un envío falla y el usuario no sabe qué pasó.** Un timeout no garantiza que el servidor no haya guardado la respuesta. La app conserva el borrador y pide recargar el historial antes de reintentar, en vez de repetir automáticamente el POST. Las pruebas simulan el fallo y comprueban la recuperación. Es menos inmediato que reenviar, pero evita facilitar envíos duplicados.

[Pruebas de recuperación](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/test/java/com/serie76/assistant/RecoveryStateTest.kt).

**Llega una transcripción después de cancelar.** Se añadió cancelación al salir, cambiar de conversación o escribir, junto con el rechazo de callbacks antiguos. Las pruebas comprueban que esos resultados no sobrescriban el texto nuevo y que la voz nunca envíe sola el mensaje.

[Pruebas de voz](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/test/java/com/serie76/assistant/VoiceInputTest.kt).

## Qué hubo de design thinking

El proceso partió de una necesidad descrita en el assessment, la convirtió en tareas de uso y fue ajustando la interfaz al probarla. En ese sentido hubo un ciclo de entender el problema, proponer una solución, construirla y revisar lo que fallaba.

No hay entrevistas ni pruebas de usabilidad con ingenieros de planta documentadas en este proyecto. Por eso estas decisiones se presentan como hipótesis de diseño apoyadas en el escenario y en pruebas de funcionamiento, no como conclusiones de investigación con usuarios. El reconocimiento real de voz sí lo probé manualmente en el emulador; eso tampoco sustituye una prueba de uso en campo.

El siguiente paso sería observar a alguien consultar y comparar modelos sin explicarle la interfaz: dónde duda, qué información busca y si entiende las preguntas. También falta revisar legibilidad y accesibilidad en un dispositivo físico. Esas observaciones permitirían saber si las decisiones realmente ayudan, más allá de que el flujo pase sus pruebas.
