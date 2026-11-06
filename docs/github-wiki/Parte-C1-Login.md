# Login y aislamiento

La API autentica con correo y contraseña, devuelve un token opaco y verifica propiedad en cada acceso a historial o debug. La base guarda **hashes de contraseñas y tokens**, no los valores originales.

Contraseñas: PBKDF2-HMAC-SHA256 con salt y 600.000 iteraciones. El cliente envía Bearer. No se implementan registro público, recuperación de contraseña ni OAuth.

Las cuentas públicas del README son **TEST ONLY**. El arranque crea las que falten y nunca cambia contraseñas existentes.

**Prueba manual:** crea una conversación con un usuario, cierra sesión y entra con el otro. La conversación anterior no debe aparecer. El servidor también rechaza un identificador ajeno, aunque alguien lo conozca.

[Seguridad](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/auth/security.py) · [Pruebas](https://github.com/SamuelCharry/serie76-assistant/blob/main/tests/test_auth.py) · [Cuentas](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.md#demo-users-test-only)
