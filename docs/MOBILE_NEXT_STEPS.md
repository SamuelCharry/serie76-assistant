# Base visual y siguientes funciones

Actualización: el usuario seleccionó login y aislamiento por usuario. La implementación, migración y contrato vigentes están en [AUTH.md](AUTH.md); la voz sigue pendiente. Los planes de abajo conservan las dependencias y el historial de decisión, no sustituyen la evidencia en reports/mobile/auth-v7.

## Versión inicial conservada

Base visual aprobada y publicada en `design/android-editorial-v3`: `6e82513`, con evidencia normalizada en `2af3cde`. Perfil local editable, Light/Dark/System y fondo Konecto; 9 pruebas JVM y 10 Compose aprobadas. Evidencia en `reports/mobile/profile-v5/`. El movimiento posterior es una extensión separada: `MOBILE_AMBIENT_MOTION.md`.

## Issues existentes

Consultados el 3 de noviembre de 2026:

- [#5 Android nativo](https://github.com/SamuelCharry/serie76-assistant/issues/5): abierto. La descripción inicial aún dice que no hay proyecto compilable; necesita reconciliarse con la evidencia actual.
- [#7 Login y voz](https://github.com/SamuelCharry/serie76-assistant/issues/7): abierto; la descripción remota aún no refleja el login implementado. Voz sigue pendiente.
- [#6 Documentación y reproducibilidad](https://github.com/SamuelCharry/serie76-assistant/issues/6): abierto.

Los issues remotos no se modificaron: la revisión automática de aprobación rechazó su actualización con «blocked by policy». El estado implementado y su evidencia están en AUTH.md y reports/mobile/auth-v7. No cerrar capacidades integrales a partir de capturas o fixtures. La lista de aceptación sigue en `REQUISITOS.md`.

## Dependencia pendiente

Antes de aceptar los opcionales, alinear el proveedor real y verificar OpenRouter dentro del presupuesto autorizado. Ejecutar desde Android consulta, continuación contextual y reapertura después de reinicio. Verificar cifras, unidades, servicio, frecuencia y procedencia; preservar N/A. La evaluación Google no sustituye ese recorrido app → modelo → SQL → app. Marcar M03/M04 y dependencias solo con evidencia real.

Android consume FastAPI; PostgreSQL permanece detrás del backend. No incorporar credenciales SQL al APK ni conectar el teléfono directamente a la base de datos. Los experimentos de arquitectura conservan volumen y puerto separados.

## Login con la base existente: plan

1. Contrato email/password → token, duración, errores y cierre de sesión. Usuarios de prueba exigidos por el assessment. Sin registro, OAuth ni recuperación añadidos por defecto.
2. Migración aditiva de usuarios y propietario de conversación. Definir el destino del historial actual de usuario único: no borrarlo ni asignarlo silenciosamente al primer usuario nuevo. Preservar catálogo y procedencia.
3. Hash de contraseñas en backend y secretos por entorno. Validar token y propietario en listado, mensajes, continuación y trazas; no confiar en user_id enviado por Android.
4. Login nativo, manejo seguro del token, expiración y salida. El perfil pasa a mostrar la cuenta real; editar una ficha local nunca cambia identidad o permisos.
5. Pruebas con dos usuarios: acceso cruzado prohibido por listado e identificador, token inválido/expirado, salida sin mostrar historial previo, migración/reinicio sin perder datos.

Firebase no es necesario para esta propuesta. Añadir otro proveedor requeriría una decisión explícita; la ficha local no equivale a autenticación. No se implementó login en el bloque visual.

## Voz: plan acotado

1. Elegir transcripción en dispositivo o alternativa permitida; documentar idiomas, red y presupuesto. No prometer funcionamiento offline sin probarlo.
2. Micrófono bajo acción explícita; estados de grabación, cancelación y permiso denegado. Transcripción revisable antes de enviar al contrato actual; no grabar de fondo.
3. Comprobar números de parte, cifras y unidades pronunciados. Permitir corrección; no convertir transcripción dudosa en dato técnico válido.
4. Documentar privacidad y descarte del audio; verificar interrupciones y permisos en hardware físico. OpenRouter, si se usa, comparte el presupuesto existente.

Prioridad elegida: login y aislamiento de conversaciones por usuario. Ver AUTH.md y su evidencia; voz sin implementar. La aceptación del modelo sigue siendo independiente.
