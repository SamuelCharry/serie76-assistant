# Verificación del scaffold

Fecha de trabajo: 2026-11-02. Esta evidencia corresponde al entorno local actual, no a una instalación limpia.

## Comprobado

- Los tres PDF fuente están copiados al repositorio.
- La referencia visual contiene 68 filas y conserva notas en JSON.
- Sintaxis de los cinco archivos Python válida.
- FastAPI /health responde 200 con stage=ocr-prototype.
- FastAPI /openapi.json responde 200.
- El contrato mínimo acepta query sin session_id.
- /api/conversation devuelve 404: no implementado, sin respuestas ficticias.
- Renderizado de página 1 completado a 300 DPI; manifest.json indica rendered_only.
- El ensayo rechaza página inválida y sobrescritura de un experimento existente.
- El ensayo informa claramente cuando no encuentra Tesseract.
- docker compose --env-file .env.example --profile ocr config --quiet finaliza correctamente.
- No se encontró el patrón de una clave OpenRouter en archivos de texto del proyecto.
- No se hicieron llamadas a OpenRouter ni se utilizó la clave proporcionada.

## Pendiente

- Docker Desktop instalado, pero motor Linux no disponible durante la revisión: no se construyeron ni arrancaron contenedores.
- Tesseract no está instalado/en PATH en Windows: no se ejecutó reconocimiento OCR. La ruta Docker instala Tesseract dentro de su imagen.
- No se ha validado reconstrucción de tablas ni exactitud OCR.
- No hay conexión funcional del backend a PostgreSQL, esquema de datos ni ingestión.
- No hay agente, LangChain Tool, historial persistente ni aplicación móvil.
- Falta probar instalación limpia con dependencias declaradas. La prueba FastAPI usó las versiones directas coincidentes ya instaladas; el cliente de prueba emitió una advertencia de deprecación sobre httpx, sin fallo de las comprobaciones.
- Falta crear/publicar remoto GitHub y completar la entrega.

Los resultados locales en data/ocr/ están excluidos de Git y se pueden regenerar siguiendo el README. La carpeta de salida de cada ensayo debe ser nueva.
