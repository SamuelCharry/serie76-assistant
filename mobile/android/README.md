# Series 76 Android

Aplicación Kotlin + Jetpack Compose. Abrir esta carpeta en Android Studio.

Desde la raíz del repositorio:

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug
./mobile/android/gradlew.bat -p mobile/android :app:testDebugUnitTest
```

URL predeterminada: http://10.0.2.2:8000/. Modificar con -PbackendUrl=<URL> y recompilar.

Tras iniciar sesión, chat con Hello centrado y fondo de ondas Konecto. Menú izquierdo con historial propio, New chat, perfil de cuenta y Sign out; Appearance ofrece Light, Dark y System. La selección se guarda y conserva la preferencia del switch anterior. Rethink Sans incluida, compositor delineado y texto de espera animado. Las sugerencias iniciales y etiquetas redundantes fueron retiradas por solicitud del usuario.

Debug de herramientas: variante debug, abrir el menú izquierdo y pulsar Developer debug; requiere DEV_DEBUG=true y solo permite respuestas del propietario. Excluido de release. Login email/password con token cifrado y aislamiento de historial; sin voz. Ver [AUTH.md](../../docs/AUTH.md).

Instrucciones completas de SDK, backend, dispositivo, URL, debug, contratos y límites: [docs/ANDROID.md](../../docs/ANDROID.md).

No hay respuestas simuladas en la aplicación. La verificación con un LLM real queda pendiente de configurar/evaluar OpenRouter; evidencia en [https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/mobile](../../docs/evidence/mobile.md).
