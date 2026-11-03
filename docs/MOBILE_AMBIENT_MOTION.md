# Movimiento ambiental del chat

Extensión de la versión visual inicial aprobada (`6e82513`, normalización de evidencia `2af3cde`). No cambia navegación, perfil, contrato HTTP ni base de datos.

## Decisión visual

El inicio vacío conserva la luz difusa y la malla original Konecto. Doce partículas violetas pequeñas recorren órbitas suaves: radios 1,1–1,8dp, desplazamientos máximos 10dp horizontales/14dp verticales, ciclo de 32 segundos. La malla tiene deriva máxima de 3dp horizontal y 4dp vertical. El texto y el compositor permanecen quietos. Sin física, conexiones entre partículas, ruido aleatorio por cuadro, desenfoques ni nuevas dependencias.

El efecto expresa una presencia tranquila al llegar al chat. Desaparece al escribir o leer resultados, mientras carga/envía, ante un error del historial y al abrir el panel lateral. Las transiciones y el saludo existente conservan su comportamiento.

## Presupuesto y suspensión

- Reloj acotado a una actualización cada 50ms como máximo (20/s), ciclo de 32s. No es un objetivo de 60/120fps.
- Estado leído solo en Canvas y graphicsLayer; no recompone ni recalcula el layout del chat en cada actualización. La geometría vectorial permanece en su capa.
- `repeatOnLifecycle(RESUMED)` cancela el reloj al perder el estado activo; se cancela también al desmontar el composable.
- Pausa con ahorro de batería de Android y con `ANIMATOR_DURATION_SCALE=0`, observados mientras la pantalla está montada. Conserva una imagen quieta sin temporizador; retoma sin recuperar el tiempo transcurrido en segundo plano.
- Sin red, sensores, servicio, wake lock, base de datos ni temporizadores de fondo.

El límite de trabajo y las pausas reducen actividad innecesaria; no equivalen a una medición de consumo energético. Las mediciones de batería y suavidad en hardware físico siguen pendientes.

## Implementación y verificación

`AmbientMotion.kt` contiene política de energía y reloj ligado al ciclo de vida; `ChatBackdrop.kt`, dibujo/capa; `Screens.kt`, visibilidad según el estado real del chat. `MotionText.kt` comparte el observador existente del ajuste Android. No se introducen datos ni controles de usuario adicionales.

Pruebas y capturas de esta extensión se registran en `reports/mobile/ambient-v6/`. Mantener separados resultados de emulador, datos de prueba y validación real app → modelo → SQL → app.

Referencias: [fases de Compose y lectura diferida del estado](https://developer.android.com/develop/ui/compose/performance/phases), [coroutines y ciclo de vida](https://developer.android.com/topic/libraries/architecture/coroutines).
