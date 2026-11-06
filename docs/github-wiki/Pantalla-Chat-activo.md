# Pantalla · Chat activo

Presenta respuestas breves, tarjetas de producto y comparaciones. Las respuestas y opciones del producto están en inglés; el usuario también puede escribir en español.

Cuando faltan datos, presenta una pregunta a la vez con navegación y revisión. **Submit envía opciones estructuradas:** el backend valida y aplica la selección sin reinterpretarla con el LLM. Cancelar abandona esa interacción.

Las recomendaciones indican el criterio usado y cuántos candidatos se muestran. Una alternativa que relaja requisitos debe estar identificada. Un valor favorable en una métrica no prueba idoneidad de instalación ni un ganador global.

## Demostración sin llamadas al modelo

1. `What is the motor power of 761A00-11300000/A?` → **15 W**.
2. `Compare 761A00-11300000/A and 761B00-11300000/A` → comparación de ambos códigos completos.
3. Abre la respuesta guardada desde el historial.

Una selección libre puede usar OpenRouter y consumir crédito. Las pruebas de UI con respuestas controladas no miden esa interpretación.

[UI](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/ui/Screens.kt) · [Contrato de presentación](https://github.com/SamuelCharry/serie76-assistant/blob/main/backend/app/contracts.py)
