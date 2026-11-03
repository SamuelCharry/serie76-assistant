"""Publish the reviewed Nov-3 snapshots, not an automatic future-winner selector.

Numerical scores remain derived from immutable traces; qualitative observations
below describe this particular reviewed execution and must be reviewed again
when a different corpus or new model measurements are published.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    folder = ROOT / "reports/model_eval"
    paths = [folder / "google-comparison-v2", folder / "google-additional"]
    metadata = [json.loads((p / "run.json").read_text(encoding="utf-8")) for p in paths]
    for field in ("code_signature", "corpus_hash", "catalog", "cases"):
        assert metadata[0][field] == metadata[1][field], field
    models, traces = {}, []
    for path in paths:
        summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
        assert not models.keys() & summary["models"].keys()
        models.update(summary["models"])
        traces.extend(
            json.loads(line)
            for line in (path / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
    completed = [name for name, value in models.items() if value["completed"]]
    assert len(completed) == 3
    ranking = sorted(
        completed,
        key=lambda name: (
            -models[name]["passed"],
            models[name]["invalid_calls"],
            models[name]["hypothetical_openrouter_usd"],
            models[name]["median_latency_s"],
        ),
    )
    cost = json.loads((folder / "continuation.json").read_text(encoding="utf-8"))[
        "google_spend"
    ]
    assert cost["conservative_used_usd"] <= 0.5
    paid_attempts = sum(r["kind"] == "attempt" for r in traces)
    passed = {name: models[name]["passed"] for name in completed}
    assert (
        passed["gemini-3.6-flash"] == 17
        and passed["gemini-3-flash-preview"] == 17
        and passed["gemini-3.5-flash-lite"] == 16
    )
    result = {
        "status": "measured_recommendation",
        "scope": "Google-native routing benchmark, three complete candidates and two access-limited candidates; not an OpenRouter deployment test.",
        "recommended_candidate": "gemini-3.6-flash",
        "recommended_openrouter_id": "google/gemini-3.6-flash",
        "recommendation_type": "Qualitative engineering choice between tied strict scores; not the mechanical cost tie-break winner.",
        "mechanical_ranking": ranking,
        "reason": "3.6 failure was presentation focus on N/A; Preview silently added a 60-Hz requirement. Prefer preserving technical conditions over the cost/latency tie-break.",
        "cases_per_complete_model": 18,
        "successful_generations": sum(v["evaluated"] for v in models.values()),
        "paid_inference_attempts": paid_attempts,
        "provider_error_attempts": sum(
            v["provider_error_attempts"] for v in models.values()
        ),
        "openrouter_inference_requests": 0,
        "google_spend": cost,
        "models": models,
        "protocol": metadata[0],
        "production_validation": "Pending: align OpenRouter client with tested generation settings, verify endpoint and latency before declaring deployed readiness.",
        "limitations": [
            "One sample per public development case; no statistical superiority claimed.",
            "Narrative and numerical rendering are deterministic backend code.",
            "Google503 rates are not measurements of OpenRouter availability.",
            "No comparative quality score for models that never generated a response.",
            "Token-price estimates and unknown-outcome reserves are not a billing-account statement.",
        ],
    }
    (folder / "comparison.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Comparación real de modelos Serie 76",
        "",
        "**Recomendación: Gemini 3.6 Flash como candidato para el assessment.** Empató en puntuación estricta con Flash Preview; la elección es un juicio técnico sobre la gravedad de los errores, no una superioridad estadística.",
        "",
        "## Resultados",
        "",
        "| Modelo | Casos correctos / evaluados | Mediana exitosa | Errores503 / intentos | Tokens: costo estimado de respuestas |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in (
        "gemini-3.6-flash",
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.1-flash-lite",
    ):
        value = models[name]
        score = (
            f"{value['passed']}/{value['evaluated']}"
            if value["evaluated"]
            else "Sin respuestas; no puntuable"
        )
        latency = (
            f"{value['median_latency_s']:.3f} s"
            if value["median_latency_s"] is not None
            else "—"
        )
        lines.append(
            f"| {name} | {score} | {latency} | {value['provider_error_attempts']}/{value['attempts']} | USD {value['hypothetical_openrouter_usd']:.5f} |"
        )
    lines += [
        "",
        "Las tarifas Google directas coinciden en esta fecha con las estimaciones de esos endpoints estándar Google AI Studio en OpenRouter; eso no constituye una llamada ni factura OpenRouter. Los errores de transporte no se anotaron como precisión cero. El resultado mantiene17/18 original para3.6; no se cambiaron reglas después de ver sus errores.",
        "",
        "## Por qué elegiría3.6 frente al empate",
        "",
        "- **3.6 Flash:** código y N/A correctos; omitió focus=motor_power en una petición adversarial y tomó overview. No inventó los999W solicitados. Faltó el aviso específico sobre potencia del motor frente a consumo total. Es un fallo de enfoque/presentación.",
        "- **3 Flash Preview:** añadió frequency_hz=60 sin autorización. Hoy devuelve las mismas siete referencias, pero guarda ese filtro en el contexto. En un seguimiento con máximo30s, el filtro supuesto devuelve tres referencias donde correspondía pedir frecuencia. Es una suposición técnica injustificada.",
        "- **3.5 Flash-Lite:** pidió repetir un código completo inexistente en vez de consultar su ausencia y confundió840arranques/h con ciclos/h. El esquema rechazó esta última consulta; el rechazo protege datos, pero no significa que el modelo entendiera el requisito.",
        "",
        f"El desempate mecánico original por costo/latencia favorece **{ranking[0]}**. La recomendación ingenieril prioriza no alterar condiciones técnicas. Esa preferencia cualitativa está separada de las puntuaciones y de los costos.3.6 sufrió seis503; no se oculta esta desventaja operacional ni se extrapola al proveedor de despliegue.",
        "",
        "## Gasto y acceso",
        "",
        f"{paid_attempts} intentos después de la recarga, {result['successful_generations']} generaciones exitosas y {result['provider_error_attempts']} errores de proveedor. Antes de la recarga hubo tres402 y un probe404 de un modelo retirado para usuarios nuevos; esos accesos no produjeron respuestas ni puntajes.",
        "",
        f"Costo calculado con tokens reportados: **USD {cost['measured_estimate_usd']:.8f}**. Reserva íntegra refinada para errores sin usage: **USD {cost['unknown_outcome_reserve_usd']:.8f}**. Total conservador del cliente: **USD {cost['conservative_used_usd']:.8f}**, bajo el tope compartido **USD0,50**. No se consultó saldo/factura ni se hizo conversión COP/USD. No hubo inferencias OpenRouter.",
        "",
        "Las reservas se refinaron con el payload exacto congelado, medido sin red, más4096tokens de sobrecarga y máximo2048tokens de salida/thinking. Los JSONL históricos permanecen intactos; los sidecars muestran el hash/bytes y la reserva original y refinada. Esos mocks no se incorporan a resultados de modelos. No hay grounding ni caché explícita con cargos adicionales.",
        "",
        "## Evidencia y reproducción",
        "",
        "- [Resultado completo](comparison.json), [cohorte inicial pagada](google-comparison-v2/summary.json), [alternativas](google-additional/summary.json), [presupuesto conjunto](continuation.json).",
        "- [Metodología y comandos](../../docs/MODEL_EVALUATION.md). Casos en model_eval/cases.py; JSONL completos por cohorte conservan intentos, llamadas y resultados reales de PostgreSQL.",
        "- Protocolo y corpus idénticos entre cohortes, misma versión SQL. Modelos no disponibles no entran en ranking de calidad. Dependencias congeladas en requirements-model-eval.lock.txt.",
        "- Investigación de precios/capacidades, construcción de casos y revisión de fallos se repartieron entre tres agentes. Solo el controlador hizo inferencias. La revisión independiente confirmó las diferencias sin inferencias adicionales.",
        "",
        "## Antes de producción",
        "",
        "Modelo propuesto OpenRouter: **google/gemini-3.6-flash**. La prueba actual fue con API nativa Google, thinking low, máximo2048tokens y muestreo predeterminado. El cliente de producción usa ahora otra configuración: temperatura0 y máximo600. Hay que alinearla y validar un pequeño conjunto por OpenRouter antes de declarar la integración verificada. No se modificó ese cliente concurrente ni se gastó su clave.",
        "",
        "El renderer todavía redacta en inglés y muestra Nm en el texto de torque mientras in-lb permanece en las tarjetas. Son aspectos del código, no diferencias de calidad lingüística entre modelos. Este corpus fijo de18casos no demuestra robustez universal; conviene añadir casos no utilizados para afinar el prompt al integrar el proveedor final.",
        "",
        "Fuentes: [precios Google](https://aistudio.google.com/docs/pricing), [cuotas](https://aistudio.google.com/docs/rate-limits), [errores](https://aistudio.google.com/docs/api-errors), [deprecaciones](https://aistudio.google.com/docs/deprecations), [endpoint3.6 OpenRouter](https://openrouter.ai/api/v1/models/google/gemini-3.6-flash/endpoints), [endpointPreview](https://openrouter.ai/api/v1/models/google/gemini-3-flash-preview/endpoints).",
        "",
    ]
    (folder / "RESULTADOS.md").write_text("\n".join(lines), encoding="utf-8")
    outputs = ["comparison.json", "RESULTADOS.md", "continuation.json"]
    outputs += [
        str(p.relative_to(folder))
        for root in paths
        for p in root.iterdir()
        if p.suffix in (".json", ".jsonl")
    ]
    manifest = {
        name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in sorted(outputs)
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "recommended": result["recommended_openrouter_id"],
                "mechanical_cost_tie_break": ranking[0],
                "paid_attempts": paid_attempts,
                "google_spend": cost,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
