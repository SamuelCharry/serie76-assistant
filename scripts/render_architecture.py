"""Build docs/architecture.html and docs/er-series76.svg from the LIVE PostgreSQL schema.

  python scripts/render_architecture.py            # inspect DB -> docs/evidence/data/architecture-database.json -> render
  python scripts/render_architecture.py --offline  # render from the saved database.json
The A-E flows are kept as a historical appendix (code archived at tag arch-eval-cohort-1).
"""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SNAPSHOT = ROOT / "docs/evidence/data/architecture-database.json"

GROUPS = [
    ("Catálogo eléctrico (única fuente de cifras)", ["documents", "imports", "catalog_state", "source_tables"]),
    ("Mediciones y evidencia", ["entries", "service_specs", "frequency_specs", "source_cells"]),
    ("Glosario del resumen y conversaciones", ["context_terms", "conversations", "messages", "schema_migrations"]),
    ("Login (bloque concurrente)", ["users", "auth_sessions", "auth_login_limits"]),
]


def esc(value):
    return html.escape(str(value))


def inspect():
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    local_environment()
    with connect() as c:
        columns = c.execute("""SELECT table_name,column_name,data_type,is_nullable,ordinal_position
            FROM information_schema.columns WHERE table_schema='series76' ORDER BY table_name,ordinal_position""").fetchall()
        fks = c.execute("""SELECT conrelid::regclass::text AS child, confrelid::regclass::text AS parent,
            pg_get_constraintdef(oid) AS definition FROM pg_constraint
            WHERE connamespace='series76'::regnamespace AND contype='f' ORDER BY 1,2,3""").fetchall()
        keys = c.execute("""SELECT conrelid::regclass::text AS table_name, contype, pg_get_constraintdef(oid) AS definition
            FROM pg_constraint WHERE connamespace='series76'::regnamespace AND contype IN ('p','u') ORDER BY 1,2,3""").fetchall()
    data = dict(columns=[dict(r) for r in columns], foreign_keys=[dict(r) for r in fks], keys=[dict(r) for r in keys])
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def er_svg(data):
    columns = {}
    for c in data["columns"]:
        columns.setdefault(c["table_name"], []).append(c)
    known = {t for _, tables in GROUPS for t in tables}
    missing = sorted(set(columns) - known)
    if missing:
        raise SystemExit(f"Tables not placed in the diagram: {missing}")
    width, gap, positions, cards, y = 330, 30, {}, [], 20
    for title, tables in GROUPS:
        cards.append(f'<text x="20" y="{y + 18}" font-family="sans-serif" font-size="15" font-weight="600" fill="#6b5576">{esc(title)}</text>')
        y += 54  # title sits above the routing lanes that run just over each row
        tallest = 0
        for i, name in enumerate(tables):
            x = 20 + i * (width + gap)
            rows = columns.get(name, [])
            height = 52 + len(rows) * 22
            positions[name] = (x, y, height)
            tallest = max(tallest, height)
            card = (f'<g tabindex="0"><title>{esc(name)}</title><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" '
                    f'fill="#ffffff" stroke="#b8aaca"/><text x="{x + 14}" y="{y + 29}" font-family="sans-serif" font-size="16" font-weight="bold" fill="#56385f">{esc(name)}</text>')
            for j, c in enumerate(rows):
                mark = " *" if c["is_nullable"] == "NO" else ""
                card += (f'<text x="{x + 14}" y="{y + 56 + j * 22}" font-family="monospace" font-size="12.5" fill="#302636">{esc(c["column_name"] + mark)}'
                         f'<tspan fill="#8a7a92"> {esc(c["data_type"])}</tspan></text>')
            cards.append(card + "</g>")
        y += tallest + 50
    # Orthogonal routing through the free lanes between rows and the gutters between columns,
    # drawn beneath the cards, so no relation line crosses a table.
    row_bottom = {}
    for _, tables in GROUPS:
        bottom = max(positions[t][1] + positions[t][2] for t in tables)
        row_bottom.update({t: bottom for t in tables})
    edges = []
    for k, fk in enumerate(data["foreign_keys"]):
        child, parent = fk["child"].split(".")[-1], fk["parent"].split(".")[-1]
        (px, py, ph), (cx, cy, ch) = positions[parent], positions[child]
        offset = (k % 4) * 6
        if py == cy and abs(px - cx) == width + gap:
            left, right = (px, cx) if px < cx else (cx, px)
            points = [(px + width if px < cx else px, py + 40 + offset), (cx if px < cx else cx + width, cy + 40 + offset)]
        elif py == cy:
            lane = py - 10 - offset
            points = [(px + width / 2 + offset, py), (px + width / 2 + offset, lane), (cx + width / 2 - offset, lane), (cx + width / 2 - offset, cy)]
        elif py < cy:
            below, above = row_bottom[parent] + 12 + offset, cy - 8 - offset
            gutter = cx - gap / 2 + (k % 3) * 4 - 4
            points = [(px + width / 2 - 30 + offset, py + ph), (px + width / 2 - 30 + offset, below), (gutter, below),
                      (gutter, above), (cx + width / 2 - 30 + offset, above), (cx + width / 2 - 30 + offset, cy)]
        else:
            above_parent, below_child = py - 8 - offset, row_bottom[child] + 12 + offset
            gutter = px - gap / 2 + (k % 3) * 4 - 4
            points = [(px + width / 2 + 30 - offset, py), (px + width / 2 + 30 - offset, above_parent), (gutter, above_parent),
                      (gutter, below_child), (cx + width / 2 + 30 - offset, below_child), (cx + width / 2 + 30 - offset, cy + ch)]
        path = "M " + " L ".join(f"{x:.0f} {y_:.0f}" for x, y_ in points)
        edges.append(f'<path d="{path}" fill="none" stroke="#80628d" stroke-width="1.6" opacity="0.8" marker-end="url(#arrow)">'
                     f'<title>{esc(fk["child"])} → {esc(fk["parent"])}: {esc(fk["definition"])}</title></path>')
    total_w = 20 + 4 * (width + gap)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {y}" role="img" aria-label="Modelo entidad relación de PostgreSQL">'
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#80628d"/></marker></defs>' + "".join(edges + cards) + "</svg>")


