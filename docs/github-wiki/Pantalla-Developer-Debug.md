# Pantalla · Developer Debug

Permite explicar **una respuesta concreta**: herramienta, parámetros, validaciones, datos y tiempos disponibles en su traza. No expone el razonamiento privado del modelo.

1. Configura `DEV_DEBUG=true` en el backend.
2. Toca el nombre/correo del perfil **siete veces en tres segundos**.
3. Pulsa el icono de información de una respuesta.

La traza se carga a demanda y está disponible para respuestas guardadas. El gesto solo oculta la interfaz: la protección real es el token, la comprobación del propietario y la configuración del servidor.

Para verificarlo, consultar la potencia del código completo y revisar su ruta determinista. La presencia de una traza no implica que se llamó al modelo; `llm_called` distingue ese caso.

[Endpoint](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/api.py) · [Evidencia de emulador](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-D.md)
