# Series 76

Este proyecto nació de una tarea concreta: consultar las tablas de actuadores sin tener que buscar cada dato a mano. La app permite preguntar por un modelo, comparar opciones y retomar una conversación.

La idea que guía el backend es sencilla: el modelo ayuda a entender la pregunta; los datos técnicos salen del catálogo. Aquí cuento cómo lo construí y por qué elegí ese camino.

## Índice

### Parte A · Backend

- [Arquitectura: cómo se conectan las piezas](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura)
- [Del PDF al catálogo](https://github.com/SamuelCharry/serie76-assistant/wiki/Pipeline-de-ingesta)
- [PostgreSQL y Docker](https://github.com/SamuelCharry/serie76-assistant/wiki/Base-de-datos-y-Docker)
- [Modelo de datos](https://github.com/SamuelCharry/serie76-assistant/wiki/Modelo-entidad-relacion)
- [El agente y sus herramientas](https://github.com/SamuelCharry/serie76-assistant/wiki/Agente-LangChain)
- [API e historial de conversaciones](https://github.com/SamuelCharry/serie76-assistant/wiki/API-REST-FastAPI)

### Parte B · App Android

- [Diseño de la app: interacción, patrones e iteraciones](https://github.com/SamuelCharry/serie76-assistant/wiki/Diseno-de-la-app)
- [Configuración de la app](https://github.com/SamuelCharry/serie76-assistant/wiki/Configuracion-base-Android)
- [Lista de conversaciones](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Conversaciones)
- [Chat y comparación de productos](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Chat-activo)
- [Qué muestra el debug](https://github.com/SamuelCharry/serie76-assistant/wiki/Pantalla-Developer-Debug)

### Parte C · Opcionales

- [Login e historial por usuario](https://github.com/SamuelCharry/serie76-assistant/wiki/Parte-C1-Login)
- [Entrada por voz](https://github.com/SamuelCharry/serie76-assistant/wiki/Parte-C2-Mensajes-de-voz)

### Cómo lo construí

- [Las decisiones más importantes y sus motivos](https://github.com/SamuelCharry/serie76-assistant/wiki/Decisiones)
- [Cronología: cómo usé IA durante el desarrollo](https://github.com/SamuelCharry/serie76-assistant/wiki/Como-use-IA)
- [Pruebas, resultados y límites](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites)
- [Archivos de entrega y cómo ejecutar el proyecto](https://github.com/SamuelCharry/serie76-assistant/wiki/Documentacion-y-entrega)

Para probarlo, el punto de entrada es el [README](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.md). La [checklist detallada](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/requirements.md) relaciona cada requisito del assessment con su implementación.
