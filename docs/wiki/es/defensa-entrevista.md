# Guion de sustentación

## Recorrido de cinco minutos

1. **Problema — 30 s.** «Consultar un catálogo técnico exige conservar códigos, unidades, servicio y frecuencia. Una respuesta fluida con un dato mal asignado no sirve».
2. **Arquitectura — 60 s.** Muestra [el diagrama](https://github.com/SamuelCharry/serie76-assistant/wiki/Arquitectura): Android → FastAPI → interpretación o ruta determinista → SQL → validación/plantillas → historial.
3. **Demostración — 90 s.** Consulta potencia por código completo, compara dos códigos, reabre historial y muestra debug. Estas consultas concretas funcionan sin LLM.
4. **Decisiones — 60 s.** Explica un agente, datos relacionales, recuperación de ejemplos y estado controlado por código.
5. **Evidencia y límites — 60 s.** Presenta 79,4 % frente a 61,1 %, distingue candidato medido y reparación offline, y declara pendiente la voz real.

## Preguntas que conviene preparar

| Pregunta | Respuesta breve |
|---|---|
| ¿Dónde está la IA? | Interpreta lenguaje y elige herramienta/argumentos; el código resuelve rutas cerradas y SQL aporta valores. |
| ¿Por qué no un chatbot sobre fragmentos del PDF? | La selección exige filtros y ámbitos exactos; similitud textual no garantiza torque, frecuencia ni unidades. |
| ¿Para qué sirve pgvector? | Recupera ejemplos de interpretación, no conocimiento numérico de producto. |
| ¿Por qué un agente? | Menos llamadas y un flujo inspeccionable; no afirmo superioridad universal sobre múltiples agentes. |
| ¿Cómo maneja seguimiento? | Conserva contexto y aplica deltas validados; resuelve referencias contra resultados guardados. |
| ¿Puede alucinar? | SQL evita fabricar cifras en la presentación, pero puede fallar la interpretación o elección de producto. |
| ¿Qué demuestra el 79,4 %? | Promedio de tres ejecuciones pareadas de 60 conversaciones del candidato medido; no la puntuación del código reparado. |
| ¿Qué pasa sin OpenRouter? | Login, historial y rutas deterministas funcionan; interpretación libre devuelve un error de configuración/disponibilidad. |
| ¿Y con 100 veces más tráfico? | No está probado. Hay límites por proceso y transacción durante el turno; mediría contención y cuotas distribuidas. |
| ¿Qué harías después? | Evaluación independiente de reparaciones, pruebas manuales pendientes y carga medida antes de añadir complejidad. |
| ¿La voz funciona? | Flujo implementado y probado con transcripciones controladas; reconocimiento real y dispositivo físico pendientes. |

## Preparar la demostración

- [ ] Abrir emulador y comprobar `/ready`.
- [ ] Entrar con una cuenta TEST ONLY.
- [ ] Consultar `What is the motor power of 761A00-11300000/A?` → 15 W.
- [ ] Comparar `761A00-11300000/A` y `761B00-11300000/A`.
- [ ] Reabrir la conversación y comprobar historial.
- [ ] Mostrar debug si `DEV_DEBUG=true` y explicar la ruta registrada.
- [ ] Si se muestra voz, distinguir indisponibilidad, simulación y reconocimiento real.

No presentes el banco de regresión como casos inéditos ni prometas cero errores. [Resultados y fuentes](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites).