def flow_svg(nodes):
    width = 210 * len(nodes)
    out = f'<svg viewBox="0 0 {width} 130" role="img" aria-label="{esc(" → ".join(nodes))}">'
    for i, node in enumerate(nodes):
        x = 8 + i * 210
        if i:
            out += f'<text x="{x - 24}" y="72" fill="#80628d" font-size="22">→</text>'
        out += f'<rect x="{x}" y="22" width="182" height="86" rx="8" fill="#efe7f5"/>'
        for k, line in enumerate(node.split("\n")):
            out += f'<text x="{x + 91}" y="{58 + k * 17}" text-anchor="middle" font-size="13">{esc(line)}</text>'
    return out + "</svg>"


FINAL = ["Pregunta\n+ historial + contexto", "LLM: 1 decisión\n(tool + argumentos)", "Política en código\ncódigos · fundamentos\nfusión · conflictos",
         "SQL parametrizado\ncatálogo / glosario", "Plantillas\nrespuesta + fichas", "PostgreSQL\nmensajes + trazas"]
HISTORICAL = {
    "A": ("Agente único con SQL", ["Pregunta + historial", "LLM interpreta", "Herramientas SQL", "Respuesta / aclaración"]),
    "B": ("Agente + pgvector", ["Pregunta + historial", "pgvector resumen", "LLM interpreta", "Herramientas SQL", "Respuesta / aclaración"]),
    "C": ("Dos especialistas", ["Pregunta + historial", "pgvector resumen", "Agente contextual", "Agente catálogo", "Herramientas SQL"]),
    "D": ("Supervisor", ["Pregunta + historial", "Supervisor", "Contexto si hace falta", "Agente catálogo", "Herramientas SQL"]),
    "E": ("Proponente y revisor", ["Pregunta + historial", "pgvector resumen", "Proponente + SQL", "Revisor", "Acepta / aclara"]),
}


