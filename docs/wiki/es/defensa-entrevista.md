# Defensa de entrevista

[Wiki](index.md)

Preguntas difíciles con respuestas breves que separan decisiones de ingeniería, pruebas ejecutadas y aceptación pendiente. Usa cada archivo como punto de partida para recorrer el código; no memorices cifras como garantía universal.

## 1. ¿Por qué un agente y no varios?

- A–E encontró fallos deterministas: DC + 60 Hz terminaba en error de esquema y se pedía completar un código bien formado inexistente; se corrigieron en código, no añadiendo otro LLM. [ADR archivado](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md).
- Un revisor LLM no garantiza cifras; en el ensayo compartía modelo/proveedor y posibles sesgos. La garantía numérica viene de validación + SQL + plantillas. [Análisis archivado](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/reports/architecture_eval/ANALISIS.md) y [ADR](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md).
- En turnos completados C y E hacen 2 decisiones LLM; D hace 1 al aclarar, 2 en ruta catálogo o 3 con contexto. Se excluyen embeddings y FixedRouter local. [Código archivado verificado](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/architecture_eval/engine.py).
- Con 19 fallos de proveedor en 103 llamadas observadas y presupuesto del assessment de USD 10, cada llamada extra añade exposición a fallo, latencia y coste; no estimo probabilidades independientes con esa muestra. [Comparación](../../evidence/architecture_comparison.md) y [presupuesto en ADR archivado](https://github.com/SamuelCharry/serie76-assistant/blob/archive/pre-cleanup/docs/adr/0001-arquitectura-agente.md).
- A+ pasó 50/55 escenarios en v4, con 4 fallos solo de proveedor; es aceptación Google, no OpenRouter. [Cohortes](../../evidence/agent_acceptance.md).
- A–E quedó inconcluso: es una decisión de ingeniería, no un ranking medido. Consideraría multiagente con flujos realmente distintos o un corpus grande que justifique recuperación especializada. [Comparación y límites](../../evidence/architecture_comparison.md).

## 2. ¿Por qué OCR y no un LLM para las tablas?

El OCR local conserva texto, geometría y lecturas alternativas sin gasto de inferencia remota. No es infalible: las ambigüedades bloquean exportación y la exactitud se contrasta después.

Prueba: [catalog_ingest/pipeline.py](../../../catalog_ingest/pipeline.py#L1).

## 3. ¿Cómo garantizas que no inventa números?

El modelo no redacta la respuesta técnica. SQL devuelve cifras publicadas y la plantilla las presenta con unidades/alcance. Esto evita números generados, pero un filtro semánticamente equivocado todavía puede seleccionar otro producto.

Prueba: [backend/conversation/rendering.py](../../../backend/conversation/rendering.py#L1).

## 4. ¿941/941 significa que funciona con cualquier PDF?

No. Es coincidencia con una referencia revisada y falible para este catálogo. La prueba de 100 páginas repite cuatro páginas; no evalúa 100 diseños distintos.

Prueba: [docs/evidence/ocr.md](../../../docs/evidence/ocr.md#L1).

## 5. ¿La referencia manual alimenta el catálogo?

No. Producción bloquea manual/reference/reviewed; solo el evaluador posterior las usa. Las correcciones de referencia no son reglas por pieza.

Prueba: [tests/test_pipeline_safety.py](../../../tests/test_pipeline_safety.py#L1).

## 6. ¿Qué pasa con N/A?

Se conserva source_NA, diferente de cero y de not_in_layout. Una referencia N/A se consulta por código, pero no se recomienda como si cumpliera un umbral.

Prueba: [backend/catalog/repository.py](../../../backend/catalog/repository.py#L1).

## 7. ¿Por qué no conviertes torque entre unidades?

Porque ambas columnas son valores publicados. Comparo in-lb con in-lb y Nm con Nm; una conversión calculada no reemplaza el dato del fabricante.

Prueba: [backend/catalog/models.py](../../../backend/catalog/models.py#L32).

## 8. ¿Qué ocurre con DC y 60 Hz?

El código detecta contradicción y pregunta cuál requisito conservar. En búsqueda HTTP directa la validación puede devolver 422; la herramienta conversacional la intercepta antes.

Prueba: [backend/conversation/policy.py](../../../backend/conversation/policy.py#L142).

## 9. ¿Cómo conserva restricciones en un seguimiento?

El LLM envía delta con refine/more/remove; merge_filters fusiona con el contexto persistido. Al cambiar servicio retira una tasa anterior incompatible y lo informa.

Prueba: [backend/conversation/policy.py](../../../backend/conversation/policy.py#L118).

## 10. ¿Qué hace ante un código incompleto?

No añade /A ni inventa sufijo. Puede mostrar candidatos por prefijo y pedir selección. Un código completo inexistente se informa como ausente.

Prueba: [backend/conversation/agent.py](../../../backend/conversation/agent.py#L306).

## 11. ¿Por qué pgvector solo para interpretación?

T9 usa pgvector para frases e interpretaciones, no para productos. El glosario sigue literal y las cifras salen de SQL. Retrieval añade coste y dependencia; el margen de ronda 9 es pequeño y el rango de rondas 9–10 es 68–73 % estricto, sin superioridad general demostrada. [Diseño vigente](agent.md).

Prueba: [docs/adr/0001-arquitectura-agente.md](../../../docs/adr/0001-arquitectura-agente.md#L1).

## 12. ¿Qué pasa cuando el proveedor devuelve 503?

Un 503 del proveedor permite retry acotado y fallback opcional dentro del plazo compartido de 60 s. Si falla la decisión, el backend responde 503 y revierte todo el turno. Android muestra exactamente “The assistant is not configured on the server.” si `error_code=not_configured`; para cualquier otro 503 muestra “The assistant is temporarily unavailable. Please try again.”

Los códigos del backend son `not_configured`, `timeout`, `turn_deadline`, `rate_limited`, `budget_exhausted`, `provider_unreachable`, `provider_error` y `rate_limited_local` (guarda por proceso). Un 503 por DB/capacidad puede no llevar `error_code`. Un timeout del cliente no prueba cancelación: revisar historial antes de reenviar.

Prueba: [mensajes Android](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/ConversationRepository.kt#L61), [códigos del proveedor](../../../backend/conversation/agent.py#L249), [guarda local](../../../backend/conversation/agent.py#L209) y [rollback/API](../../../backend/conversation/api.py#L76).

## 13. ¿El límite horario impide agotar el saldo?

No. Cuenta intentos por proceso, se reinicia al reiniciar y se multiplica con workers. El ledger de evaluación reserva gasto conservador; tampoco consulta factura ni limita otras aplicaciones.

Prueba: [backend/conversation/agent.py](../../../backend/conversation/agent.py#L209).

## 14. ¿require_parameters garantiza que el modelo entiende?

No. Pide routing compatible con parámetros al host OpenRouter. No garantiza intención, exactitud semántica ni disponibilidad; debe aceptarse el proveedor final.

Prueba: [backend/conversation/agent.py](../../../backend/conversation/agent.py#L224).

## 15. ¿Está verificado OpenRouter?

No. Hay cohortes Google con cliente A+ y cero llamadas OpenRouter. La aceptación OpenRouter y Android con modelo real están pendientes.

Prueba: [docs/evidence/agent_acceptance.md](../../../docs/evidence/agent_acceptance.md#L1).

## 16. ¿Las pruebas con modelo programado prueban comprensión?

No. Prueban validación, herramientas SQL, renderizado y persistencia con decisiones fijadas. La interpretación exige modelo real y cohortes separadas.

Prueba: [tests/test_agent_scenarios.py](../../../tests/test_agent_scenarios.py#L1).

## 17. ¿Cómo impides ver conversaciones ajenas?

La identidad sale del bearer y cada lectura/continuación/traza filtra propietario. UUID ajeno devuelve 404 antes de invocar modelo. El historial antiguo sin dueño queda en cuarentena.

Prueba: [backend/conversation/store.py](../../../backend/conversation/store.py#L1).

## 18. ¿Por qué token opaco en vez de JWT?

Ya dependemos de PostgreSQL y necesitamos revocación inmediata de la sesión. El coste es una consulta indexada por petición. No afirmo escalabilidad masiva validada.

Prueba: [backend/auth/api.py](../../../backend/auth/api.py#L24).

## 19. ¿Dónde guarda Android la contraseña y las claves del modelo?

No las guarda. Solo conserva token cifrado con AES-GCM y clave Android Keystore no exportable. Las claves de proveedor permanecen en backend.

Prueba: [mobile/android/app/src/main/java/com/serie76/assistant/data/Authentication.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/data/Authentication.kt#L34).

## 20. ¿El debug se filtra al usuario final?

Ambas variantes tienen debug oculto por respuesta; se habilita con siete toques al nombre/email. El backend exige DEV_DEBUG=true, autenticación y propiedad: el gesto solo controla presentación.

Prueba: [mobile/android/app/src/main/java/com/serie76/assistant/ui/DebugDetails.kt](../../../mobile/android/app/src/main/java/com/serie76/assistant/ui/DebugDetails.kt#L1).

## 21. ¿Qué falla con cien veces más tráfico?

Hay cuatro turnos simultáneos por proceso y una transacción abierta durante el modelo. No hay cola distribuida ni guarda monetaria global. Necesitaría medir conexiones, transacciones, latencia y cuotas antes de escalar.

Prueba: [backend/conversation/api.py](../../../backend/conversation/api.py#L18).

## 22. ¿Cuál es una debilidad técnica concreta?

Los umbrales estrictos ya se admiten: below 5 W usa lt y mayor a/over usa gt; al menos/hasta son inclusivos. Se verificaron offline con decisiones programadas, SQL y pruebas de frontera; la comprobación v6 con LLM real queda pendiente del coordinador. Sigue siendo una debilidad que presencia de un número no prueba su asignación al campo semántico correcto.

Prueba: [regresiones T6](../../../tests/test_conversation_quality.py), [SQL de filtros](../../../backend/catalog/repository.py) y [evidencia T6](../../../reports/submission/T6.md).

## 23. ¿Qué harías con más tiempo o menos presupuesto?

Primero cerraría aceptación OpenRouter acotada y el recorrido Android real; después ampliaría casos reservados y resiliencia con proveedor real; las desigualdades estrictas ya tienen cobertura offline. Con menos presupuesto priorizaría controles offline y un corpus congelado pequeño antes de gastar.

Prueba: [docs/evidence/agent_acceptance.md](../../../docs/evidence/agent_acceptance.md#L1).

## 24. ¿Reiniciar borra historial o cambia respuestas antiguas?

No: PostgreSQL conserva mensajes y snapshots. Activar otra importación no reescribe productos previos. No se debe borrar el volumen para reiniciar ni para imponer contraseñas demo.

Prueba: [backend/conversation/store.py](../../../backend/conversation/store.py#L70).

## 25. ¿Por qué Submit no llama al LLM?

La app ya envía IDs y valores exactos de opciones pendientes. El código valida, fusiona filtros y repite SQL; reinterpretarlos gastaría una llamada y podría alterar la elección. Eliminar una etiqueta sigue la misma ruta. [Prueba HTTP sin reserva de modelo](../../../tests/test_t7_contract.py), [capturas](../../../reports/submission/T7-interactions.json).

## 26. ¿Por qué el agente no decide las flechas?

Una flecha afirma una relación entre datos publicados: se calcula comparando números, unidades y ámbito. `better` es un índice o null; empate/N/A no tiene ganador. El resumen cuenta campos sin ponderar, no declara el mejor actuador global. Tres/cuatro modelos usan tarjetas sin flechas. [Reglas y ejemplo SQL](agent.md#comparación-y-lead).

## 27. ¿Por qué 0–3 sugerencias en vez de siempre tres?

Rellenar tres chips mezclaba datos necesarios con navegación genérica. Una pregunta lleva sus propias opciones; hechos, definiciones y comparaciones no necesitan sugerencias. Una búsqueda de 2–4 modelos propone un par útil; una imposibilidad ofrece relajaciones SQL. Cero es una respuesta válida. [Política completa](agent.md#sugerencias-opcionales).

## 28. ¿Por qué acotar retry con un plazo total?

Dos timeouts de 45 s podrían completar el servidor después de que Android abandone a 75 s. El plazo compartido de 60 s limita cada intento al tiempo restante y omite otro si quedan menos de 10 s; fallback comparte ese límite. Solo se reintentan 503/timeout/conexión, nunca 4xx, y cada intento real cuenta. [Prueba de servidor local lento](../../../tests/test_t7_resilience.py).

## 29. ¿Qué prueban la suite límite y las corrupciones?

Los 103 escenarios son 63 históricos más 40 EC con expectativas fijadas contra el CSV. Selfcheck prueba el flujo determinista; las seis corrupciones exigen que el evaluador rechace operador, N/A, unidad, requisito, código y extremo de intervalo alterados después de aceptar el original. Esto demuestra detección de esos fallos, no todos los fallos posibles ni comprensión del modelo. [Pruebas v6](testing.md#aceptación-offline-t7--v6).

## 30. ¿Qué no permite afirmar T7 todavía?

Las 202 pruebas Python (2 omisiones OCR), 103 escenarios y 40 pruebas JVM no equivalen a aceptación con LLM real, ajuste visual en dispositivo, disponibilidad del proveedor o carga masiva. El catálogo tampoco publica precios, no identifica una instalación física y la app no compra ni promete entregas. [Evidencia backend](../../../reports/submission/T7-backend.md), [Android](../../../reports/submission/T7-android.md).

## 31. ¿Por qué embeddings de ejemplos de interpretación y no conocimiento de producto?

La similitud ayuda a traducir una frase a intención; no garantiza una cifra ni su ámbito. El banco guarda frases/interpretaciones y anclas; el PDF eléctrico, SQL y plantillas conservan valores, N/A, unidades y procedencia. [Banco T9](operations.md#example-bank).

## 32. ¿Por qué solo aditivo?

Un vecino semántico no puede borrar “110 V” ni una negación. El parser determinista corre ON/OFF y los conceptos solo completan campos vacíos tras requisitos, argumentos fundamentados y filtros previos. Abstenerse conserva el contrato; no hay motivo para degradarlo por una similitud. [Agente](agent.md).

## 33. ¿Cómo evitas fuga de evaluación?

Congelo los conjuntos retenidos antes de leer respuestas; uso casos nuevos o excluyo todos sus IDs mediante `EMBEDDING_EXCLUDE_SOURCES` antes del ranking. Versiones y manifiestos guardan etiquetas y toda la procedencia. El banco incluye casos históricos v7: tras incorporarlos son regresión, no prueba inédita; el replay de ronda 9 no se carga al banco. [Método](testing.md#behavior-evaluation).

## 34. ¿Por qué la imagen pgvector debía coincidir con glibc?

El volumen PG17 tenía collation de glibc 2.41 y el primer tag pg17 traía 2.36. Una collation distinta puede invalidar supuestos de orden e índices. Se hizo backup y se fijó pg17-trixie por digest, verificando collation y conteos; borrar el volumen o solo refrescar la versión no resuelve esa compatibilidad. [Operaciones](operations.md#pgvector).

## 35. ¿Por qué voz on-device?

Evita una integración de audio, clave y coste de transcripción en nuestro servidor. El usuario revisa texto editable y decide enviarlo. Android prefiere on-device API 31+; el servicio alternativo puede usar red pese a solicitar offline. No afirmo que todos los teléfonos operen sin red. [Voz](android.md#voz-t9).

## 36. ¿Por qué debug oculto por respuesta?

La traza sirve para inspeccionar un resultado concreto; no debe ocupar la conversación normal ni descargarse para todo el historial. Siete toques al perfil habilitan ⓘ, que obtiene la traza perezosamente; backend valida propietario y DEV_DEBUG. Disponible también en release, sin convertir el gesto en seguridad. [Debug](android.md#developer-debug).

## 37. ¿Por qué gemini-3.6-flash y no Pro?

Pro ganó el primer conjunto común de 44: 28/44 frente a 21/44 de 3.6 y 25/44 de 3.8, pero tuvo p95 7.1 s y un turno de 11 s. Tras ronda 6, 3.6 obtuvo 28/43 frente a 26/43 de 3.8. Elegimos ese equilibrio observado de calidad/latencia; no afirmamos que Flash sea universalmente mejor ni que OpenRouter ya esté validado. [Modelos](testing.md#selección-de-modelos).

## 38. ¿Cómo mediste calidad y por qué reportas 68–73 % estricto?

Seis personas, conjuntos congelados y revisión independiente por conversación; las rondas 1–2 usaron un criterio más laxo. En ronda 9 ON pasó 30/41 y OFF 29/41; ronda 10 ON tras las reparaciones pasó 28/41. El rango honesto es 68–73 %, con todas las respuestas de rondas 9–10 bajo 10 s y p95 3.7–5.1 s. No hubo cifras de catálogo incorrectas, pero eso no compensa perder un requisito, errar el contexto de peligro o responder de más; los replays no autorizan inflar la tasa. [Tabla completa](testing.md#behavior-evaluation).

## 39. ¿Qué harías después?

Congelaría una cohorte nueva para medir las reparaciones sin reutilizar entrenamiento, con revisión independiente y costes/latencia separados. Cerraría aceptación OpenRouter autorizada y pruebas Android reales de voz, filtros y debug; después mediría carga, colas/cupos globales y recuperación. Mientras tanto, el ingeniero confirma filtros activos, servicio, cerramiento y clasificación del área peligrosa antes de ordenar.

## 40. ¿Es 73 % mejor que 71 %?

Es mayor en esta muestra, pero no demuestra una mejora: son 30 frente a 29 aprobaciones de las mismas 41 conversaciones. ON−OFF tiene IC95% de −4,9 a +12,2 puntos y McNemar p=1; ambas direcciones siguen siendo compatibles con la incertidumbre. [Resultados](testing.md#cómo-sabemos-si-una-diferencia-es-real).

## 41. ¿Por qué McNemar y no comparar porcentajes?

Porque cada conversación se probó con ambas configuraciones: solo cuentan los desacuerdos, 2 a favor de ON y 1 de OFF. Comparar porcentajes ignora ese emparejamiento; McNemar pregunta si los desacuerdos favorecen sistemáticamente un lado. No rechazar igualdad tampoco demuestra equivalencia.

## 42. ¿Cómo justificaste k = 5 en la recuperación?

Como límite provisional de contexto, no como óptimo probado. Con 649 ejemplos y excluyendo cada consulta y sus textos idénticos, MRR sin umbral fue 0,476/0,546/0,563/0,570 para k=1/3/5/8: después de cinco la ganancia es pequeña. P@5 fue solo 38,2%; el umbral 0,70 cubre 98,3% pero apenas mejora la precisión de los vecinos devueltos, así que requiere calibración con consultas nuevas. [Métrica y límites](testing.md#diagnóstico-del-recuperador).

## 43. ¿Cómo mejoraste la recuperación y cómo sabes que mejoró?

Probé reranking por metadatos, BM25+denso, diversidad MMR y embeddings con cantidades enmascaradas; medí precisión y primer vecino relevante bajo dos definiciones, con ajuste y validación separados dentro del banco. No afirmo una mejora suficiente: el mejor P@5 útil pasó de 37,8% a 39,2%, por debajo de los 5 puntos exigidos, y empeoró la métrica estricta. Conservé denso y sus filtros: medir también sirve para rechazar complejidad que no demuestra beneficio. [Tabla y decisión](testing.md#mejorar-la-recuperación).

## Límites conocidos

No hay aceptación OpenRouter ni Android con LLM real cerrada; la voz está implementada con pruebas JVM, pendiente en dispositivo; no hay sincronización offline ni evidencia de carga masiva. [Pruebas](testing.md) delimita el alcance.
