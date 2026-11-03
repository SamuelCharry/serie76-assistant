# Perfil local y apariencia

Extensión solicitada por el usuario sobre la dirección MOBILE_DIRECTION_V4.md. Mantener fondo Konecto, Rethink Sans, superficies y controles claros/oscuros. El chat y el backend no cambian.

El pie del drawer abre un menú nativo compacto de perfil. Muestra nombre/correo disponibles, estado local, acción Edit profile y apariencia Light, Dark, System. Sin identidad configurada muestra Profile/Local profile y No email added: no inventar cuenta, correo verificado ni autenticación. El usuario proporcionó literalmente 'name' para su ficha local; ese valor se instala en preferencias del dispositivo, nunca como identidad predeterminada versionada.

Edit profile abre un formulario corto de nombre y correo opcionales, valida el formato del correo y guarda al confirmar. Cancelar no modifica la ficha. La información permanece en el almacenamiento privado del dispositivo; no se envía al backend. La presentación recibe ProfileDetails y una acción de guardado, de modo que un proveedor de cuenta futuro pueda sustituir el almacenamiento local sin fingir una sesión hoy. Cambiar cuenta queda para una implementación posterior; no hay un botón sin acción.

La apariencia tiene tres valores persistidos. System sigue la configuración Android y es el valor inicial sin preferencia previa. Una elección antigua del switch Dark theme se conserva al actualizar; al seleccionar un modo se reemplaza el flag legado. El cambio no modifica sesión ni borrador.

Interacción: menú anclado al pie del drawer, cierre nativo por fondo/Atrás, controles de48dp, correo largo con ajuste de líneas en el menú y elipsis únicamente en el resumen del pie. El formulario admite teclado y desplazamiento. Resto de límites de V4 conservados: datos técnicos completos, fixtures solo en pruebas, sin validación del LLM por esta extensión.