def build(data):
    svg = er_svg(data)
    (ROOT / "docs/er-series76.svg").write_text(svg, encoding="utf-8")
    fks = "".join(f'<li><strong>{esc(f["child"])}</strong> → {esc(f["parent"])}: <code>{esc(f["definition"])}</code></li>' for f in data["foreign_keys"])
    keys = "".join(f'<li><strong>{esc(k["table_name"])}</strong> {"PK" if k["contype"] == "p" else "UNIQUE"} <code>{esc(k["definition"])}</code></li>' for k in data["keys"])
    history = "".join(f'<details><summary>{k} · {esc(label)}</summary>{flow_svg(nodes)}</details>' for k, (label, nodes) in HISTORICAL.items())
    page = f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Series 76 · Arquitectura</title><style>
:root{{--bg:#faf8fc;--fg:#28202d;--card:#fff;--line:#e1d8e8;--accent:#56385f}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#1d1820;--fg:#eee6f2;--card:#2a2330;--line:#43384a;--accent:#d9b8e8}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}}main{{max-width:1480px;margin:auto;padding:16px 16px 48px}}
h1{{font-size:30px;margin:12px 0 4px}}h2{{font-size:21px;color:var(--accent)}}p,li{{max-width:1000px}}section{{margin:20px 0;padding:18px;background:var(--card);border:1px solid var(--line);border-radius:12px}}
svg{{width:100%;height:auto;background:#fff;border-radius:8px}}.scroll{{overflow:auto}}.scroll svg{{min-width:1100px}}code{{overflow-wrap:anywhere}}a{{color:var(--accent)}}
summary{{cursor:pointer;font-weight:600;margin:8px 0}}table{{border-collapse:collapse}}td,th{{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}}</style><main>
<h1>Series 76 · Arquitectura y datos</h1>
<p>Arquitectura elegida: <strong>A+</strong>, un agente LangChain con una decisión por turno y herramientas deterministas. El LLM interpreta; el código valida y consulta; las respuestas se redactan desde SQL o desde citas literales. <a href="adr/0001-arquitectura-agente.md">ADR 0001</a>.</p>
<section><h2>Flujo de un turno</h2>{flow_svg(FINAL)}
<table><tr><th>Responsabilidad</th><th>Quién</th></tr>
<tr><td>Entender lenguaje informal, intención y referencias ("it")</td><td>LLM (una llamada, una tool)</td></tr>
<tr><td>Canonicalizar códigos sin completarlos; fundamentar cada valor en la conversación</td><td>Código (policy.py)</td></tr>
<tr><td>Fusionar seguimientos (delta) y detectar contradicciones</td><td>Código (policy.py)</td></tr>
<tr><td>Cifras, filtros, servicio, frecuencia, N/A</td><td>SQL sobre el catálogo del PDF eléctrico</td></tr>
<tr><td>Definiciones (S4, FLA, LRA…)</td><td>Tabla context_terms: texto literal del resumen + página</td></tr>
<tr><td>Redacción de la respuesta</td><td>Plantillas (rendering.py); el LLM no escribe cifras</td></tr></table></section>
<section><h2>Modelo entidad–relación (PostgreSQL inspeccionado)</h2><p>* = NOT NULL. Generado desde information_schema y pg_constraint. Sin pgvector: la tabla experimental de fragmentos vive solo en la instancia archivada.</p>
<div class="scroll">{svg}</div><details><summary>Claves foráneas</summary><ul>{fks}</ul></details><details><summary>Claves primarias y unicidad</summary><ul>{keys}</ul></details></section>
<section><h2>Apéndice histórico: configuraciones A–E</h2><p>Comparación inconclusa (1 escenario común de 24, 19 fallos de proveedor). Código y evidencia en el tag <code>arch-eval-cohort-1</code>; <a href="evidence/architecture_comparison.md">análisis</a>. No es un ranking.</p>{history}</section>
</main></html>'''
    (ROOT / "docs/architecture.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    build(json.loads(SNAPSHOT.read_text(encoding="utf-8")) if args.offline else inspect())
    print("ok")
