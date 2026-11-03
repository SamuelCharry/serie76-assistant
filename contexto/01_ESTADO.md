# Estado verificado y límites

## Publicación y organización

- Cuenta GitHub: SamuelCharry.
- Repositorio privado, rama main.
- Commits anteriores a este handoff: d1604bd (scaffold) y 7c4feeb (seguimiento y entorno limpio).
- Siete milestones abiertos y siete issues, asociados uno a uno y asignados a SamuelCharry. Ver [seguimiento](../docs/SEGUIMIENTO.md) y snapshot en evidence/.
- Grupos: 1 entorno/entrega; 2 datos/OCR/modelos; 3 backend/agente; 4 API; 5 Android; 6 documentación/reproducibilidad; 7 login/voz opcionales.
- Son grupos de requisitos, no una secuencia rígida: grupo 1 incluye la entrega final; grupo 6 avanza durante todo el trabajo. No cerrar un milestone por completar solo una parte.

## Implementado y ejecutado

- .venv creada desde cero en el clon principal, Python 3.12, requirements.txt instalado y pip check correcto.
- FastAPI mínimo en backend/app/main.py. /health respondió por HTTP real desde la nueva .venv, y el proceso de prueba se detuvo al terminar.
- /health solo demuestra que el proceso responde; no comprueba DB ni agente.
- Contratos mínimos en backend/app/contracts.py. POST /api/conversation NO existe todavía: devuelve 404.
- scripts/ocr_probe.py renderiza una página y puede invocar Tesseract. Produce PNG, TXT/TSV si hay OCR, y manifest con hash/versiones/estado.
- Renderizado real de página 1, 300 DPI, con nueva .venv: data/ocr/page1-clean-venv/page.png y manifest.json. El manifiesto dice rendered_only, validated_table_data=false y external_api_calls=0.
- Verificados rechazo de página inválida, carpeta de salida existente y motor Tesseract ausente.
- Dockerfile y Compose preparados; sintaxis Compose validada. Esto NO demuestra contenedores construidos o ejecutados.
- Android Studio, Android SDK y adb localizados; no se compiló una app.
- No se han realizado llamadas a OpenRouter en este trabajo. No se verificó el saldo de la clave y no debe afirmarse su saldo actual.

## Bloqueo observado: Docker

Docker CLI existe. Se solicitó iniciar Docker Desktop, pero el proceso terminó. docker info no conectó con `dockerDesktopLinuxEngine` (pipe inexistente). Logs mostraron cierre del backend; no se identificó una causa concluyente. No se reinició Windows, reinstaló Docker ni reseteó su estado intencionalmente.

Rutas útiles locales:
- Docker Desktop: `C:\Users\nrir\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe`.
- Logs: `C:\Users\nrir\AppData\Local\Docker\log\host`.
- Android Studio: `C:\Program Files\Android\Android Studio\bin\studio64.exe`.
- Android SDK: `C:\Users\nrir\AppData\Local\Android\Sdk`.

Estos datos pueden cambiar. Verificar antes de intervenir. No atribuir el cierre a WSL, virtualización u otra causa sin evidencia. No ejecutar limpiezas destructivas para probar.

Tesseract no se encontró en PATH ni en la ruta convencional de Windows durante la preparación. La imagen Docker de OCR lo instala dentro del contenedor, pero todavía no se construyó.

## No implementado

- OCR ejecutado y evaluado; reconstrucción de tablas; ingest.py; esquema DB y carga idempotente.
- Conexión funcional del backend a PostgreSQL y conversaciones persistentes.
- LangChain, herramientas, integración OpenRouter y elección de modelos.
- Endpoint de conversación y endpoints de sesiones.
- App Android compilable: mobile/android solo contiene README.
- Instalación limpia del producto completo, validación de contenedores, entrega final.

## Fuentes de verdad

- Cifras: PDF eléctrico original.
- Requisitos: assessment-en.pdf.
- Estado del código: git y archivos actuales.
- Estado de tareas: issues actuales, con snapshot solo como respaldo.
- CSV/JSON manuales: referencia útil pero falible, NO salida de un pipeline automático.
