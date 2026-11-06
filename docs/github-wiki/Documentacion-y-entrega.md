# Documentación y entrega

Secciones 8–9 del assessment. La entrega evaluable está en **`main`**. PR #10 integró la aplicación en `ac56dee`; **`v1.0-submission`** conserva ese código. `main` también contiene la evidencia posterior de reproducción y esta documentación técnica.

| Entregable solicitado | Ubicación y uso |
|---|---|
| [README](https://github.com/SamuelCharry/serie76-assistant/blob/main/README.es.md) | Instalación, cuentas TEST ONLY y arranque |
| [Checklist](https://github.com/SamuelCharry/serie76-assistant/blob/main/docs/SUBMISSION.md) | 47 obligaciones, evidencia y límites |
| [T18](https://github.com/SamuelCharry/serie76-assistant/blob/main/reports/submission/T18-tag-clean-clone.md) | 10/10 pasos desde un clon de la etiqueta final |
| [Resultados](https://github.com/SamuelCharry/serie76-assistant/wiki/Resultados-y-limites) | Calidad, latencia, gasto y alcance |
| Código backend y app | [Backend](https://github.com/SamuelCharry/serie76-assistant/tree/main/backend) · [Android](https://github.com/SamuelCharry/serie76-assistant/tree/main/mobile/android) |
| Pipeline y datos procesados | [ingest.py](https://github.com/SamuelCharry/serie76-assistant/blob/main/scripts/ingest.py) · [Catálogo validado](https://github.com/SamuelCharry/serie76-assistant/tree/main/data/extracted/series76) |
| Contenedores | [Dockerfile](https://github.com/SamuelCharry/serie76-assistant/blob/main/Dockerfile) · [Compose](https://github.com/SamuelCharry/serie76-assistant/blob/main/docker-compose.yml) |
| Variables sin claves reales | [.env.example](https://github.com/SamuelCharry/serie76-assistant/blob/main/.env.example) |
| Configuración del asistente de desarrollo | [.claude](https://github.com/SamuelCharry/serie76-assistant/tree/main/.claude) |

## Cómo evaluar

1. Seguir el Quick start del README para arrancar Docker, iniciar sesión y ejecutar Android.
2. Probar consulta por código, comparación e historial. La interpretación libre requiere clave configurada y consume presupuesto.
3. Revisar debug por respuesta y casos límite según los criterios del assessment.
4. Contrastar resultados con la checklist y los límites documentados. La reproducción T18 es Windows sin inferencia pagada; no prueba macOS ni dispositivos físicos.

Las cuentas de la app no conceden acceso al repositorio privado. El gasto registrado es USD 6,17; no es saldo consultado en vivo.

Las fuentes de esta wiki se conservan en [docs/github-wiki](https://github.com/SamuelCharry/serie76-assistant/tree/main/docs/github-wiki).
