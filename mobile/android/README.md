# Series 76 Android

Aplicación Kotlin + Jetpack Compose. Abrir esta carpeta en Android Studio.

Desde la raíz del repositorio:

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug
./mobile/android/gradlew.bat -p mobile/android :app:testDebugUnitTest
```

URL predeterminada: http://10.0.2.2:8000/. Modificar con -PbackendUrl=<URL> y recompilar.

Inicio en chat con Hello centrado y fondo de ondas Konecto. Menú izquierdo con historial, New chat y Dark theme; la elección claro/oscuro se guarda localmente. Rethink Sans incluida, compositor delineado y texto de espera animado. Las sugerencias iniciales y etiquetas redundantes fueron retiradas por solicitud del usuario.

Debug de herramientas: variante debug, abrir el menú izquierdo y pulsar Developer debug; requiere DEV_DEBUG=true en el backend local. Excluido de release. Sin login ni voz.

Instrucciones completas de SDK, backend, dispositivo, URL, debug, contratos y límites: [docs/ANDROID.md](../../docs/ANDROID.md).

No hay respuestas simuladas en la aplicación. La verificación con un LLM real queda pendiente de configurar/evaluar OpenRouter; evidencia en [reports/mobile](../../reports/mobile).
