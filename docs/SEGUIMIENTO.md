# Seguimiento del proyecto

Repositorio: https://github.com/SamuelCharry/serie76-assistant (privado).

| Grupo | Milestone | Issue | Estado |
|---|---|---|---|
| 1. Entorno y entrega | [M1](https://github.com/SamuelCharry/serie76-assistant/milestone/1) | [#1](https://github.com/SamuelCharry/serie76-assistant/issues/1) | En curso: Python listo; Docker pendiente; entrega al final |
| 2. Datos, OCR y modelos | [M2](https://github.com/SamuelCharry/serie76-assistant/milestone/2) | [#2](https://github.com/SamuelCharry/serie76-assistant/issues/2) | Próximo: OCR de primera página |
| 3. Backend y agente | [M3](https://github.com/SamuelCharry/serie76-assistant/milestone/3) | [#3](https://github.com/SamuelCharry/serie76-assistant/issues/3) | Pendiente |
| 4. Contrato API | [M4](https://github.com/SamuelCharry/serie76-assistant/milestone/4) | [#4](https://github.com/SamuelCharry/serie76-assistant/issues/4) | Pendiente |
| 5. Android | [M5](https://github.com/SamuelCharry/serie76-assistant/milestone/5) | [#5](https://github.com/SamuelCharry/serie76-assistant/issues/5) | Pendiente |
| 6. Documentación y reproducibilidad | [M6](https://github.com/SamuelCharry/serie76-assistant/milestone/6) | [#6](https://github.com/SamuelCharry/serie76-assistant/issues/6) | Parcial; verificar producto completo al final |
| 7. Login y voz | [M7](https://github.com/SamuelCharry/serie76-assistant/milestone/7) | [#7](https://github.com/SamuelCharry/serie76-assistant/issues/7) | Opcional, diferido |

## Evidencia del primer paso — 2026-11-02

- Repositorio publicado y clon verificado en el PC de Samuel.
- Entorno .venv creado desde cero; requirements.txt instalado y pip check sin incompatibilidades declaradas.
- Renderizado de página 1 a 300 DPI ejecutado usando ese entorno: data/ocr/page1-clean-venv. Es renderizado, no reconocimiento OCR.
- Android Studio, Android SDK y adb localizados. No se compiló ni ejecutó una app.
- Se intentó iniciar Docker Desktop. El proceso terminó y docker info no pudo conectar con dockerDesktopLinuxEngine. Los registros muestran cierre del backend; no permiten atribuir una causa concreta con la evidencia revisada. No se construyeron contenedores.
- Sin llamadas a OpenRouter.

## Siguiente acción

Resolver arranque de Docker o instalar un motor Tesseract local, ejecutar OCR sobre página 1 y revisar sus errores antes de reconstruir tablas. No avanzar aún al agente.

Estos siete grupos conservan la clasificación del assessment; no son una secuencia rígida. El grupo 1 incluye la entrega final y el grupo 6 se actualiza durante el trabajo. No cerrar un milestone mientras conserve tareas obligatorias pendientes.
