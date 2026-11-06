# Pantalla · Conversaciones

Muestra el historial del usuario autenticado y permite crear o reabrir una conversación. El contexto se recupera del servidor: no depende solo de mantener abierta la app.

- **Nueva:** el primer envío no lleva `session_id`.
- **Reabrir:** carga mensajes y continúa con el identificador guardado.
- **Eliminar:** oculta la conversación y ofrece Undo durante cinco segundos; Undo cancela el DELETE pendiente. No restaura un borrado confirmado por servidor.
- **Error:** conserva una acción de reintento; cambiar de usuario no debe mostrar historial ajeno.

Para demostrarlo: crea una conversación con la consulta de 15 W, vuelve a la lista, reábrela y reinicia la app. El reinicio del backend también conservó el historial en T18.

[Repositorio Android](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt) · [Persistencia](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/store.py) · [T18](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/T18-tag-clean-clone.md)
