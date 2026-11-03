# Android Editorial A

Base anterior publicada en `main`, commit `7f69e9c`. Rediseño en `design/android-editorial-v3`. El usuario conservó chat inicial/historial lateral y aprobó la composición A para toda la app con adaptación nativa.

Cambios: Rethink Sans400/500/600 incluida con licencia OFL; paleta Konecto blanca/ciruela/lila; saludo editorial, sugerencias en filas delineadas, compositor blanco, iconos de trazo fino y drawer con acción principal clara. Fichas, tablas, errores y depuración heredan el sistema sin cambiar los datos ni la API.

Movimiento: entrada de480ms desde contenido ya visible, regla que se extiende, flechas con respuesta de140ms al pulsar, colocación de filas y drawer nativos. Compose respeta la escala de animación del sistema; no hay bucles decorativos ni demoras artificiales.

Verificación: siete pruebas unitarias/contrato y seis instrumentadas pasan; debug y release compilan, release sin firma. Emulador Series76_API35 en `emulator-5554`, Android15. Capturas reales en `.impeccable/review/redesign-v3/`: inicio, drawer, recuperación, teclado, envío, producto con fuente130%, comparación, debug, error e historial vacío. Los dos últimos aíslan el componente del drawer en el host de pruebas; la topología completa se ve en `conversations.png`. La app instalada no contiene estos fixtures.

El compositor queda por encima del teclado nativo. Las capturas finales sustituyen la primera ronda, que había capturado el modo de escritura manual del emulador; desactivarlo para la comprobación no modificó la app. No se alteraron preferencias de animación.

La comparación automática marca78,95% y deriva; sus fallos se conservan. La aprobación de adaptaciones nativas no es un pase mecánico. `.impeccable/build/state.json` y `spec.json` se incluyen explícitamente en Git para conservar esta distinción y las mediciones.

Hashes y separación debug/release: [apk.json](apk.json). Resultados: [tests.json](tests.json). Dirección: [MOBILE_DIRECTION_V3](../../../docs/MOBILE_DIRECTION_V3.md).

Alcance: teléfono/light. No se probaron rendimiento en hardware físico ni el recorrido real app→LLM→SQL→app. El backend no cambió; no se añadieron autenticación, servicios, voz ni funciones de negocio.
