# Configuración base · Android

App nativa en Kotlin con Jetpack Compose. El ViewModel controla estado; el repositorio encapsula HTTP y permite pruebas con respuestas controladas.

El [diseño de la app](https://github.com/SamuelCharry/serie76-assistant/wiki/Diseno-de-la-app) explica por qué se separaron esas responsabilidades y cómo se eligieron las tarjetas, las preguntas y los controles de voz.

| Capa | Responsabilidad |
|---|---|
| Compose | Login, conversaciones, chat, tarjetas, comparación y debug |
| ViewModel | Carga, errores, acciones, borrado pendiente y ciclo de voz |
| Repository | HTTP autenticado, historial y contratos de respuesta |
| FastAPI | Propiedad, interpretación, SQL y persistencia |

Base verificada: **JDK 17, SDK Platform 36**; app para API 26+. En el emulador, el backend del equipo se alcanza mediante `http://10.0.2.2:8000/`. El teléfono físico necesitaría otra ruta; no está validado aquí.

No hace falta dispositivo físico para demostrar compilación, pruebas JVM, navegación y HTTP en emulador. Eso no acredita reconocimiento de micrófono ni legibilidad física.

[Quick start](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.es.md) · [Código Android](https://github.com/SamuelCharry/serie76-assistant/tree/main/mobile/android/app/src/main/java/com/serie76/assistant) · [Resultados](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites)
