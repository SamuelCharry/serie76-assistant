# Agente LangChain

El agente convierte lenguaje en una operación sobre datos. **No redacta libremente las cifras ni la respuesta técnica.**

## Recorrido de una pregunta

1. FastAPI comprueba usuario y sesión; recupera historial reciente y contexto.
2. El código intenta una ruta determinista. Si hace falta interpretación, añade ejemplos semánticos opcionales y solicita una decisión al modelo.
3. Valida la decisión, aplica cambios de filtros y resuelve referencias como «el segundo» sobre el orden guardado.
4. La herramienta consulta SQL; el planificador y las plantillas construyen la presentación.
5. La guarda final comprueba los productos seleccionados frente a requisitos representados. Se guardan mensajes, productos, contexto y traza.

| Herramienta | Uso |
|---|---|
| `get_actuator` | Códigos completos, campos concretos o comparaciones |
| `search_actuators` | Candidatos y selección según requisitos/criterio |
| `explain_terms` | Definiciones del resumen suministrado |
| `ask_clarification` | Pedir información o explicar una limitación |

## Ejemplo defendible

`What is the motor power of 761A00-11300000/A?` se resuelve sin LLM: código completo + campo inequívoco → SQL → **15 W**. Una selección libre puede necesitar el modelo. Sin clave configurada, la interpretación devuelve `503 not_configured`; login y consultas deterministas siguen disponibles.

En seguimientos, «al menos» y «como máximo» conservan sus operadores. Una corrección sustituye los campos afectados; retirar un requisito no debe retirar los demás. El código mantiene el estado, pero una interpretación equivocada sigue siendo posible.

## Modelos y recuperación

Chat: `google/gemini-3.6-flash`, sin fallback configurado. Embeddings: `google/gemini-embedding-2`, 768 dimensiones. El banco guarda frases, interpretaciones y procedencia; no cifras de producto. Los ejemplos similares no pueden sustituir requisitos explícitos o negaciones.

**Límite:** validación tipada y cifras correctas no prueban comprensión perfecta. Un producto puede tener cifras exactas y ser inadecuado para la petición. [Resultados](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites).

[Flujo y herramientas](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/agent.py) · [Estado](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/policy.py) · [Recuperación](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/conversation/embeddings.py)
