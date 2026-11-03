# Android Serie 76

Login email/password obligatorio en la versión actual; perfil de cuenta real, token cifrado con Android Keystore y Sign out con revocación. Cada cuenta recupera únicamente su historial. Configuración, usuarios de prueba, migración y límites: [AUTH.md](AUTH.md). El perfil local de las versiones visuales anteriores es histórico y no da acceso al backend.

Movimiento ambiental acotado: [MOBILE_AMBIENT_MOTION.md](MOBILE_AMBIENT_MOTION.md). Base visual, issues existentes y plan de opcionales con PostgreSQL: [MOBILE_NEXT_STEPS.md](MOBILE_NEXT_STEPS.md).

Kotlin/Jetpack Compose, interfaz en inglés y tres superficies: conversaciones guardadas, chat y Developer debug. Presentación vigente: Hello centrado, fondo de ondas Konecto y luz difusa. El perfil al pie del menú izquierdo reúne nombre/correo locales y Appearance: Light/Dark/System. Guarda la preferencia y conserva las elecciones del switch anterior. Rethink Sans local y compositor delineado. Sin accesos iniciales, slogan ni etiquetas de marca redundantes. Saludo por letras y Thinking animado solo durante envío, con alternativa estática según la escala de animación de Android. Dirección: MOBILE_DIRECTION_V4.md y MOBILE_PROFILE.md. Login local con FastAPI/PostgreSQL; sin Firebase ni voz. Ver AUTH.md.

## Requisitos y compilación

Android Studio, JDK 17 o 21, Android SDK Platform 36 y emulador/dispositivo API 26 o posterior. Internet para la primera descarga de dependencias. Versiones fijadas: AGP 8.13.1, Gradle Wrapper 8.13, Kotlin/Compose compiler 2.2.21 y Compose BOM 2025.10.01. Android Studio genera local.properties con la ruta del SDK; no se versiona.

Abrir mobile/android en Android Studio y ejecutar app. Alternativa desde la raíz en PowerShell:

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug
# adb está en <Android SDK>/platform-tools; añadirlo a PATH.
adb install -r mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

Abrir Series 76 desde el lanzador. Paquete debug: com.serie76.assistant.debug. No contiene datos de demostración ni respuestas simuladas.

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:assembleRelease
```

Release produce app/build/outputs/apk/release/app-release-unsigned.apk. No se introduce una clave de firma privada al repositorio. Para instalar release se necesita firma local; para evaluación puede ejecutarse debug. Release no contiene la implementación de debug y requiere HTTPS.

## URL del backend

La propiedad Gradle backendUrl se incluye al compilar. Cambiarla requiere recompilar e instalar. No hay pantalla adicional de configuración.

| Entorno | URL |
|---|---|
| Emulador estándar | http://10.0.2.2:8000/ (predeterminada) |
| Dispositivo USB con adb reverse | http://127.0.0.1:8000/ |
| Servidor HTTPS | URL HTTPS accesible completa |

```powershell
# USB: el backend puede seguir publicado solo en loopback.
adb reverse tcp:8000 tcp:8000
./mobile/android/gradlew.bat -p mobile/android :app:assembleDebug -PbackendUrl=http://127.0.0.1:8000/
adb install -r mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

localhost desde el emulador identifica a Android, no al PC. PostgreSQL nunca se conecta directamente al teléfono. HTTP se permite solo en debug para desarrollo local; release conserva la política HTTPS de Android.

## Preparar el backend

Con Docker Desktop activo, desde la raíz:

```powershell
# Solo si .env no existe: copiar .env.example y reemplazar POSTGRES_PASSWORD.
docker compose up -d --build db backend
docker compose exec -T backend python -m backend.catalog.cli migrate
docker compose exec -T backend python -m backend.catalog.cli load data/extracted/series76
docker compose exec -T backend python -m backend.catalog.cli status
```

Más información: POSTGRES.md. No borrar volúmenes para reiniciar.

Para interpretar lenguaje real, configurar OPENROUTER_API_KEY y OPENROUTER_CHAT_MODEL en .env y recrear backend con docker compose up -d backend. OPENROUTER_BASE_URL es configurable. La selección/evaluación del modelo queda pendiente por instrucción del usuario; no se asigna uno sin evaluación ni se consume presupuesto en estas pruebas. Sin configuración, listar/abrir historial funciona y enviar devuelve un error controlado; no hay respuesta falsa de sustitución. No se necesitan embeddings.

Se utiliza langchain-openai con el contrato estándar Chat Completions de OpenRouter, sin campos de razonamiento ni extensiones. La integración langchain-openrouter disponible durante esta ejecución exigía una versión de Pydantic incompatible con el runtime fijado. Se preservó el runtime PostgreSQL; este compromiso debe reevaluarse al seleccionar el modelo.

## Acceso a debug

El pie del menú izquierdo abre el perfil local: nombre/correo editables y Appearance → Light / Dark / System. System vuelve a seguir la configuración Android; el modo se guarda y conserva las elecciones del switch anterior al actualizar. La ficha no es una cuenta autenticada y no altera el contrato backend. Ver MOBILE_PROFILE.md.

