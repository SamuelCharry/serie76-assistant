# Verificación de Android y conversaciones

Ejecución local: 3 de noviembre de 2026. Implementación Kotlin/Compose y API persistente. No se usó OpenRouter; modelo y clave siguen sin configurar. No hay datos falsos ni respuestas de sustitución en el APK.

## Evidencia ejecutada

| Comprobación | Resultado | Límite |
|---|---|---|
| Construcción debug y release, incluida reducción R8 | Correcta | Release sin firma de distribución |
| Unit tests Android | 6/6 | Repositorio controlado y servidor HTTP local de prueba |
| Pantallas en Android 15/API35 | 6/6 | Teléfono emulado; fixtures solo en androidTest |
| Conversaciones backend | 9/9 | SQL real; routing controlado, adaptador HTTP probado contra servidor local |
| Regresión de catálogo PostgreSQL | 19/19 | No sustituye la evidencia OCR previa |
| Persistencia tras reiniciar DB/backend | Correcta | Dos mensajes y dos snapshots recuperados por HTTP; sin modelo real |
| Debug fuera de release | Verificado por source sets y cadenas DEX | No equivale a una auditoría exhaustiva del APK |

tests.json resume resultados; backend.json registra el reinicio; apk.json registra hashes/tamaños y comprobación DEX. Los fixtures no se incluyen en la app principal. El primer intento de UI sobre Android 17 preliminar falló dentro de Espresso antes de probar pantallas; se repitió correctamente con API35 estable.

## Capturas reales de Compose en emulador

- [Conversaciones](../../.impeccable/review/conversations.png)
- [Sin conversaciones](../../.impeccable/review/conversations-empty.png)
- [Backend inaccesible](../../.impeccable/review/backend-error.png)
- [Teclado y compositor](../../.impeccable/review/chat-keyboard.png)
- [Chat después de enviar](../../.impeccable/review/chat-sent.png)
- [Ficha con fuente al 130 %](../../.impeccable/review/product-font130.png)
- [Comparación](../../.impeccable/review/comparison.png)
- [Debug](../../.impeccable/review/developer-debug.png)

Son capturas completas 1080×2400 de instrumentación Android, no renders web ni imágenes generadas. Las conversaciones y trazas visibles son fixtures de prueba; las cifras de producto del fixture corresponden a ejemplos del catálogo. La comprobación TalkBack automatizada valida la asociación producto/atributo/valor/unidad por semántica, no una sesión manual completa con lector de pantalla.

La maqueta C generada con imagegen fue aprobada antes de programar. Las capturas registran su traducción a componentes Android y contenido dinámico; no se rasterizaron texto ni controles. La dirección y adaptaciones están en docs/MOBILE_DIRECTION.md. El comparador automático pasó de 70.3 % a 76.91 % global tras ajustes y conserva flags regionales: no es un pase automático. El usuario aprobó después explícitamente la adaptación nativa y sus diferencias con C; esa aceptación cerró hero mediante override registrado. Véanse .impeccable/review/native-approval.json, native-adjudication.md, diff/hero y hero-before-fixes. La revisión nativa independiente evalúa los cambios de jerarquía, contexto, accesibilidad y alcance.

## Pendiente

- Seleccionar/configurar un modelo OpenRouter, medir costo/calidad y probar lenguaje/contexto de extremo a extremo.
- Validar uso físico, TalkBack manual y comportamiento en dispositivos reales.
- La comprobación visual mecánica regional conserva discrepancias aceptadas expresamente por el usuario; no se presenta como un pase automático.
- La entrega externa, firma de distribución y acceso de evaluadores no se realizaron.

Instrucciones reproducibles: ../../docs/ANDROID.md. No hubo commit/push, cambios de visibilidad ni envío externo.
