# Mensajes de voz

La voz es una entrada opcional al editor. Android transcribe; el usuario revisa o corrige y pulsa **Send**. La app no envía audio al backend de este proyecto ni manda automáticamente el texto reconocido.

```mermaid
flowchart LR
    MIC[Micrófono y permiso] --> SR[SpeechRecognizer de Android]
    SR --> EDIT[Texto editable]
    EDIT --> SEND[Usuario pulsa Send]
    SEND --> API[API de conversación]
```

Se prefiere reconocimiento on-device en API 31+ cuando está disponible. El servicio alternativo recibe una preferencia offline, pero puede usar red. Sin servicio disponible, la app informa que no puede reconocer voz.

## Evidencia disponible

- **Implementado:** permiso, resultados parciales/finales, errores y cancelación del reconocedor.
- **Verificado con entradas controladas:** el texto llega al editor, no se envía solo y se ignoran callbacks tardíos tras cancelar.
- **Pendiente:** micrófono y reconocimiento reales, integración de permisos y comportamiento físico. El autor no dispone actualmente de un Android físico.

Un emulador con servicio de reconocimiento y micrófono del equipo podría permitir una prueba adicional; no se registra como aprobada sin ejecutarla. Sin servicio, se demuestra el manejo de indisponibilidad y se mantiene pendiente la transcripción real.

**Para la sustentación:** «Implementé el flujo y probé su estado con transcripciones controladas; no tengo evidencia de reconocimiento real en un dispositivo físico».

[Reconocedor](https://github.com/SamuelCharry/serie76-assistant/blob/main/mobile/android/app/src/main/java/com/serie76/assistant/ui/AndroidVoiceRecognizer.kt) · [Evidencia P2-D](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/P2-D.md)
