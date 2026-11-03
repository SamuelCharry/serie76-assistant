"""Build a self-contained architecture viewer from inspected database metadata."""
import html
import json
from pathlib import Path


def esc(value):
    return html.escape(str(value))


def build():
    data = json.loads(Path("reports/architecture_eval/database.json").read_text())
    positions = {"documents":(20,30),"imports":(375,30),"catalog_state":(730,30),"conversations":(1085,30),
                 "source_tables":(20,390),"entries":(375,390),"messages":(1085,390),
                 "service_specs":(20,1040),"frequency_specs":(375,1040),"source_cells":(730,1040),"schema_migrations":(1085,1040)}
    columns = {name:[c for c in data["columns"] if c["table_name"]==name] for name in positions}
    cards, edges = [], []
    for name, (x,y) in positions.items():
        rows = columns[name]
        height = 52+len(rows)*24
        card = f'<g tabindex="0"><title>{esc(name)}: columnas reales PostgreSQL</title><rect x="{x}" y="{y}" width="330" height="{height}" rx="10" fill="#fff" stroke="#b8aaca"/><text x="{x+14}" y="{y+29}" class="entity">{name}</text>'
        for i,c in enumerate(rows):
            required = " *" if c["is_nullable"]=="NO" else ""
            card += f'<text x="{x+14}" y="{y+59+i*24}" class="column">{esc(c["column_name"]+required)}<title>{esc(c["data_type"])}</title></text>'
        cards.append(card+"</g>")
    for fk in data["foreign_keys"]:
        child, parent = fk["child"].split(".")[-1], fk["parent"].split(".")[-1]
        if child not in positions or parent not in positions:
            continue
        x1,y1=positions[parent]; x2,y2=positions[child]
        h1=52+len(columns[parent])*24
        if y1==y2:
            start=(x1+330,y1+45); end=(x2,y2+45)
        else:
            start=(x1+165,y1+h1); end=(x2+165,y2)
        edges.append(f'<path d="M {start[0]} {start[1]} L {end[0]} {end[1]}" fill="none" stroke="#80628d" stroke-width="2" marker-end="url(#arrow)"><title>{esc(fk["definition"])}</title></path>')
        if y1 != y2:
            cardinality = "1 a 0..1" if child=="catalog_state" else "1 a 0..N"
            edges.append(f'<text x="{(start[0]+end[0])/2+8}" y="{(start[1]+end[1])/2-8}" font-size="12" fill="#56385f">{cardinality}</text>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 1400" role="img" aria-label="Modelo entidad relación actual"><style>.entity{font:bold 17px sans-serif;fill:#56385f}.column{font:13px monospace;fill:#302636}</style><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#80628d"/></marker></defs>'+"".join(edges+cards)+"</svg>"
    Path("docs/er-series76.svg").write_text(svg,encoding="utf-8")
    flows={
      "A":("Actual: un agente",["Pregunta + historial","LLM interpreta","Herramientas SQL","Respuesta / aclaración"]),
      "B":("Un agente con contexto",["Pregunta + historial","pgvector resumen","LLM interpreta","Herramientas SQL","Respuesta / aclaración"]),
      "C":("Dos especialistas · máximo 2 llamadas",["Pregunta + historial","pgvector resumen","Agente contextual","Agente catálogo","Herramientas SQL","Respuesta / aclaración"]),
      "D":("Supervisor · máximo 3 llamadas",["Pregunta + historial","Supervisor","Contexto si hace falta","Agente catálogo","Herramientas SQL","Respuesta / aclaración"]),
      "E":("Proponente y revisor · máximo 2 llamadas",["Pregunta + historial","pgvector resumen","Proponente + SQL","Revisor independiente","Acepta / aclara"])}
    panels=[]
    for key,(label,nodes) in flows.items():
        width=220*len(nodes)
        content=f'<section class="flow" id="flow-{key}" {"" if key=="A" else "hidden"}><h2>{esc(label)}</h2><svg viewBox="0 0 {width} 150" role="img" aria-label="{esc(label)}">'
        for i,node in enumerate(nodes):
            x=10+i*220
            if i:
                content+=f'<text x="{x-24}" y="78" fill="#80628d" font-size="22">→</text>'
            content+=f'<rect x="{x}" y="35" width="190" height="75" rx="8" fill="#efe7f5"/><text x="{x+95}" y="77" text-anchor="middle" font-size="13">{esc(node)}</text>'
        content+='</svg><p>El original y el historial llegan al decisor final. Las cifras y compatibilidad se validan contra SQL. Los agentes pueden pedir aclaraciones; no completar requisitos ausentes.</p></section>'
        panels.append(content)
    keys="".join(f'<button type="button" onclick="showFlow(\'{k}\')" aria-pressed="{str(k=="A").lower()}" id="button-{k}">{k} · {esc(v[0].split(" ·")[0])}</button>' for k,v in flows.items())
    constraints="".join(f'<li><strong>{esc(f["child"])}</strong> → {esc(f["parent"])}: <code>{esc(f["definition"])}</code></li>' for f in data["foreign_keys"])
    document='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Series 76 · Arquitectura</title><style>
body{margin:0;background:#faf8fc;color:#28202d;font:16px/1.6 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:32px}h1{font-size:32px;margin-bottom:6px}h2{font-size:22px}p{max-width:980px}nav{display:flex;gap:8px;flex-wrap:wrap}button{font:inherit;padding:9px 14px;border:1px solid #947aa7;border-radius:8px;background:white;cursor:pointer}button[aria-pressed=true]{background:#56385f;color:white}button:focus-visible{outline:3px solid #245ee8;outline-offset:3px}svg{width:100%;height:auto}section{margin:24px 0;padding:20px;background:white;border:1px solid #e1d8e8;border-radius:12px}.entity{font:600 17px system-ui;fill:#56385f}.column{font:13px ui-monospace,monospace;fill:#302636}.scroll{overflow:auto}.scroll svg{min-width:1000px}code{overflow-wrap:anywhere}a{color:#60367a}[hidden]{display:none}small{color:#64566a}</style><main>
<h1>Series 76 · Arquitectura y datos</h1><p>Implementación actual y cinco configuraciones experimentales. La búsqueda semántica explica términos; PostgreSQL conserva las cifras y aplica los requisitos.</p>
<nav aria-label="Configuración">'''+keys+"</nav>"+"".join(panels)+'''<section><h2>Modelo entidad–relación actual</h2><p>Columnas inspeccionadas en PostgreSQL. * = NOT NULL. Pase el cursor por una columna para ver su tipo o por una relación para ver su FK. El modelo experimental de fragmentos está separado.</p><div class="scroll">'''+svg+'''</div><details><summary>Claves foráneas exactas</summary><ul>'''+constraints+'''</ul></details><p>PK: documents.sha256; imports.id; catalog_state.singleton; source_tables.id; entries.id; service_specs(entry_id,service); frequency_specs.id; source_cells(entry_id,field); conversations.id; messages.sequence; schema_migrations.name.</p><p>Unicidad compuesta de imports(document_sha256,pipeline_signature); source_tables(import_id,source_table) y (id,import_id); entries(table_id,source_row); frequency_specs(entry_id,frequency_hz), incluidos nulos; messages.id es único. El código de parte está indexado y conserva apariciones/versiones.</p></section>
<section><h2>Ampliación experimental: pgvector</h2><p>Instancia independiente en 127.0.0.1:5543. chunks(index_signature, id, metadata JSONB, embedding vector(768)). PK compuesta. metadata conserva documento, hash, página, sección, texto y tokens. Sin FK a productos: una definición general no acredita una especificación de una referencia.</p><p><a href="ARCHITECTURE_EVALUATION.md">Protocolo reproducible</a> · <a href="../reports/architecture_eval/ANALISIS.md">Resultados reales</a></p></section><small>Los diagramas describen responsabilidades, no una mejora demostrada. No se modificó el chat operativo.</small></main><script>
function showFlow(k){document.querySelectorAll('.flow').forEach(e=>e.hidden=e.id!=='flow-'+k);document.querySelectorAll('nav button').forEach(e=>e.setAttribute('aria-pressed',String(e.id==='button-'+k)));}
</script></html>'''
    Path("docs/architecture.html").write_text(document,encoding="utf-8")


if __name__=="__main__":
    build()
