# Perfil local y apariencia

Implementado: perfil editable al pie del historial, nombre y correo opcionales, validación del correo, guardado local y selección Light / Dark / System. System sigue Android; las elecciones del antiguo interruptor se conservan al actualizar. No hay autenticación ni cambio de cuenta.

Verificación en Series76_API35, Android 15:

- 9 pruebas JVM y 10 pruebas Compose aprobadas, sin errores ni omisiones: `tests.json` y `android-build.txt`.
- Tras ajustar superficie y radio del editor, se repitió su prueba de edición y validación: 1/1 aprobada, junto con assembleRelease: `android-editor-build.txt`.
- Capturas inspeccionadas en `.impeccable/review/profile-v5/`: menú claro/oscuro, formulario con teclado, ficha, historial e inicio. Los datos Example user y user@example.test son fixtures exclusivos de pruebas.
- Revisión visual final: ship; ningún arreglo material pendiente. Paleta V4, tipografía y fondo conservados.
- APK debug instalado y abierto en el emulador; nombre solicitado configurado en sus preferencias privadas. No se versionan datos personales como valores predeterminados. Hashes y tamaños en `apk.json`; APK release sin firmar.

Límites: no se probaron dispositivo físico, escala tipográfica ampliada, autenticación ni respuestas reales del LLM. Estas pruebas no certifican el backend. El correo local es información de presentación, no una dirección verificada.
