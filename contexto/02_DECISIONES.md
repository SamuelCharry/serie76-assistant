# Actualización PostgreSQL

OCR, PostgreSQL y consultas técnicas están implementados y verificados. PostgreSQL 17.11 y backend corren en Docker. La reconstrucción SQL coincide en 68 referencias, 869 cifras, cuatro N/A, cinco marcas y 272 atributos de contexto (941/941 comprobaciones primarias). Las 62 pruebas actuales pasan con SERIES76_TEST_DB=1. El reinicio de DB/backend conserva catálogo y hash. Ver docs/POSTGRES.md y reports/postgres/summary.json. Agente, LangChain, historial, selección del LLM y Android siguen pendientes.

Los apartados siguientes conservan historia anterior. Sus pendientes de PostgreSQL/Docker ya fueron resueltos. No se modificaron issues remotos; el grupo de datos sigue abierto porque falta integración/modelos.

# Decisiones, restricciones y colaboración

## Cómo quiere trabajar Samuel

Samuel pidió comprender el dominio antes de programar y después avanzar de forma gradual. Cuando la explicación saltó demasiado rápido a arquitectura indicó explícitamente: «escalaste muy rápido». Explicar cada próximo bloque en español, con lenguaje claro y ejemplos. No volver a preguntar todos los requisitos ya acordados ni construir toda la app de una vez.

Prefiere auditoría rigurosa: señalar fallos concretos y su impacto antes de alternativas. No inventar problemas, exagerar avances ni convertir escepticismo en insultos. La diferencia entre lo planeado y lo comprobado es esencial.

## Alcance y decisiones tomadas

Actualización del plan Android autorizado: Kotlin/Compose, inglés, paleta clara/lila Konecto y maqueta C aprobada antes de programar. Una ficha para un producto y tabla comparativa en el chat para varios. Tres pantallas; sin Firebase, login, voz, búsqueda de conversaciones ni onboarding. Wrappers LangChain y conversaciones implementados con pruebas controladas; elección/evaluación de LLM sigue diferida. Ver docs/ANDROID.md. Esto actualiza las referencias históricas a capacidades pendientes de este archivo.

- Backend Python/FastAPI, agente LangChain y PostgreSQL: obligatorios del assessment.
- App elegida: Android, Kotlin + Jetpack Compose. Flutter no satisface este enunciado.
- Un agente conversacional; no múltiples agentes de producto ni delegación a subagentes acordada.
- El agente interpreta lenguaje, resuelve referencias y decide qué herramienta llamar; código valida argumentos, filtra restricciones y consulta datos.
- Dos herramientas previstas: get_actuator y search_actuators. Son diseños pendientes, no implementaciones.
- Las fichas de producto deben derivarse de resultados estructurados, no de cifras improvisadas por el modelo.
- Primera estrategia de extracción: probar Tesseract local. Fue una hipótesis inicial, posteriormente evaluada junto con los otros dos motores.
- Actualización: se compararon tres motores en notebooks ejecutados. RapidOCR/PP-OCRv5 inglés fue seleccionado con 935/941 coincidencias; Tesseract dejó de ser la ruta elegida. Se mantiene inferencia local, plantilla específica del PDF y revisión obligatoria de seis discrepancias antes de ingerir.
- Actualización posterior: revisión visual completa y nueva transcripción de las siete tablas/notas; catálogo en data/reviewed/catalog-v1 con las seis correcciones registradas. No modificar el OCR crudo ni llamarlo perfecto. Un valor nuevo que difiera sin revisión debe detener la exportación.
- Un modelo de visión podría evaluarse como extractor acotado si hace falta; una llamada a un modelo no implica construir un agente.
- No usar embeddings/pgvector inicialmente: primero consultas exactas y filtros. Si después se justifica búsqueda vectorial, pgvector es obligatorio.
- No fine-tuning, LoRA, RLHF/DPO ni votaciones multiagente para verificar cifras.
- No login ni voz hasta completar requisitos obligatorios.
- Modelos OpenRouter no elegidos. Variables preparadas, sin clave real. Límite del assessment: USD 10 sin recarga.
- Repositorio privado para desarrollo. Antes de entregar verificar acceso de evaluadores; no cambiar visibilidad ni añadir personas por inferencia.

## Plazo y envío

Correo de Nahuel Montesino, Konecto: siguiente fase técnica, siete días desde recepción, responder al mismo correo con enlace al repositorio; después habrá conversación para defender solución y decisiones. No se verificó la fecha/hora real de recepción: no establecer un vencimiento a partir del nombre del directorio. El envío final no está realizado.

## Lecciones aprovechadas de las notas de PLN

Se revisó el índice del libro de 310 páginas de Rubén Francisco Manrique y secciones pertinentes, no una auditoría exhaustiva del libro. Archivo local verificado al handoff: `C:\Users\nrir\Downloads\Notas sobre Procesamiento de Lenguaje Natural (3).pdf`. No se incorpora el libro completo al repositorio.

- Correferencia (PDF pp. 29-30): «¿y cuánto consume?» necesita contexto; si hay varios modelos, aclarar.
- Preprocesamiento (pp. 37-43): preservar códigos, negaciones, unidades y cifras; evitar limpieza lingüística indiscriminada.
- Prompting estructurado (pp. 272-274): interpretar requisitos en campos y validar con código.
- Herramientas (p. 276): delegar consultas y comparaciones numéricas al código.
- Conocimiento externo (pp. 269-278): recuperar datos verificables; embeddings no son un requisito universal de esta idea.
- Evaluación (pp. 282-285): comprobar respaldo de cada afirmación y condición; un LLM juez no sustituye comparar contra el PDF.
- Contexto/costo (pp. 271-272): no enviar catálogo completo ni historial infinito por consulta.
- Seguridad (pp. 276-277, 298): documentos son datos no confiables, herramientas limitadas, argumentos validados.

La pantalla debug debe mostrar llamadas reales, parámetros y resultados, no supuestas cadenas de razonamiento internas.


## Actualización: pipeline OCR verificable

El pipeline PDF → OCR local → reconstrucción/limpieza → validación → CSV/JSON está implementado y verificado. La salida real está en data/extracted/series76; procede del OCR, sin leer manual/reference/reviewed. Comparación posterior: 68/68 códigos, 869/869 cifras, 4/4 N/A, 5/5 marcas y 272/272 campos de contexto. Las 941 comprobaciones primarias coinciden. Ver reports/pipeline/RESULTADOS.md y reports/pipeline/verified/summary.json. La referencia manual solo evalúa. PostgreSQL, agente y Android siguen pendientes.
