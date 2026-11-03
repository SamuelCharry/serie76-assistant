"""Export the visually reviewed catalog; gate OCR against explicit reviewed cells.

This is OCR plus a human-readable visual-review record, not autonomous perfect OCR.
No reference CSV is read. No API calls, unit conversion, fuzzy repair or blind ffill.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/series_76_electric_data.pdf"
TRANSCRIPTION = ROOT / "data/manual/series76_visual_transcription.json"
CORRECTIONS = ROOT / "data/manual/approved_ocr_corrections.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def numeric(text):
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", text):
        raise ValueError(f"Invalid numeric source cell: {text!r}")
    value = text.replace(",", "")
    return float(value) if "." in value else int(value)


def canonical(text, field):
    value = re.sub(r"\s+", "", str(text))
    if field in {"base_part_number", "data_status"}:
        return value.upper()
    numeric(value)  # Reject BOO, punctuation hallucinations and malformed grouping.
    return Decimal(value.replace(",", ""))


def compile_transcription(source):
    rows, cells = [], []
    all_numeric = list(dict.fromkeys(c[0] for t in source["tables"] for c in t["columns"][1:]))
    identities = set()
    for table in source["tables"]:
        columns = table["columns"]
        if columns[0][0] != "base_part_number" or columns[-1][0] != "motor_power_w":
            raise ValueError("Unexpected source column order")
        present = {c[0] for c in columns[1:]}
        na = table.get("na_block")
        for number, values in enumerate(table["rows"], 1):
            is_na = bool(na and na["from_row"] <= number <= na["to_row"])
            if len(values) != (1 if is_na else len(columns) - 1):
                raise ValueError(f"{table['id']}/{number}: missing or extra source cells")
            original = values[0]
            code = original.rstrip("*")
            if not re.fullmatch(r"76[A-Z0-9]{4}-[A-Z0-9]{8}/A", code) or code in identities:
                raise ValueError(f"Invalid or duplicated complete part number: {original}")
            identities.add(code)
            row = dict(base_part_number=code, source_part_number=original,
                       enclosure=table["enclosure"], supply_voltage_v=table["voltage_v"],
                       supply_current=table["current"], phase_count=table["phases"],
                       source_page=table["page"], source_table=table["id"], source_row=number,
                       source_table_title=table["title"], service_layout=table["service_layout"],
                       data_status="source_NA" if is_na else "reported",
                       certification_header_raw=source["page_headers"][str(table["page"])],
                       source_footnote="*" if original.endswith("*") else None,
                       csa_status="explicitly_not_CSA_certified" if original.endswith("*") else "reported_in_header",
                       **{field: None for field in all_numeric})
            row["field_status"] = {field: "not_in_layout" for field in all_numeric}
            spans = [p for p in table["power_cells"] if p["from_row"] <= number <= p["to_row"]]
            if len(spans) != (0 if is_na else 1):
                raise ValueError(f"{table['id']}/{number}: overlapping or missing power span")
            for col, (field, header, unit) in enumerate(columns, 1):
                raw = original if col == 1 else "N/A" if is_na else spans[0]["text"] if field == "motor_power_w" else values[col - 1]
                state = "reported" if col == 1 or not is_na else "source_NA"
                value = code if col == 1 else None if is_na else numeric(raw)
                if col != 1:
                    row[field] = value
                    row["field_status"][field] = state
                span = [number, number]
                if is_na and col != 1:
                    span = [na["from_row"], na["to_row"]]
                elif field == "motor_power_w":
                    span = [spans[0]["from_row"], spans[0]["to_row"]]
                cells.append(dict(source_page=table["page"], source_table=table["id"],
                                  source_row=number, source_column=col, field=field,
                                  header=header, unit_raw=unit, raw_text=raw, value=value,
                                  status=state, source_span_rows=span,
                                  evidence=f"reports/manual_review/{table['id']}.png"))
            rows.append(row)
    return rows, cells


def verify_ocr(source, cells, folder, approvals):
    folder = Path(folder)
    manifest = read_json(folder / "manifest.json")
    if manifest["source_sha256"] != source["source_sha256"] or manifest["status"] != "ocr_completed_unvalidated":
        raise ValueError("OCR evidence is incomplete or belongs to another PDF")
    if {p["page"] for p in manifest["pages"]} != {1, 2, 3, 4}:
        raise ValueError("Missing OCR pages")
    if approvals["source_sha256"] != source["source_sha256"]:
        raise ValueError("Correction ledger belongs to another PDF")
    predictions = read_json(folder / "cells.json")
    indexed = {(c["source_table"], c["source_row"], c["field"]): c for c in predictions}
    if len(indexed) != len(predictions):
        raise ValueError("Duplicated OCR cell coordinates")
    allowed = {(c["table"], c["row"], c["field"]): c for c in approvals["corrections"]}
    expected_keys = {(c["source_table"], c["source_row"], c["field"]) for c in cells}
    for t in source["tables"]:
        na = t.get("na_block")
        if na:
            expected_keys |= {(t["id"], n, "data_status") for n in range(na["from_row"], na["to_row"] + 1)}
    if set(indexed) != expected_keys:
        raise ValueError("Missing or extra OCR grid cells; cannot silently export")
    ledger, checks = [], 0
    for c in cells:
        key = (c["source_table"], c["source_row"], c["field"])
        actual = indexed[key]["raw_text"]
        if c["status"] == "source_NA":
            if actual.strip():
                raise ValueError(f"Unexpected numeric content inside N/A: {key}: {actual!r}")
            continue
        checks += 1
        try:
            same = canonical(actual, c["field"]) == canonical(c["raw_text"], c["field"])
        except ValueError:
            same = False
        if same:
            continue
        decision = allowed.get(key)
        if not decision or actual != decision["ocr_text"] or c["raw_text"] != decision["source_text"]:
            raise ValueError(f"Unreviewed OCR mismatch {key}: {actual!r} vs {c['raw_text']!r}")
        ledger.append(dict(**decision, source_page=c["source_page"], source_column=c["source_column"],
                           status="corrected_after_visual_review"))
    for table in source["tables"]:
        na = table.get("na_block")
        if na:
            for n in range(na["from_row"], na["to_row"] + 1):
                actual = indexed[table["id"], n, "data_status"]["raw_text"]
                if canonical(actual, "data_status") != "N/A":
                    raise ValueError("N/A block not recognized; requires explicit review")
                checks += 1
    return dict(primary_cells_checked=checks, matching_ocr_cells=checks - len(ledger),
                corrections_applied=len(ledger), unreviewed_discrepancies=0, corrections=ledger)


def review_html(source):
    parts = ['<!doctype html><html lang="es"><meta charset="utf-8"><title>Serie 76 — transcripción revisada</title>',
             '<style>body{font:15px system-ui;margin:32px}table{border-collapse:collapse;margin:16px 0;font-variant-numeric:tabular-nums}th,td{border:1px solid #aaa;padding:7px;text-align:right}th{background:#edf1f4}td:first-child{text-align:left}tbody tr:nth-child(odd){background:#f5f5f5}section{overflow:auto;margin:35px 0}.na{text-align:center}li{margin:5px}</style>',
             '<h1>Serie 76: transcripción visual revisada</h1><p>68 referencias; cuatro N/A explícitos. Celdas combinadas conservadas mediante rowspan. Sin conversiones ni sustituciones intuitivas.</p>']
    for table in source["tables"]:
        parts += [f'<section id="{table["id"]}"><h2>Página {table["page"]} · {table["id"]} · {escape(table["title"])}</h2>',
                  f'<p>{escape(source["page_headers"][str(table["page"])])}</p><table><thead><tr>']
        for _, label, unit in table["columns"]:
            parts.append(f'<th>{escape(label)}<br>{escape(unit or "")}</th>')
        parts.append('</tr></thead><tbody>')
        na = table.get("na_block")
        for n, values in enumerate(table["rows"], 1):
            parts.append(f'<tr><td>{escape(values[0])}</td>')
            if na and na["from_row"] <= n <= na["to_row"]:
                if n == na["from_row"]:
                    parts.append(f'<td class="na" rowspan="{na["to_row"]-n+1}" colspan="{len(table["columns"])-1}">N/A</td>')
            else:
                parts += [f'<td>{escape(v)}</td>' for v in values[1:]]
                for power in table["power_cells"]:
                    if power["from_row"] == n:
                        parts.append(f'<td rowspan="{power["to_row"]-n+1}">{escape(power["text"])}</td>')
            parts.append('</tr>')
        parts.append('</tbody></table>')
        for note in table.get("footnotes", []):
            parts.append(f'<p>{escape(note["marker"])} {escape(note["text"])}</p>')
        parts.append('</section>')
    for page, notes in source["notes_by_page"].items():
        parts.append(f'<h2>Notas — página {page}</h2><ul>')
        for note in notes:
            prefix = f'{note["number"]}. ' if note["number"] is not None else ''
            parts.append(f'<li>{escape(prefix + note["text"])}')
            if note.get("items"):
                parts.append('<ul>' + ''.join(f'<li>{escape(item)}</li>' for item in note["items"]) + '</ul>')
            parts.append('</li>')
        parts.append('</ul>')
    parts.append('</html>')
    return '\n'.join(parts)


def export(pdf, ocr_dir, out):
    source = read_json(TRANSCRIPTION)
    if digest(pdf) != source["source_sha256"]:
        raise ValueError("Visual review belongs to another PDF; review the new source before export")
    rows, cells = compile_transcription(source)
    result = verify_ocr(source, cells, ocr_dir, read_json(CORRECTIONS))
    out = Path(out)
    if out.exists():
        raise FileExistsError("Choose a new output directory to preserve reviewed evidence")
    out.mkdir(parents=True)
    write_json(out / "catalog.json", dict(source_sha256=source["source_sha256"],
               method="local OCR plus complete visual transcription and explicit reviewed corrections",
               review_scope="all seven tables and four pages, AI visual review; no manufacturer certification or second human sign-off",
               rows=rows, notes_by_page=source["notes_by_page"], tables=source["tables"]))
    headers = [k for k in rows[0] if k != "field_status"]
    with (out / "catalog.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)
    with (out / "cells.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cells[0]))
        writer.writeheader(); writer.writerows(cells)
    (out / "review.html").write_text(review_html(source), encoding="utf-8")
    write_json(out / "review_log.json", result)
    manifest = dict(status="exported_after_complete_visual_review", source_sha256=digest(pdf),
                    transcription_sha256=digest(TRANSCRIPTION), approvals_sha256=digest(CORRECTIONS),
                    code_sha256=digest(__file__), ocr_evidence=str(Path(ocr_dir).resolve()),
                    created_utc=datetime.now(timezone.utc).isoformat(),
                    rows=len(rows), tables=len(source["tables"]), pages=4,
                    source_na_rows=sum(r["data_status"] == "source_NA" for r in rows),
                    reported_power_rows=sum(r["motor_power_w"] is not None for r in rows),
                    raw_ocr_is_perfect=False, external_api_calls=0,
                    primary_cells_checked=result["primary_cells_checked"],
                    corrections_applied=result["corrections_applied"], unreviewed_discrepancies=0)
    manifest["output_sha256"] = {p.name: digest(p) for p in out.iterdir() if p.is_file()}
    write_json(out / "manifest.json", manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf", type=Path, default=PDF)
    p.add_argument("--ocr-dir", type=Path, required=True, help="Completed raw OCR evidence directory")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(export(a.pdf, a.ocr_dir, a.out), indent=2))


if __name__ == "__main__":
    main()
