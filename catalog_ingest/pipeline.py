"""Page-streaming PDF ingestion with disk spooling and atomic validated exports."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import csv
import hashlib
from html import escape
from importlib.metadata import version
import json
import math
from pathlib import Path
import re
import sqlite3
import time

import cv2
import numpy as np
import pymupdf

from .geometry import infer_tables, GeometryError
from .metadata import page_metadata, table_footnotes
from .ocr import LocalOCR, atomic_json
from .processing import read_table


@dataclass(frozen=True)
class Config:
    dpi: int = 300
    max_pages: int = 2000
    max_pixels: int = 20_000_000
    max_pdf_bytes: int = 512 * 1024 * 1024
    max_tokens_per_page: int = 30_000
    max_rows_per_table: int = 1000
    max_fields: int = 128
    strict: bool = True
    keep_images: bool = True


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pipeline_signature(config: Config) -> str:
    digest = hashlib.sha256(json.dumps(asdict(config), sort_keys=True).encode())
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    for package in (
        "PyMuPDF",
        "onnxruntime",
        "rapidocr",
        "opencv-python-headless",
        "numpy",
    ):
        digest.update(package.encode())
        digest.update(version(package).encode())
    return digest.hexdigest()


def emit(stream, value):
    stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


class RowSpool:
    """Scratch storage only; this is not the application's PostgreSQL database."""

    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE rows (seq INTEGER PRIMARY KEY,payload TEXT)"
        )
        self.connection.execute(
            "CREATE TABLE identities (code TEXT PRIMARY KEY,signature TEXT,location TEXT)"
        )
        self.fields = []
        self.count = 0
        self.source_na = 0
        self.duplicates = 0

    def append(self, row: dict) -> dict | None:
        for field in row["field_status"]:
            if field not in self.fields:
                self.fields.append(field)
        code = row.get("base_part_number")
        if code:
            comparable = {
                k: v
                for k, v in row.items()
                if k in row["field_status"]
                or k
                in {
                    "enclosure",
                    "supply_voltage_v",
                    "supply_current",
                    "phase_count",
                    "data_status",
                    "source_part_number",
                }
            }
            signature = hashlib.sha256(
                json.dumps(comparable, sort_keys=True).encode()
            ).hexdigest()
            prior = self.connection.execute(
                "SELECT signature,location FROM identities WHERE code=?", (code,)
            ).fetchone()
            if prior and prior[0] != signature:
                return dict(
                    code="conflicting_duplicate_identity",
                    part_number=code,
                    first_location=prior[1],
                )
            if prior:
                self.duplicates += 1
            else:
                self.connection.execute(
                    "INSERT INTO identities VALUES (?,?,?)",
                    (
                        code,
                        signature,
                        f"page {row['source_page']}, {row['source_table']}, row {row['source_row']}",
                    ),
                )
        self.count += 1
        self.source_na += row["data_status"] == "source_NA"
        self.connection.execute(
            "INSERT INTO rows VALUES (?,?)",
            (self.count, json.dumps(row, ensure_ascii=False, allow_nan=False)),
        )
        return None

    def commit(self):
        self.connection.commit()

    def iter_rows(self):
        for (payload,) in self.connection.execute(
            "SELECT payload FROM rows ORDER BY seq"
        ):
            row = json.loads(payload)
            for field in self.fields:
                if field not in row["field_status"]:
                    row[field] = None
                    row["field_status"][field] = "not_in_layout"
            yield row

    def export(self, folder: Path, source: dict, page_files: list[Path]):
        common = [
            "base_part_number",
            "source_part_number",
            "enclosure",
            "supply_voltage_v",
            "supply_current",
            "phase_count",
            "data_status",
            "service_layout",
            "source_page",
            "source_table",
            "source_row",
            "source_table_title",
            "certification_header_raw",
            "source_footnote",
            "csa_status",
            "source_sha256",
        ]
        with (
            (folder / "catalog.csv.tmp").open(
                "w", encoding="utf-8-sig", newline=""
            ) as csvfile,
            (folder / "catalog.json.tmp").open("w", encoding="utf-8") as jsonfile,
        ):
            writer = csv.DictWriter(
                csvfile, fieldnames=common + self.fields, extrasaction="ignore"
            )
            writer.writeheader()
            jsonfile.write(
                '{"source":' + json.dumps(source, ensure_ascii=False) + ',"rows":['
            )
            for i, row in enumerate(self.iter_rows()):
                writer.writerow(row)
                jsonfile.write(
                    ("," if i else "")
                    + json.dumps(row, ensure_ascii=False, allow_nan=False)
                )
            jsonfile.write('],"pages":[')
            for i, path in enumerate(page_files):
                evidence = json.loads(path.read_text(encoding="utf-8"))
                metadata = {k: v for k, v in evidence.items() if k != "tokens"}
                jsonfile.write(
                    ("," if i else "")
                    + json.dumps(metadata, ensure_ascii=False, allow_nan=False)
                )
            jsonfile.write("]}")
        (folder / "catalog.csv.tmp").replace(folder / "catalog.csv")
        (folder / "catalog.json.tmp").replace(folder / "catalog.json")
        with (folder / "catalog.html.tmp").open("w", encoding="utf-8") as html:
            html.write(
                '<!doctype html><html lang="es"><meta charset="utf-8"><title>Catálogo extraído por OCR</title><style>body{font:14px system-ui;margin:30px}section{overflow:auto;margin:25px 0}table{border-collapse:collapse;font-variant-numeric:tabular-nums}td,th{padding:7px;border:1px solid #bbb;text-align:right}th{background:#eaf0f4}td:first-child{text-align:left}li{margin:8px 0}</style><h1>Catálogo extraído por OCR</h1><p>Valores derivados de la imagen; unidades, N/A y procedencia conservados. Consultar el manifiesto y cells.jsonl para lecturas y cajas.</p>'
            )
            current = None
            for row in self.iter_rows():
                if row["source_table"] != current:
                    if current is not None:
                        html.write("</tbody></table></section>")
                    current = row["source_table"]
                    evidence = json.loads(
                        page_files[row["source_page"] - 1].read_text(encoding="utf-8")
                    )
                    table = next(t for t in evidence["tables"] if t["id"] == current)
                    fields = [c["field"] for c in table["columns"]]
                    html.write(
                        "<section><h2>"
                        + escape(
                            f"Página {row['source_page']} · {row['source_table_title']} · {row['enclosure']}"
                        )
                        + "</h2><table><thead><tr><th>Base Part Number</th>"
                    )
                    for column in table["columns"]:
                        label = column["field"] + " · " + column["unit"]
                        if column["frequency_hz"] is not None:
                            label += f" · {column['frequency_hz']} Hz"
                        html.write("<th>" + escape(label) + "</th>")
                    html.write("</tr></thead><tbody>")
                html.write(
                    "<tr><td>" + escape(row["source_part_number"] or "") + "</td>"
                )
                for field in fields:
                    value = (
                        "N/A"
                        if row["field_status"][field] == "source_NA"
                        else str(row[field])
                    )
                    html.write("<td>" + escape(value) + "</td>")
                html.write("</tr>")
            if current is not None:
                html.write("</tbody></table></section>")
            for path in page_files:
                evidence = json.loads(path.read_text(encoding="utf-8"))
                if evidence.get("notes"):
                    html.write(f"<h2>Notas — página {evidence['page']}</h2><ul>")
                    for note in evidence["notes"]:
                        html.write("<li>" + escape(note["text"]) + "</li>")
                    html.write("</ul>")
            html.write("</html>")
        (folder / "catalog.html.tmp").replace(folder / "catalog.html")

    def close(self):
        self.connection.close()