1. Instalar la variante Android debug.
2. Configurar DEV_DEBUG=true en .env del backend local y ejecutar docker compose up -d backend.
3. Abrir el menú izquierdo del chat y pulsar Developer debug al pie del panel.
4. Elegir una respuesta: se muestran herramienta, parámetros validados y datos devueltos; se indica si no hubo llamadas.

DEV_DEBUG es false por defecto: endpoint 404, fuera de OpenAPI. Es una opción local de desarrollo, no autenticación para un despliegue público. Release excluye pantalla, botón y cliente de trazas mediante source sets separados. Ningún APK incluye claves OpenRouter o credenciales DB. No se exponen cadenas de razonamiento.

## Arquitectura y compromisos

UI Compose -> ViewModel/StateFlow -> ConversationRepository -> Retrofit/OkHttp -> FastAPI -> PostgreSQL. Un módulo Android e inyección por constructor. DTOs separados de presentación; números JSON conservados como contenido decimal, sin pasar por Double.

El modelo selecciona una herramienta LangChain a partir del historial reciente y contexto persistido. Código valida parámetros, consulta SQL y redacta los datos técnicos desde resultados reales. Una llamada de modelo por turno, timeout 45 s, máximo 600 tokens de salida y sin reintentos automáticos. Evita una segunda generación que altere cifras y reduce gasto, a cambio de prosa más limitada. No demuestra comprensión universal de lenguaje.

Se envían hasta 12 mensajes recientes y se conservan aparte los últimos códigos/filtros. No se garantiza recuperar cualquier detalle narrativo arbitrariamente antiguo. Cada turno y sus snapshots de producto/trazas se guardan transaccionalmente; un fallo no deja mensajes huérfanos. Bloqueo por sesión entre procesos: una segunda petición simultánea recibe 409. Máximo cuatro interpretaciones concurrentes por proceso; exceso 503. No se presenta este ejercicio local de un usuario como servicio público ilimitado.

Una ficha delineada para un producto, tabla de etiquetas fijas para varios. Unidades, servicio, frecuencia, N/A, datos no publicados y notas conservan su significado. Potencia de motor no se etiqueta como consumo total; valores compartidos no se duplican como mediciones independientes.

ModalNavigationDrawer mantiene el chat montado mientras presenta el historial: cerrar por Atrás, gesto o scrim conserva sesión/borrador. Las filas muestran título/fecha y resaltan la sesión activa. Abrir el menú actualiza el listado existente; seleccionar una sesión conserva el contrato backend. Los accesos Look up a part/Find an actuator rellenan el borrador y enfocan el mismo compositor; nunca envían solos. Atrás desde el chat raíz mantiene el comportamiento nativo de salir de la actividad.

La app impide dobles envíos y cambiar de conversación mientras espera una respuesta; Atrás hacia la lista funciona. Tras un fallo conserva el borrador y exige recargar historial, o revisar la lista si no se recibió session_id. Un timeout no garantiza cancelación del servidor: revisar si ya existe respuesta antes de reenviar. No hay reintentos POST automáticos.

ViewModel conserva solicitudes durante rotación. SavedStateHandle restaura sesión/borrador ante recreación de proceso; el historial se recupera del backend. No se promete persistencia de borradores tras forzar cierre o reiniciar el dispositivo. No hay base local ni sincronización offline.

## Contratos

- POST /api/conversation: query de 1..4000 caracteres no vacía y session_id UUID opcional. Devuelve session_id, answer, message_id, products.
- GET /api/sessions?limit=50&offset=0: sessions con id, title, updated_at, created_at y preview. La UI permite cargar más.
- GET /api/sessions/{id}/messages?limit=100&before=<sequence>: mensajes cronológicos, has_more y next_before; sin trazas ni contexto interno.
- GET /api/messages/{id}/debug: message_id, session_id, tool_calls [{name, parameters, data}]. Requiere DEV_DEBUG=true.

Productos: identidad, alimentación, measurements, field_status, certificación, notas y procedencia pública. La UI no extrae números del texto answer. Los snapshots evitan que una importación posterior cambie conversaciones antiguas.

## Pruebas

```powershell
./mobile/android/gradlew.bat -p mobile/android :app:testDebugUnitTest
# Con teléfono emulado estable encendido:
./mobile/android/gradlew.bat -p mobile/android :app:connectedDebugAndroidTest

python -m venv .venv-chat
./.venv-chat/Scripts/python.exe -m pip install -r requirements-backend.lock.txt -r requirements-conversation.lock.txt
$env:SERIES76_TEST_DB='1'
./.venv-chat/Scripts/python.exe -m unittest discover -s tests -p test_conversations.py -v
./.venv-chat/Scripts/python.exe scripts/verify_mobile_backend.py --restart
```

Fixtures de pantalla solo en androidTest. Herramientas/SQL reales con interpretación controlada en pruebas backend; cero llamadas OpenRouter. El verificador de reinicio crea un registro marcado y limpia únicamente su propio UUID; no borra catálogo ni volúmenes. Evidencia y límites en reports/mobile.
