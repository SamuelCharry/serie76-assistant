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

## 11. ¿Por qué no pgvector?

El resumen cabe como glosario literal en contexto y las consultas numéricas son relacionales. Vectorizar añadiría embeddings, coste y otro fallo sin mejora demostrada; se reconsideraría con un corpus mayor.

Prueba: [docs/adr/0001-arquitectura-agente.md](../../../docs/adr/0001-arquitectura-agente.md#L1).

## 12. ¿Qué pasa cuando el proveedor devuelve 503?

El backend responde 503 y revierte todo el turno. Android muestra exactamente “The assistant is not configured on the server.” si `error_code=not_configured`; para cualquier otro 503 muestra “The assistant is temporarily unavailable. Please try again.”

Los códigos del backend son `not_configured`, `timeout`, `rate_limited`, `budget_exhausted`, `provider_unreachable`, `provider_error` y `rate_limited_local` (guarda por proceso). Un 503 por DB/capacidad puede no llevar `error_code`. Un timeout del cliente no prueba cancelación: revisar historial antes de reenviar.

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

La variante release excluye pantalla/cliente y acceso; backend exige DEV_DEBUG=true, autenticación y propiedad. Mantener debug público activado sería una mala operación.

Prueba: [mobile/android/app/src/release/java/com/serie76/assistant/ui/DeveloperScreen.kt](../../../mobile/android/app/src/release/java/com/serie76/assistant/ui/DeveloperScreen.kt#L1).

## 21. ¿Qué falla con cien veces más tráfico?

Hay cuatro turnos simultáneos por proceso y una transacción abierta durante el modelo. No hay cola distribuida ni guarda monetaria global. Necesitaría medir conexiones, transacciones, latencia y cuotas antes de escalar.

Prueba: [backend/conversation/api.py](../../../backend/conversation/api.py#L18).

## 22. ¿Cuál es una debilidad técnica concreta?

Los umbrales estrictos ya se admiten: below 5 W usa lt y mayor a/over usa gt; al menos/hasta son inclusivos. Se verificaron offline con decisiones programadas, SQL y pruebas de frontera; la comprobación v5 con LLM real queda pendiente del coordinador. Sigue siendo una debilidad que presencia de un número no prueba su asignación al campo semántico correcto.

Prueba: [regresiones T6](../../../tests/test_conversation_quality.py), [SQL de filtros](../../../backend/catalog/repository.py) y [evidencia T6](../../../reports/submission/T6.md).

## 23. ¿Qué harías con más tiempo o menos presupuesto?

Primero cerraría aceptación OpenRouter acotada y el recorrido Android real; luego desigualdades estrictas y casos con error de proveedor. Con menos presupuesto priorizaría controles offline y un corpus congelado pequeño antes de gastar.

Prueba: [docs/evidence/agent_acceptance.md](../../../docs/evidence/agent_acceptance.md#L1).

## 24. ¿Reiniciar borra historial o cambia respuestas antiguas?

No: PostgreSQL conserva mensajes y snapshots. Activar otra importación no reescribe productos previos. No se debe borrar el volumen para reiniciar ni para imponer contraseñas demo.

Prueba: [backend/conversation/store.py](../../../backend/conversation/store.py#L70).

## Límites conocidos

No hay aceptación OpenRouter ni Android con LLM real cerrada; no hay voz, sincronización offline ni evidencia de carga masiva. [Pruebas](testing.md) delimita el alcance.
