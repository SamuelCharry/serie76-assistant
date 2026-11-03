# Comparación experimental de arquitecturas

No se cambió el chat operativo. Google; aceptación OpenRouter pendiente.

| Configuración | Comunes | Éxitos | Fallos proveedor/ejecución | Costo medio USD | Latencia p95 s |
|---|---:|---:|---:|---:|---:|
| A | 1 | 1 | 3 | 0.0019319999999999893 | 7.208929699998407 |
| B | 1 | 1 | 4 | 0.002895150000000013 | 17.592667799999617 |
| C | 1 | 1 | 5 | 0.005146499999999998 | 55.74970019999819 |
| D | 1 | 1 | 5 | 0.002080500000000013 | 31.916602900000726 |
| E | 1 | 1 | 5 | 0.01205324999999996 | 15.656236999999237 |

Resultado: **inconclusive_partial_experiment**. Escenarios comunes completos: 1/24.
Cargo conservador del controlador: USD 0.48392565; límite USD 0.50. No es una factura ni consulta de saldo.

Se comparan únicamente escenarios completados por las cinco variantes. Las reservas de errores sin consumo conocido se conservan. No se declara superioridad estadística.

## Fallos observados
- C / exact_power_en: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- D / exact_power_en: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- C / context_fla: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- E / context_fla: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- A / context_fla: [{"arguments_ok": false, "cited_context_ids": [], "context_ok": false, "facts": {}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "ask_clarification", "unrequested_or_changed_filters": false}]
- A / vague_factory: {"provider_failure": true, "status": 503, "type": "AgentUnavailable"}
- D / follow_power: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- E / follow_power: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- E / conflict_dc: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- A / conflict_dc: [{"arguments_ok": false, "cited_context_ids": [], "context_ok": true, "facts": {}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "search_actuators", "unrequested_or_changed_filters": true}]
- B / conflict_dc: {"provider_failure": false, "status": null, "type": "ValidationError"}
- C / conflict_dc: {"provider_failure": false, "status": null, "type": "ValidationError"}
- D / conflict_dc: {"provider_failure": true, "status": 0, "type": "ProviderFailure"}
- B / exact_torque_es: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- C / exact_csa: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- D / exact_csa: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- E / exact_csa: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- D / exact_unknown: [{"arguments_ok": false, "cited_context_ids": [], "context_ok": true, "facts": {"products": false}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "ask_clarification", "unrequested_or_changed_filters": false}]
- E / exact_unknown: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- A / exact_unknown: {"provider_failure": true, "status": 503, "type": "AgentUnavailable"}
- B / exact_unknown: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- C / exact_unknown: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- A / context_onoff: {"provider_failure": true, "status": 503, "type": "AgentUnavailable"}
- B / context_onoff: {"provider_failure": true, "status": 503, "type": "ProviderFailure"}
- A / context_duty: [{"arguments_ok": false, "cited_context_ids": [], "context_ok": false, "facts": {}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "ask_clarification", "unrequested_or_changed_filters": false}]
- B / context_duty: [{"arguments_ok": true, "cited_context_ids": ["a20da9b10e1f7258f49d47c3a79f1c92908bfb4572fe2229356ac8ab04c6f954"], "context_ok": false, "facts": {}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "explain_context", "unrequested_or_changed_filters": false}]
- C / context_duty: [{"arguments_ok": true, "cited_context_ids": ["a20da9b10e1f7258f49d47c3a79f1c92908bfb4572fe2229356ac8ab04c6f954"], "context_ok": false, "facts": {}, "numeric_authority": "deterministic_sql", "passed": false, "tool": "explain_context", "unrequested_or_changed_filters": false}]
- D / context_duty: {"provider_failure": false, "status": null, "type": "BudgetStop"}
