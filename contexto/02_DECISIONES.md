# Decisiones, restricciones y colaboración

## Cómo quiere trabajar Samuel

Samuel pidió comprender el dominio antes de programar y después avanzar de forma gradual. Cuando la explicación saltó demasiado rápido a arquitectura indicó explícitamente: «escalaste muy rápido». Explicar cada próximo bloque en español, con lenguaje claro y ejemplos. No volver a preguntar todos los requisitos ya acordados ni construir toda la app de una vez.

Prefiere auditoría rigurosa: señalar fallos concretos y su impacto antes de alternativas. No inventar problemas, exagerar avances ni convertir escepticismo en insultos. La diferencia entre lo planeado y lo comprobado es esencial.

## Alcance y decisiones tomadas

- Backend Python/FastAPI, agente LangChain y PostgreSQL: obligatorios del assessment.
- App elegida: Android, Kotlin + Jetpack Compose. Flutter no satisface este enunciado.
- Un agente conversacional; no múltiples agentes de producto ni delegación a subagentes acordada.
- El agente interpreta lenguaje, resuelve referencias y decide qué herramienta llamar; código valida argumentos, filtra restricciones y consulta datos.
- Dos herramientas previstas: get_actuator y search_actuators. Son diseños pendientes, no implementaciones.
- Las fichas de producto deben derivarse de resultados estructurados, no de cifras improvisadas por el modelo.
- Primera estrategia de extracción: probar Tesseract local. Su calidad aún no se midió y no se eligió definitivamente sobre evidencia.
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
