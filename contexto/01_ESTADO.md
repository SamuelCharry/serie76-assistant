# Estado verificado y límites

## Estado actual del pipeline

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL, agente y Android siguen pendientes.

43 pruebas pasan, lint F/E9 y pip check correctos. Entorno runtime limpio sin PyTorch/pandas/ydata/EasyOCR. La historia de abajo describe los ensayos anteriores, no la ruta actual.

## Publicación y organización

- Cuenta GitHub: SamuelCharry.
- Repositorio privado, rama main.
- Commits anteriores a este handoff: d1604bd (scaffold) y 7c4feeb (seguimiento y entorno limpio).
- Siete milestones abiertos y siete issues, asociados uno a uno y asignados a SamuelCharry. Ver [seguimiento](../docs/SEGUIMIENTO.md) y snapshot en evidence/.
- Grupos: 1 entorno/entrega; 2 datos/OCR/modelos; 3 backend/agente; 4 API; 5 Android; 6 documentación/reproducibilidad; 7 login/voz opcionales.
- Son grupos de requisitos, no una secuencia rígida: grupo 1 incluye la entrega final; grupo 6 avanza durante todo el trabajo. No cerrar un milestone por completar solo una parte.

## Implementado y ejecutado

- Nueva revisión visual completa de cuatro páginas, siete tablas y notas, con recortes en reports/manual_review y transcripción introducida desde las imágenes en data/manual/series76_visual_transcription.json. Comparación posterior con la referencia revisada: cero diferencias numéricas.
- Exportación final en data/reviewed/catalog-v1: 68 códigos, 869 cifras, cuatro N/A, notas/unidades/alcances y estado explícito de cada vacío numérico. Las seis diferencias crudas están resueltas mediante data/manual/approved_ocr_corrections.json; el motor no se presenta como perfecto.
- scripts/extract_reviewed_catalog.py verifica el hash del PDF, el esquema OCR completo y cada diferencia antes de exportar. Dieciocho pruebas pasan, incluyendo inversiones de unidades, BOO y cambios no revisados; la carga de PostgreSQL sigue pendiente.

- Laboratorio separado `.venv-ocr`: Tesseract 5.5.3/tesserocr 2.12.0, EasyOCR 1.7.2 y RapidOCR 3.10.0/PP-OCRv5 inglés, inferencia CPU sin OpenRouter.
- Notebook 01 ejecutó las cuatro páginas para cada motor. Métricas: RapidOCR 6 discrepancias primarias y 68/68 códigos; EasyOCR 228 y 13/68; Tesseract 252 y 30/68. Referencia visual revisada, no validación independiente global.
- Se revisaron contra el PDF tres errores de la referencia y se corrigieron CSV/JSON juntos; recortes y cambios en docs/OCR_REFERENCE_REVIEW.md. Primera tabla de 11 filas revisada visualmente sin discrepancias contra la referencia actual.
- Motor seleccionado configurado en config/ocr.json. Conserva texto crudo, coordenadas, alcance de celdas combinadas y manifiestos. Plantilla específica del catálogo, con rechazo de otro hash de PDF.
- Ocho pruebas de integridad verifican separación de frecuencias, celdas combinadas, N/A, ausencia de reparaciones inventadas y preservación de evidencia. Ver docs/OCR.md para reproducir.
- Notebook 02 ejecutado: dos perfiles mínimos reales de referencia y OCR, 11 columnas y 68 filas. reports/ocr/latest_profile.json apunta a los HTML y conserva el conteo de cuatro N/A y un token inválido entre las columnas perfiladas.
- Ejecución adicional por config/ocr.json terminada sobre las cuatro páginas: data/ocr/selected-smoke-20261102. Sigue marcada como ocr_completed_unvalidated.

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

Tesseract no se encontró como ejecutable de sistema durante la preparación. Ahora funciona mediante el wheel tesserocr dentro de `.venv-ocr`; eso no instala un ejecutable `tesseract` en PATH. El servicio Docker `ocr` conserva el ensayo original y aún no se construyó; el laboratorio seleccionado funciona localmente sin Docker.

## No implementado

- Esquema DB, carga idempotente en PostgreSQL y consultas deterministas del catálogo OCR. Las seis discrepancias siguen presentes en el OCR crudo, pero están revisadas y corregidas en la exportación de data/reviewed/catalog-v1; no volver a contarlas como pendientes de esa exportación.
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
