# Series 76 Android

Aplicación Kotlin + Jetpack Compose. Abrir esta carpeta en Android Studio.

Desde la raíz del repositorio:

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug
./mobile/android/gradlew.bat -p mobile/android :app:testDebugUnitTest
```

URL predeterminada: http://10.0.2.2:8000/. Modificar con -PbackendUrl=<URL> y recompilar.

Inicio directamente en chat; menú izquierdo con historial y New chat. Estilo tipo Gemini aprobado, acento lila Konecto y compositor tonal. Los accesos iniciales solo preparan el borrador.

Debug de herramientas: variante debug, abrir el menú izquierdo y pulsar Developer debug; requiere DEV_DEBUG=true en el backend local. Excluido de release. Sin login ni voz.

Instrucciones completas de SDK, backend, dispositivo, URL, debug, contratos y límites: [docs/ANDROID.md](../../docs/ANDROID.md).

No hay respuestas simuladas en la aplicación. La verificación con un LLM real queda pendiente de configurar/evaluar OpenRouter; evidencia en [reports/mobile](../../reports/mobile).
