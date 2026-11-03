"""Small YData report for the visual reference and actual selected OCR output."""
import json
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport

from scripts.ocr_lab import ROOT, normalize, write_json

FIELDS = ["source_table", "source_row", "base_part_number", "data_status",
          "motor_power_w", "on_off_torque_nm", "modulating_torque_nm",
          "shared_torque_nm", "fla_60hz_a", "fla_50hz_a", "fla_unqualified_a"]


def write_profile_index(out):
    """Expose the actual HTML reports beside the dated experiment directory."""
    from html import escape
    out = Path(out)
    folder = escape(out.name, quote=True)
    index = out.parent / "index.html"
    index.write_text(f'''<!doctype html>
<html lang="es"><meta charset="utf-8"><title>Serie 76 — informes ydata</title>
<style>body{{font:18px system-ui;max-width:850px;margin:60px auto;padding:0 24px;line-height:1.6}}a{{color:#1355ad}}</style>
<h1>Informes ydata-profiling</h1>
<p>Dos informes HTML reales: 68 filas, 11 columnas. Exploración mínima, sin imputación.</p>
<ul><li><a href="{folder}/ocr_profile.html">Abrir perfil de la salida del OCR seleccionado</a></li>
<li><a href="{folder}/reference_profile.html">Abrir perfil de la referencia visual revisada</a></li></ul>
<p>Los nulos pueden ser estructurales, N/A explícitos u omisiones OCR. En data_status,
la salida OCR solo marca cuatro N/A; los otros 64 estados aún no están normalizados.</p>
<p>El perfil describe los datos; no demuestra exactitud. Ver
<a href="RESULTADOS.md">resultados del benchmark</a> y <a href="discrepancies.csv">discrepancias</a>.</p>
</html>''', encoding="utf-8")
    return index


def profile(run_dir, out):
    run_dir, out = Path(run_dir), Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    selection = json.loads((run_dir / "selection.json").read_text(encoding="utf-8"))
    cells = pd.DataFrame(json.loads((run_dir / selection["engine"] / "cells.json").read_text(encoding="utf-8")))
    cells["value"] = cells.apply(lambda r: normalize(r.raw_text, r.field), axis=1)
    extracted = cells.pivot(index=["source_table", "source_row"], columns="field", values="value").reset_index()
    # A blank output is an OCR omission, not a claim that the source is N/A.
    extracted = extracted.reindex(columns=FIELDS)
    invalid_numeric = {}
    for col in FIELDS[4:]:
        numeric = pd.to_numeric(extracted[col], errors="coerce")
        invalid_numeric[col] = int((extracted[col].notna() & numeric.isna()).sum())
        extracted[col] = numeric
    reference = pd.read_csv(ROOT / "data/reference/serie76_tablas_extraidas.csv")[FIELDS]
    for name, data in (("reference", reference), ("ocr", extracted)):
        report = ProfileReport(data, title=f"Serie 76 - {name} (provisional)",
                               minimal=True, progress_bar=False, pool_size=1,
                               correlations={"auto": {"calculate": False}},
                               samples={"head": 0, "tail": 0, "random": 0})
        report.to_file(out / f"{name}_profile.html")
    summary = dict(reference_rows=len(reference), ocr_rows=len(extracted),
                   reference_unique_codes=int(reference.base_part_number.nunique()),
                   ocr_unique_codes=int(extracted.base_part_number.nunique()),
                   reference_explicit_NA=int((reference.data_status == "source_NA").sum()),
                   ocr_explicit_NA=int((extracted.data_status == "source_NA").sum()),
                   engine=selection["engine"],
                   invalid_numeric_tokens=invalid_numeric,
                   note="Nulls can be structural, explicit N/A or OCR omissions. Profiling does not prove numeric correctness; see discrepancies.csv.")
    extracted.to_csv(out / "ocr_profile_input.csv", index=False)
    write_json(out / "summary.json", summary)
    write_profile_index(out)
    return reference, extracted, summary
