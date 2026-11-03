# Ambient chat: claro y oscuro

Refinamiento solicitado por el usuario: retirar accesos, slogan y marca redundante; centrar Hello; suavizar el morado; animar saludo y espera. Solicitud posterior: incorporar únicamente el fondo de Konecto y ofrecer ambos modos de color.

Implementado: fondo local con184 trazados originales y luz radial estática, sin webview ni peticiones de red. Las ondas desaparecen durante edición, envío y conversaciones pobladas; el campo de luz se atenúa. Textos, tarjetas, iconos y barras del sistema tienen paletas claras/oscuras. Dark theme en el drawer guarda un único flag de apariencia en SharedPreferences; antes de elegir sigue el sistema. La app no obtiene capacidades nuevas de negocio.

Hello aparece por letras en640ms. Thinking usa una onda de color de1500ms solo mientras hay envío pendiente. El observador de la escala de animación de Android sustituye ambos por texto estático cuando se desactiva el movimiento. La semántica accesible mantiene texto constante, sin anunciar cada cambio de color. No se simula razonamiento ni progreso del servidor.

Verificación final: siete pruebas unitarias/contrato y nueve instrumentadas pasan; debug y release compilan. Release sin firma. Android15/API35, emulador Series76_API35. La prueba de apariencia comprueba escritura de la preferencia y ambos estados del switch, restaurando su estado previo. La prueba de navegación comprueba el centro horizontal del saludo y la ausencia de los accesos retirados. Ver tests.json y android-build.txt. Se repitieron dos pruebas existentes para corregir capturas del host: drawer-check.txt y keyboard-check.txt. El resumen tests.json conserva la suite completa anterior a esas repeticiones individuales.

Quince capturas nativas en `.impeccable/review/ambient-v4/`. Dark-drawer, backend-error y conversations-empty aíslan el componente en el host; conversations muestra el drawer completo. Todas las conversaciones/productos de esas capturas son fixtures exclusivos de androidTest. No se precargan en la app.

Procedencia y adaptación vectorial: `.impeccable/references/konecto-wave-origin.json`, SVG original junto a él. Medidas de contraste declaradas en contrast.json. No se generan métricas de similitud contra el inicio V3: el usuario cambió expresamente esa composición y sus textos. El estado y las métricas V3 son históricos.

Límites: las capturas no prueban fluidez ni consumo en hardware físico; esta revisión UI no valida app→LLM→SQL→app. No hubo cambios backend ni llamadas al modelo para estas pruebas. Fuente/dirección: docs/MOBILE_DIRECTION_V4.md.