def verified_result(folder: Path, source_hash: str, signature: str) -> dict | None:
    path = folder / "manifest.json"
    if not path.is_file():
        return None
    result = json.loads(path.read_text(encoding="utf-8"))
    if (
        result.get("source_sha256") != source_hash
        or result.get("pipeline_signature") != signature
    ):
        raise ValueError("Existing output belongs to a different source or pipeline")
    if result.get("status") != "ready":
        return result
    for name, checksum in result["artifact_sha256"].items():
        file = folder / name
        try:
            file.resolve().relative_to(folder.resolve())
        except ValueError:
            raise ValueError("Unsafe artifact path in an existing manifest") from None
        if not file.is_file() or file_hash(file) != checksum:
            raise ValueError(
                "Existing output failed integrity verification; choose a new output root"
            )
    return dict(result, reused=True)


def process_pdf(
    pdf: Path, output_root: Path, ocr: LocalOCR, config: Config
) -> tuple[Path, dict]:
    pdf = pdf.resolve()
    if not 120 <= config.dpi <= 450:
        raise ValueError("dpi must be between 120 and 450")
    if pdf.stat().st_size > config.max_pdf_bytes:
        raise ValueError("PDF exceeds the configured byte limit")
    source_hash = file_hash(pdf)
    signature = hashlib.sha256(
        (pipeline_signature(config) + ocr.signature).encode()
    ).hexdigest()
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", pdf.stem)[:48] or "document"
    folder = output_root / f"doc-{stem}-{source_hash[:16]}-{signature[:10]}"
    if folder.exists():
        existing = verified_result(folder, source_hash, signature)
        if existing is None:
            raise ValueError(
                "Incomplete existing output; choose a new output root. Inference caches remain reusable."
            )
        return folder, existing
    folder.mkdir(parents=True)
    evidence_dir = folder / "evidence"
    evidence_dir.mkdir()
    manifest = dict(
        status="processing",
        source_file=pdf.name,
        source_sha256=source_hash,
        pipeline_signature=signature,
        config=asdict(config),
        engine=ocr.settings,
        created_utc=datetime.now(timezone.utc).isoformat(),
        pages_completed=0,
        tables=0,
        rows=0,
        issues=0,
        notes_unconfirmed=0,
        external_api_calls=0,
        values_from_ocr=True,
        reference_values_loaded=False,
    )
    atomic_json(folder / "manifest.json", manifest)
    spool = RowSpool(folder / "work.sqlite3")
    page_files = []
    start = time.perf_counter()
    issues = 0
    cache_before = (ocr.cache.hits, ocr.cache.misses)
    try:
        with (
            pymupdf.open(pdf) as document,
            (folder / "cells.jsonl").open("w", encoding="utf-8") as cells_file,
            (folder / "review_queue.jsonl").open("w", encoding="utf-8") as queue,
        ):
            if document.needs_pass:
                raise ValueError("Encrypted PDF requires an accessible source")
            if not 0 < len(document) <= config.max_pages:
                raise ValueError("PDF page count exceeds the configured limit")
            manifest["pages"] = len(document)
            for index, page in enumerate(document, 1):
                page_start = time.perf_counter()
                pixels = math.ceil(page.rect.width * config.dpi / 72) * math.ceil(
                    page.rect.height * config.dpi / 72
                )
                if pixels > config.max_pixels:
                    raise ValueError(
                        f"Page {index} exceeds the configured raster pixel budget"
                    )
                pix = page.get_pixmap(dpi=config.dpi, alpha=False)
                image = cv2.cvtColor(
                    np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                        pix.height, pix.width, 3
                    ),
                    cv2.COLOR_RGB2BGR,
                )
                if config.keep_images:
                    pix.save(evidence_dir / f"page-{index:06}.png")
                tokens = ocr.page(image)
                if len(tokens) > config.max_tokens_per_page:
                    raise ValueError("Page token budget exceeded")
                page_info = dict(
                    page=index,
                    width=pix.width,
                    height=pix.height,
                    rotation=page.rotation,
                    tokens=[
                        dict(text=t.text, bbox=t.bbox, confidence=t.score)
                        for t in tokens
                    ],
                    tables=[],
                )
                try:
                    tables = infer_tables(tokens, pix.width, pix.height)
                    metadata = page_metadata(tokens, tables, image, ocr)
                    page_info.update(metadata)
                    manifest["notes_unconfirmed"] += sum(
                        n["status"] != "ocr_consensus" for n in metadata["notes"]
                    )
                    for note in metadata["notes"]:
                        if note["status"] != "ocr_consensus":
                            emit(
                                queue,
                                dict(
                                    code="unconfirmed_note",
                                    source_page=index,
                                    note=note,
                                ),
                            )
                            issues += 1
                    if tables and not metadata["enclosure"]:
                        raise GeometryError("Enclosure header could not be recognized")
                    for number, table in enumerate(tables, 1):
                        context = metadata["table_contexts"][number - 1]
                        if not context["enclosure"]:
                            raise GeometryError(
                                "Unrecognized or ambiguous table enclosure header"
                            )
                        table_id = f"p{index}_t{number}"
                        if len(table.rows) > config.max_rows_per_table:
                            raise GeometryError("Table row budget exceeded")
                        rows, problems, detail = read_table(
                            table, tokens, image, ocr, config.strict
                        )
                        footnotes = table_footnotes(metadata["notes"], table, tables)
                        for row in rows:
                            marker = (
                                "*"
                                if row.get("source_part_number", "")
                                and row["source_part_number"].endswith("*")
                                else None
                            )
                            note = " ".join(n["text"] for n in footnotes)
                            exception = bool(
                                marker
                                and re.search(r"NOT\s*CSA\s*CERTIFIED", note, re.I)
                            )
                            row.update(
                                source_sha256=source_hash,
                                source_file=pdf.name,
                                source_page=index,
                                source_table=table_id,
                                source_table_title=table.title,
                                enclosure=context["enclosure"],
                                certification_header_raw=context[
                                    "certification_header_raw"
                                ],
                                source_footnote=marker,
                                csa_status="explicitly_not_CSA_certified"
                                if exception
                                else "exception_unresolved"
                                if marker
                                else "reported_in_header"
                                if re.search(
                                    r"\bCSA\b", context["certification_header_raw"]
                                )
                                else "not_reported",
                            )
                            if marker and not footnotes:
                                problems.append(
                                    dict(
                                        code="missing_footnote",
                                        source_row=row["source_row"],
                                    )
                                )
                            if marker and not exception:
                                problems.append(
                                    dict(
                                        code="unresolved_certification_exception",
                                        source_row=row["source_row"],
                                    )
                                )
                            conflict = spool.append(row)
                            if conflict:
                                problems.append(conflict)
                            if len(spool.fields) > config.max_fields:
                                raise GeometryError(
                                    "Distinct measurement field budget exceeded"
                                )
                        for cell in detail["cells"]:
                            emit(
                                cells_file,
                                dict(
                                    source_page=index,
                                    source_table=table_id,
                                    source_sha256=source_hash,
                                    **cell,
                                ),
                            )
                        for problem in problems:
                            emit(
                                queue,
                                dict(
                                    source_page=index, source_table=table_id, **problem
                                ),
                            )
                            issues += 1
                        page_info["tables"].append(
                            dict(
                                context=context,
                                id=table_id,
                                title=table.title,
                                header_bbox=table.header_bbox,
                                family=table.family,
                                row_count=len(rows),
                                columns=[asdict_column(c) for c in table.columns],
                                power_rules=detail["power_rules"],
                                na_rows=detail["na_rows"],
                            )
                        )
                        manifest["tables"] += 1
                except GeometryError as error:
                    emit(
                        queue,
                        dict(
                            code="unsupported_or_ambiguous_layout",
                            source_page=index,
                            error=str(error),
                        ),
                    )
                    issues += 1
                path = evidence_dir / f"page-{index:06}.json"
                atomic_json(path, page_info)
                page_files.append(path)
                spool.commit()
                manifest.update(pages_completed=index, rows=spool.count, issues=issues)
                atomic_json(folder / "manifest.json", manifest)
                print(
                    f"{pdf.name}: page {index}/{len(document)}, rows={spool.count}, issues={issues}, {time.perf_counter() - page_start:.1f}s",
                    flush=True,
                )
                del image, pix, tokens
        if not spool.count:
            issues += 1
            with (folder / "review_queue.jsonl").open("a", encoding="utf-8") as queue:
                emit(queue, dict(code="no_supported_product_tables"))
        if issues == 0:
            spool.export(
                folder,
                dict(file=pdf.name, sha256=source_hash, pipeline_signature=signature),
                page_files,
            )
            manifest["status"] = "ready"
        else:
            manifest["status"] = "needs_review"
        manifest.update(
            rows=spool.count,
            source_na_rows=spool.source_na,
            identical_duplicate_rows=spool.duplicates,
            issues=issues,
            cache_hits=ocr.cache.hits - cache_before[0],
            cache_misses=ocr.cache.misses - cache_before[1],
            elapsed_seconds=time.perf_counter() - start,
        )
    except Exception as error:
        manifest.update(
            status="failed",
            error=f"{type(error).__name__}: {error}",
            elapsed_seconds=time.perf_counter() - start,
        )
    finally:
        spool.close()
        manifest["artifact_sha256"] = {
            str(p.relative_to(folder)).replace("\\", "/"): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name not in {"manifest.json", "work.sqlite3"}
        }
        atomic_json(folder / "manifest.json", manifest)
    return folder, manifest


def asdict_column(column):
    return dict(
        field=column.field,
        center=column.center,
        raw_unit=column.raw_unit,
        unit=column.unit,
        service=column.service,
        frequency_hz=column.frequency_hz,
    )
