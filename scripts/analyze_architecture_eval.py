"""Final analysis without modifying frozen runs or making provider calls.

Model schema/protocol failures count as quality failures. Only provider failures
and budget truncation remove a scenario from the paired quality comparison.
"""
import hashlib
import json
import math
from pathlib import Path
import statistics


ROOT=Path("reports/architecture_eval")


def quality_failure(row):
    return bool(row["failure"] and not row["failure"]["provider_failure"] and not row["budget_stopped"])


def paired_ids(rows, variants):
    sets=[{r["scenario"] for r in rows if r["configuration"]==v and
           not r["budget_stopped"] and not (r["failure"] and r["failure"]["provider_failure"])} for v in variants]
    return set.intersection(*sets)


def analyze():
    from architecture_eval.provider import Budget
    config=json.loads(Path("config/architecture_eval.json").read_text())
    path=ROOT/"results.jsonl"
    rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    common=paired_ids(rows,config["configurations"])
    summary={}
    for variant in config["configurations"]:
        rr=[r for r in rows if r["configuration"]==variant]
        available=[r for r in rr if not r["budget_stopped"] and not (r["failure"] and r["failure"]["provider_failure"])]
        paired=[r for r in available if r["scenario"] in common]
        rejected=sum(quality_failure(r) for r in rr)
        durations=sorted(r["latency_s"] for r in paired)
        summary[variant]=dict(attempted=len(rr),provider_failures=sum(bool(r["failure"] and r["failure"]["provider_failure"]) for r in rr),
            schema_or_protocol_failures=rejected,budget_truncated=sum(r["budget_stopped"] for r in rr),
            available_scenarios=len(available),available_passed=sum(r["passed"] for r in available),
            paired_scenarios=len(paired),paired_passed=sum(r["passed"] for r in paired),
            observed_total_charge_usd=sum(r["cost_usd"] for r in rr),
            paired_mean_observed_charge_usd=statistics.mean(r["cost_usd"] for r in paired) if paired else None,
            paired_p95_latency_s=durations[math.ceil(.95*len(durations))-1] if durations else None)
    budget=Budget(ROOT,config)
    events={e["id"]:e for e in budget.events()}
    measured=sum(e["charged_usd"] for e in events.values() if e["state"]=="completed" and e.get("usage"))
    unknown=sum(e["charged_usd"] for e in events.values() if e["state"]!="completed" or not e.get("usage"))
    frozen=json.loads((ROOT/"frozen.json").read_text(encoding="utf-8"))
    drift=[p for p,h in frozen["hashes"].items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    result=dict(configurations=summary,common_scenarios=sorted(common),planned_scenarios=24,
        complete=len(common)==24,conservative_charge_usd=budget.spent(),usage_based_charge_usd=measured,
        unknown_usage_reserve_usd=unknown,cap_usd=config["budget_usd"],provider_calls=len(events),
        failed_provider_calls=sum(e["state"]=="failed" for e in events.values()),
        frozen_input_drift=drift,raw_results_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        recommendation="inconclusive_no_promotion",promoted=False,
        limitations=["Single run; no statistical superiority claim", "Model/schema errors count as quality failures",
                     "Digit-based excerpt filter removes the S4 definition; shared renderer defect, not an embedding or model failure",
                     "Observed cost includes shared embedding-cache warmth; not independent production unit cost",
                     "Latency includes controller pacing; not a concurrency benchmark", "Google only; OpenRouter pending"])
    (ROOT/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# Resultados de arquitecturas", "", "**Conclusión: comparación inconclusa; no se promovió ninguna arquitectura.**", "",
        "Las cinco configuraciones están implementadas y se hicieron llamadas reales en Google. Los errores de esquema cuentan como fallos de calidad. Los fallos del proveedor se separan. Los archivos originales del runner permanecen intactos.", "",
        "| Variante | Intentados | Disponibles sin error proveedor | Éxitos disponibles¹ | Fallos proveedor | Fallos esquema/protocolo | Éxitos emparejados |", "|---|---:|---:|---:|---:|---:|---:|"]
    for v,s in summary.items():
        lines.append(f"| {v} | {s['attempted']} | {s['available_scenarios']} | {s['available_passed']} | {s['provider_failures']} | {s['schema_or_protocol_failures']} | {s['paired_passed']}/{s['paired_scenarios']} |")
    lines += ["", "¹ Las columnas disponibles tienen conjuntos diferentes y no sirven para ordenar las variantes. La comparación válida usa los escenarios emparejados.", "",
        "A: actual; B: agente único contextual; C: dos especialistas; D: supervisor; E: proponente/revisor.", "",
        f"Escenarios comunes: {len(common)}/24. IDs: {', '.join(sorted(common)) or 'ninguno'}.",
        f"Controlador: **USD {budget.spent():.8f} / {config['budget_usd']:.2f}**. Tokens con uso conocido: USD {measured:.8f}; reservas de uso desconocido: USD {unknown:.8f}. No es una factura.",
        f"Llamadas: {len(events)}; fallos de proveedor: {result['failed_provider_calls']}. Deriva de entradas congeladas: {drift}.", "",
        "## Observaciones verificables"]
    for r in rows:
        if not r["failure"] and not r["passed"]:
            lines.append(f"- {r['configuration']} / {r['scenario']}: respuesta recibida, escenario no resuelto. Ver argumentos y score en results.jsonl.")
        if quality_failure(r):
            lines.append(f"- {r['configuration']} / {r['scenario']}: {r['failure']['type']}, contado como fallo de calidad y no como indisponibilidad de Google.")
    lines += ["", "## Límites y siguiente decisión", "",
        "Recuperar contexto permite contestar definiciones que A no tiene cómo recuperar. Eso no demuestra que añadir agentes supere B. Los 503 y la reserva conservadora consumen el presupuesto antes de completar el diseño. No se repiten casos fallidos ni se cambian prompts para inflar la puntuación.",
        "", "Los costos observados incluyen reutilización compartida de embeddings; no representan costos unitarios independientes. Las latencias incluyen pausas del controlador. No deben usarse para afirmar escalabilidad ni para promover una variante. Antes de una comparación definitiva hay que contabilizar embeddings por invocación y separar latencia de servicio del pacing.",
        "", "**Defecto del renderizador contextual:** el filtro genérico de dígitos elimina la oración que define Duty Cycle porque contiene el identificador S4. En context_duty, B/C recuperaron la página correcta pero mostraron otros términos. Es un fallo compartido de preparación/presentación de evidencia, no una prueba contra los embeddings ni contra el modelo. El extractor también conserva un carácter de sustitución en algunas viñetas. Antes de integrar hay que distinguir identificadores de magnitudes, segmentar definiciones individualmente y validar que la respuesta conserva el término solicitado; verificarlo en una cohorte nueva, sin retocar estas puntuaciones.",
        "", "Las definiciones son extractos citados, con oraciones numéricas omitidas; no se evaluó una redacción libre en español. El revisor usa el mismo modelo y puede compartir sesgos. Algunas decisiones intermedias solo guardan metadatos de uso, no el argumento completo: ampliar esas trazas requiere una cohorte nueva, sin alterar esta.",
        "", "Sigue pendiente la validación final por OpenRouter. No cambiar el chat operativo con esta evidencia. Protocolo: ../../docs/ARCHITECTURE_EVALUATION.md."]
    (ROOT/"ANALISIS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    analyze()
