# Login e historial por usuario: evidencia

## Implementado

FastAPI/PostgreSQL: cuentas con hash de contraseña, tokens opacos con digest y expiración, logout revocable, límites persistidos y propietario en todas las rutas de historial/contexto/continuación/trazas. Migración aditiva sin borrar ni asignar automáticamente el historial antiguo. Catálogo compartido sin cambiar cifras.

Android: login nativo, token cifrado con Android Keystore, validación /me antes de mostrar contenido, perfil real y Sign out. ViewModels del chat destruidos al salir/expirar; una respuesta tardía de otra sesión no puede cerrar la nueva. Temas y fondo ambiental conservados. Documentación: `docs/AUTH.md` y `docs/MOBILE_AUTH_DIRECTION.md`.

## Verificado

- 37 pruebas Python de autenticación, conversación y catálogo contra PostgreSQL real, con rollback de datos de prueba. Incluyen contraseña incorrecta, usuario desconocido/inactivo, expiración, revocación, límites persistidos y contención de filas del limitador; acceso cruzado prohibido por UUID, listado, contexto, continuación y trazas. `backend-tests.txt`.
- 14 pruebas JVM Android y15 pruebas Compose:29 casos distintos, sin errores ni omisiones. El pase amplio inicial tenía13JVM/15Compose; después se añadió y aprobó el caso de restauración tardía en la suite JVM final. Capturas repetidas de3 casos y un menú no se cuentan como casos nuevos. `android-tests.json`, `android-tests.txt`, `android-final-build.txt`.
- 1 prueba nativa adicional con dos cuentas reales: login → historial propio → reapertura → perfil → logout, repetido con la segunda cuenta. API HTTP y SQL operativos; conversaciones marcadas y creadas solo para verificación, sin interpretación del modelo. `android-live.txt`. Total Android:30 casos distintos.
- Prueba HTTP real: dos usuarios, aislamiento, historial antiguo sin dueño,401 anónimo,404 ajeno, token expirado, revocación y supervivencia de token/historial al reiniciar backend. `http-isolation.json`.
- La instantánea preparada para commit se exportó aparte para excluir cambios paralelos del agente y superó18 pruebas de autenticación/conversación. Después se hizo robusta una aserción del limitador ante filas expiradas de otros ensayos y se repitió su caso:1/1. `staged-backend-tests.txt` y `staged-targeted-test.txt`. Son repeticiones, no casos adicionales. `products-history.json` confirma además recuperación autenticada de2 mensajes y2 productos SQL, con routing controlado.
- APK debug/release compilados. Release sin firmar; hashes en `apk.json`. Instalado debug en Series76_API35 (Android15), no dispositivo físico. Native MainActivity mantiene FLAG_SECURE; solo la instancia de instrumentación lo retiró para capturas sin contraseñas.
- Capturas finales `.impeccable/review/auth-v7/live/`: login y menús de Demo1/Demo2 con su propio historial. `fixtures/`: login claro, oscuro a130% y menú oscuro con identidad sintética. Las primeras capturas del menú se tomaron antes del render de la ventana nativa; se corrigió la espera en el helper de pruebas y se sustituyó la evidencia. No se cambió el diseño por ese desfase.

## Reproducir

Backend y cuentas: seguir `docs/AUTH.md`; mantener `.cache/auth-demo-credentials.json` fuera de Git y reportes.

```powershell
$env:SERIES76_TEST_DB='1'
./.venv-chat/Scripts/python.exe -m unittest tests.test_auth tests.test_conversations tests.test_catalog_db -v
./.venv-chat/Scripts/python.exe scripts/verify_auth_backend.py --restart-backend
$env:ANDROID_SERIAL='emulator-5556'
./mobile/android/gradlew.bat -p mobile/android :app:testDebugUnitTest :app:connectedDebugAndroidTest :app:assembleRelease '-Pandroid.testInstrumentationRunnerArguments.notClass=com.serie76.assistant.LiveAuthTest'
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug :app:assembleDebugAndroidTest
./.venv-chat/Scripts/python.exe scripts/verify_android_auth.py --serial emulator-5556
```

Para LiveAuthTest, emulador con backend accesible por10.0.2.2:8000 y app sin sesión activa. El helper instala APKs, crea dos conversaciones con UUID propios, entrega credenciales mediante archivo privado del UID Android y elimina archivo/filas propias al terminar, incluso ante fallo. El reporte sanea contraseñas antes de escribir. Nunca borra otras conversaciones, usuarios ni volúmenes. LiveAuthTest se omite si se ejecuta sin su configuración privada; por eso el pase amplio lo excluye explícitamente y el pase real se registra aparte.

## Límites y estado final

No se probó interpretación real con OpenRouter ni se gastó presupuesto del modelo. Las pruebas controladas de creación/continuación con SQL no sustituyen esa aceptación. Tampoco certifican hardware físico, despliegue HTTPS público, rendimiento a gran escala ni voz. El catálogo y OCR conservan su validación anterior; los cambios paralelos de agente/glosario tienen evidencia independiente.

Las cuentas demo se conservan para uso local y no contienen conversaciones de verificación después de la limpieza. El historial anterior permanece sin dueño. Los archivos de credenciales no se versionan. No se trasladaron datos de usuario a una cuenta por deducción.

La app quedó abierta en login en el emulador. El intento de reconciliar las listas de los issues5/7 no se ejecutó: revisión automática de aprobación rechazó la acción con «blocked by policy». No se modificaron issues ni se enviaron comentarios; las condiciones verificadas se registran en estos documentos.
