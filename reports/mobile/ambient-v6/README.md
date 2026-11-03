# Fondo ambiental: evidencia

Extensión de la base visual aprobada, conservada en `6e82513` / `2af3cde`. Implementación y decisiones: `docs/MOBILE_AMBIENT_MOTION.md`. Próximas funciones y dependencias: `docs/MOBILE_NEXT_STEPS.md`.

## Resultado verificado

- Android 15/API35, AVD Series76_API35. 9 pruebas JVM + 12 Compose: 21 aprobadas, cero errores/omisiones. `tests.json` y `android-build.txt`.
- Pruebas nuevas verifican que el reloj se detiene al ocultarlo, al bajar de RESUMED y al desactivar animaciones Android mientras está montado, y que retoma después.
- Debug instalado y abierto; release sin firmar compilado. Hashes en `apk.json`. El nombre local solicitado se conserva en preferencias del dispositivo, sin predeterminar una identidad en el código.
- Capturas nativas en `.impeccable/review/ambient-v6/`: inicio claro/oscuro, teclado, respuesta, historial y producto con fuente al130%. Motes y malla no cubren entrada ni resultados. Los datos de las pruebas son fixtures.
- Dos imágenes separadas por3s confirman cambios en la región inferior del inicio (`motion-a/b.png`); dos separadas por2s durante ahorro de batería permanecen iguales (`saver-a/b.png`). Comparación de píxeles excluye reloj/barra de estado.
- Muestras independientes de6s, sin grabación de pantalla: gfxinfo informa102 cuadros activos y0 durante ahorro. Son contadores del proceso en emulador, no una tasa certificada ni una medición de energía. `gfx-active.txt`, `gfx-saver.txt` y `runtime.json`.
- Ahorro activado por comandos Android con batería simulada desconectada. El formato inicial del parser de dumpsys no coincidía con API35; un pase corto independiente confirmó `Battery Saver is currently: ON` y `mSettingBatterySaverEnabled=true`, conservados en `power-policy.txt`. Se restauraron modo de ahorro y simulación de batería después.
- `preview.mp4` es una grabación posterior de8s del inicio real; no se usa para medir cuadros ni batería.

## Límites

El trabajo está limitado a12 círculos, una capa vectorial y máximo20 actualizaciones/s, con pausas de ciclo de vida, estado, movimiento reducido y ahorro. No se midieron consumo energético ni suavidad en dispositivo físico. Las capturas/pruebas no validan respuestas reales del LLM, login, voz ni aislamiento multiusuario. No se modificó PostgreSQL ni se consumió presupuesto de modelos.
