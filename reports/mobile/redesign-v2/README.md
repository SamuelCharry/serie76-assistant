# Android: rediseño conversacional tipo Gemini

La dirección vigente es [MOBILE_DIRECTION_V2](../../../docs/MOBILE_DIRECTION_V2.md). Sustituye la composición C anterior por inicio en chat, historial en un drawer izquierdo, cabecera compacta, dos sugerencias que rellenan el borrador y compositor tonal. El usuario aprobó las maquetas Gemini y sus adaptaciones nativas; no exigió igualdad de píxeles.

## Cambios y motivos

- `ModalNavigationDrawer` mantiene el chat montado mientras se consulta el historial. Atrás, gesto y fondo cierran el menú; seleccionar una conversación recupera su contexto.
- ViewModel + StateFlow conservan navegación y borrador. El repositorio sigue separando HTTP de la presentación. No se añadieron capas ni servicios para un cambio visual.
- Las sugerencias preparan texto editable; enviar sigue siendo una acción explícita. Un envío pendiente bloquea cambiar de sesión.
- Las tarjetas técnicas usan borde fino y conservan códigos completos, unidades, servicio, N/A, notas y procedencia. La comparación mantiene etiquetas fijas y semántica por producto.
- Los controles de depuración permanecen en la variante debug. No se añadieron autenticación, Firebase, voz, búsquedas ni ajustes.

## Verificación

Gradle: `:app:testDebugUnitTest :app:connectedDebugAndroidTest :app:assembleRelease --no-daemon`. Siete pruebas unitarias/contrato y seis instrumentadas, cero fallos. Emulador aislado Series76_API35, Android 15/API35, teléfono 1080×2400. Compilación debug y release; release sin firma. Hashes y comprobación de textos/ruta debug en [apk.json](apk.json).

Capturas nativas en `.impeccable/review/redesign-v2/`: inicio, drawer, chat recuperado, teclado, envío, comparación, texto130%, depuración, error e historial vacío. Los ejemplos son fixtures de `androidTest`, nunca datos precargados en la app. La ventana de prueba reproduce edge-to-edge y adjustResize de MainActivity; no confundir problemas del host de pruebas con cambios en producción.

## Límites

La comparación automática con la maqueta conserva sus fallos: aproximadamente75% en el comp-diff final V2. El gate histórico59% se calculó por error contra una captura V1 y no mide la versión actual; la revisión lo detectó, se archivó y se regeneró hero/final con la captura V2 correcta. La aceptación de la adaptación nativa es una decisión del usuario, no una aprobación automática de fidelidad. Consultar `.impeccable/build/state.json` y `.impeccable/review/diff/` para los resultados originales.

Esta validación cubre la interfaz y los contratos con repositorio controlado. No demuestra el recorrido completo app→LLM→SQL→app, rendimiento en hardware físico ni una distribución firmada. La evaluación del modelo se registra por separado en `reports/model_eval/`.
