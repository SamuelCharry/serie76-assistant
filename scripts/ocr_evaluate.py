"""Compare OCR evidence with the fallible visual reference, without changing predictions."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

from scripts.ocr_lab import ROOT, PDF, normalize, reconstruct, sha256, write_json

ENGINES = ("tesseract", "easyocr", "rapidocr")
REFERENCE = ROOT / "data/reference/serie76_tablas_extraidas.csv"


def evaluate(run_dir):
    run_dir = Path(run_dir)
    with REFERENCE.open(encoding="utf-8-sig", newline="") as stream:
        reference = {(r["source_table"], int(r["source_row"])): r for r in csv.DictReader(stream)}
    comparisons, summaries = [], []
    for engine in ENGINES:
        folder = run_dir / engine
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if manifest["status"] != "ocr_completed_unvalidated":
            raise ValueError(f"{engine} did not complete; cannot select a winner")
        if manifest["source_sha256"] != sha256(PDF):
            raise ValueError("OCR evidence and source PDF differ")
        cells = json.loads((folder / "cells.json").read_text(encoding="utf-8"))
        expected_keys = {(c["source_table"], c["source_row"], c["field"])
                         for c in reconstruct({p: [] for p in range(1, 5)}, 300)}
        actual_keys = [(c["source_table"], c["source_row"], c["field"]) for c in cells]
        if set(actual_keys) != expected_keys or len(actual_keys) != len(expected_keys):
            raise ValueError(f"{engine}: incomplete or duplicated cell grid")
        if manifest["dpi"] != 300 or manifest["engine"] != engine:
            raise ValueError(f"{engine}: mismatched benchmark settings")
        records = []
        for cell in cells:
            row = reference[(cell["source_table"], cell["source_row"])]
            field = cell["field"]
            expected = row[field]
            actual = normalize(cell["raw_text"], field)
            # Absent numeric columns in the N/A block are not free true positives.
            if not expected:
                if actual is not None:
                    records.append(dict(engine=engine, **cell, expected=None,
                                        actual=actual, exact=False, kind="unexpected_in_NA"))
                continue
            kind = "code" if field == "base_part_number" else "status" if field == "data_status" else "numeric"
            records.append(dict(engine=engine, **cell, expected=normalize(expected, field),
                                actual=actual, exact=actual == normalize(expected, field), kind=kind))
        # Annotation is distinct from normalized product identity.
        for cell in (c for c in cells if c["field"] == "base_part_number"):
            expected_star = reference[(cell["source_table"], cell["source_row"])]["source_part_number"].endswith("*")
            actual_star = cell["raw_text"].strip().endswith("*")
            records.append(dict(engine=engine, **{**cell, "field": "footnote_marker"},
                                expected=expected_star, actual=actual_star,
                                exact=expected_star == actual_star, kind="annotation"))
        frame = pd.DataFrame(records)
        scored = frame[frame.kind != "annotation"]
        summary = dict(engine=engine, cells=len(scored), exact=int(scored.exact.sum()),
                       errors=int((~scored.exact).sum()),
                       complete_rows=int(scored.groupby(["source_table", "source_row"]).exact.all().sum()),
                       inference_seconds=sum(p["seconds"] for p in manifest["pages"]),
                       load_seconds=manifest["load_seconds"])
        for kind in ("code", "numeric", "status"):
            subset = frame[frame.kind == kind]
            summary[f"{kind}_exact"] = int(subset.exact.sum())
            summary[f"{kind}_total"] = len(subset)
        summary["csa_markers_exact"] = int(frame[(frame.kind == "annotation") & (frame.expected == True)].exact.sum())
        summaries.append(summary)
        comparisons.extend(records)
    metrics = pd.DataFrame(summaries).sort_values(
        ["errors", "complete_rows", "inference_seconds"], ascending=[True, False, True]).reset_index(drop=True)
    details = pd.DataFrame(comparisons)
    metrics.to_csv(run_dir / "metrics.csv", index=False)
    details.to_csv(run_dir / "comparisons.csv", index=False)
    details[~details.exact].to_csv(run_dir / "discrepancies.csv", index=False)
    selected = metrics.iloc[0].engine
    config = dict(engine=selected, dpi=300, source_sha256=sha256(PDF),
                  benchmark=str(run_dir.relative_to(ROOT)),
                  reference_sha256=sha256(REFERENCE), layout="fixed-series76-v1",
                  selection_rule="fewest unequal cells, then complete rows, then inference time",
                  validated_table_data=False,
                  limitations="Best of these three tested configurations on this PDF; reference is provisional. Review discrepancies before database import.")
    write_json(run_dir / "selection.json", config)
    return metrics, details, config


def benchmark(out=None):
    out = Path(out or ROOT / "data/ocr" / ("benchmark-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")))
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    failures = []
    for engine in ENGINES:
        try:
            subprocess.run([sys.executable, str(ROOT / "scripts/ocr_lab.py"),
                            "--engine", engine, "--out", str(out / engine)],
                           cwd=ROOT, check=True, timeout=1200)
        except (subprocess.SubprocessError, OSError) as error:
            failures.append(f"{engine}: {error}")
    write_json(out / "experiment.json", dict(
        source_sha256=sha256(PDF), reference_sha256=sha256(REFERENCE),
        engines=list(ENGINES), failures=failures, external_api_calls=0,
        comparison="same four full pages, 300 DPI, CPU, fixed geometry shared by all engines",
        scope="Reference comparison, not independent ground truth; confidence is not accuracy"))
    if failures:
        raise RuntimeError("Three-way benchmark incomplete: " + "; ".join(failures))
    return out, *evaluate(out)
