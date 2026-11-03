"""Local OCR adapters and fixed-layout reconstruction. Never reads reference answers.

The layout is manually measured from this four-page PDF, not a generic table detector.
Coordinates in the layout use a 120 DPI rendering; evidence uses the requested DPI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import time

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/series_76_electric_data.pdf"
CATALOG_SHA256 = "4c28023929183df8e2a763e759cc84572b44604b30837a21e22c1166f88267e0"
CACHE = ROOT / ".cache/ocr"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


MIXED = ["base_part_number", "on_off_torque_in_lb", "on_off_torque_nm",
         "on_off_duty_s4_percent", "cycles_per_hour", "modulating_torque_in_lb",
         "modulating_torque_nm", "modulating_duty_s4_percent", "starts_per_hour",
         "operating_time_60hz_s", "operating_time_50hz_s", "fla_60hz_a",
         "fla_50hz_a", "lra_60hz_a", "lra_50hz_a", "motor_power_w"]
SHARED = ["base_part_number", "shared_torque_in_lb", "shared_torque_nm",
          "shared_duty_s4_percent", "cycles_per_hour", "starts_per_hour",
          "operating_time_60hz_s", "operating_time_50hz_s", "fla_60hz_a",
          "fla_50hz_a", "lra_60hz_a", "lra_50hz_a", "motor_power_w"]


def layout(table, page, top, bottom, rows, centers, fields, power_groups, na_rows=0):
    return dict(id=table, page=page, top=top, bottom=bottom, rows=rows,
                centers=centers, fields=fields, power_groups=power_groups, na_rows=na_rows)


X1 = [190, 277, 322, 365, 406, 450, 493, 548, 603, 641, 674, 706, 738, 770, 803, 838]
X4 = [187, 272, 318, 360, 405, 450, 494, 546, 600, 639, 672, 705, 737, 770, 802, 838]
X3 = [205, 310, 380, 447, 518, 594, 670, 752, 817]
SINGLE_ON = ["base_part_number", "on_off_torque_in_lb", "on_off_torque_nm",
             "on_off_duty_s4_percent", "cycles_per_hour", "operating_time_unqualified_s",
             "fla_unqualified_a", "lra_unqualified_a", "motor_power_w"]
SINGLE_MOD = ["base_part_number", "modulating_torque_in_lb", "modulating_torque_nm",
              "modulating_duty_s4_percent", "starts_per_hour", "operating_time_unqualified_s",
              "fla_unqualified_a", "lra_unqualified_a", "motor_power_w"]
LAYOUTS = [
    layout("p1_t1", 1, 330, 545, 11, X1, MIXED, [(0, 2), (2, 5), (5, 7), (7, 11)]),
    layout("p1_t2", 1, 657, 968, 16, X1, MIXED, [(0, 2), (2, 5), (5, 7), (7, 11), (11, 16)]),
    layout("p2_t1", 2, 325, 513, 11,
           [192, 278, 331, 383, 438, 497, 550, 596, 644, 696, 749, 801, 846],
           SHARED, [(4, 5), (5, 7), (7, 11)], na_rows=4),
    layout("p3_t1", 3, 293, 389, 5, X3, SINGLE_ON, [(0, 5)]),
    layout("p3_t2", 3, 475, 571, 5, X3, SINGLE_MOD, [(0, 5)]),
    layout("p4_t1", 4, 322, 519, 10, X4, MIXED, [(0, 2), (2, 5), (5, 7), (7, 10)]),
    layout("p4_t2", 4, 630, 826, 10, X4, MIXED, [(0, 2), (2, 5), (5, 6), (6, 10)]),
]


def record(box, text, confidence):
    xs, ys = zip(*box)
    return {"bbox": [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))],
            "text": str(text), "confidence": float(confidence)}


class Engine:
    def __init__(self, name, *, download=True):
        self.name = name
        start = time.perf_counter()
        CACHE.mkdir(parents=True, exist_ok=True)
        if name == "tesseract":
            import tesserocr
            tessdata = CACHE / "tessdata"
            model = tessdata / "eng.traineddata"
            if not model.is_file():
                raise FileNotFoundError("Run scripts/setup_ocr.py to download the pinned English model")
            if sha256(model) != "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2":
                raise ValueError("English Tesseract model hash mismatch")
            self.engine = tesserocr.PyTessBaseAPI(path=str(tessdata), lang="eng", psm=11,
                                                variables={"load_system_dawg": "0", "load_freq_dawg": "0"})
            self.version = tesserocr.tesseract_version()
        elif name == "easyocr":
            import torch
            import easyocr
            torch.set_num_threads(2)
            self.engine = easyocr.Reader(["en"], gpu=False, verbose=False,
                                        model_storage_directory=str(CACHE / "easyocr"),
                                        download_enabled=download)
            self.version = version("easyocr")
        elif name == "rapidocr":
            from rapidocr import RapidOCR, OCRVersion, ModelType, LangDet, LangRec
            self.engine = RapidOCR(params={"Global.model_root_dir": str(CACHE / "rapidocr"),
                                           "Global.use_cls": False,
                                           "Global.max_side_len": 3500,
                                           "Det.limit_side_len": 3500,
                                           "Det.limit_type": "max",
                                           "Det.ocr_version": OCRVersion.PPOCRV5, "Det.model_type": ModelType.MOBILE,
                                           "Rec.ocr_version": OCRVersion.PPOCRV5, "Rec.model_type": ModelType.MOBILE,
                                           "Det.lang_type": LangDet.CH, "Rec.lang_type": LangRec.EN,
                                           "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                                           "EngineConfig.onnxruntime.inter_op_num_threads": 2})
            self.version = version("rapidocr")
        else:
            raise ValueError(f"Unknown OCR engine: {name}")
        self.load_seconds = time.perf_counter() - start

    def read(self, image_path):
        if self.name == "tesseract":
            from tesserocr import RIL
            self.engine.SetImageFile(str(image_path))
            self.engine.Recognize()
            iterator = self.engine.GetIterator()
            result = []
            if iterator:
                while True:
                    text = iterator.GetUTF8Text(RIL.WORD)
                    box = iterator.BoundingBox(RIL.WORD)
                    if text and box:
                        x0, y0, x1, y1 = box
                        result.append(record([(x0, y0), (x1, y1)], text.strip(),
                                             iterator.Confidence(RIL.WORD) / 100))
                    if not iterator.Next(RIL.WORD):
                        break
            return result
        if self.name == "easyocr":
            return [record(b, t, c) for b, t, c in self.engine.readtext(
                str(image_path), detail=1, paragraph=False, batch_size=8, workers=0,
                canvas_size=3500, mag_ratio=1.0)]
        result = self.engine(str(image_path))
        if result.txts is None:
            return []
        return [record(b, t, c) for b, t, c in zip(result.boxes, result.txts, result.scores)]


def tokens_in(tokens, bbox):
    x0, y0, x1, y1 = bbox
    selected = [t for t in tokens if x0 <= (t["bbox"][0] + t["bbox"][2]) / 2 < x1
                and y0 <= (t["bbox"][1] + t["bbox"][3]) / 2 < y1]
    return sorted(selected, key=lambda t: (t["bbox"][1], t["bbox"][0]))


def reconstruct(pages, dpi):
    """Geometry only. No filling from reference, fuzzy code repair or numeric guesses."""
    scale = dpi / 120
    cells = []
    for table in LAYOUTS:
        centers = table["centers"]
        bounds = [135 if table["page"] != 4 else 129]
        bounds += [(a + b) / 2 for a, b in zip(centers, centers[1:])]
        bounds += [866]
        step = (table["bottom"] - table["top"]) / table["rows"]
        for row in range(table["rows"]):
            for col, field in enumerate(table["fields"]):
                first, last = row, row + 1
                if field == "motor_power_w":
                    first, last = next(((a, b) for a, b in table["power_groups"]
                                        if a <= row < b), (row, row + 1))
                bbox = [bounds[col] * scale, (table["top"] + first * step) * scale,
                        bounds[col + 1] * scale, (table["top"] + last * step) * scale]
                chosen = tokens_in(pages[table["page"]], bbox)
                # The printed N/A is one merged status cell, not a number in the
                # numeric column beneath its geometric center. Preserve it below.
                if row < table["na_rows"] and field != "base_part_number":
                    chosen = [t for t in chosen if normalize(t["text"], "data_status") != "source_NA"]
                cells.append(dict(source_table=table["id"], source_page=table["page"],
                                  source_row=row + 1, field=field, bbox=bbox,
                                  raw_text=" ".join(t["text"] for t in chosen),
                                  merged_span=[first + 1, last] if last - first > 1 else None))
        if table["na_rows"]:
            bbox = [bounds[1] * scale, table["top"] * scale, bounds[-1] * scale,
                    (table["top"] + table["na_rows"] * step) * scale]
            raw = " ".join(t["text"] for t in tokens_in(pages[table["page"]], bbox))
            for row in range(table["na_rows"]):
                cells.append(dict(source_table=table["id"], source_page=table["page"],
                                  source_row=row + 1, field="data_status", bbox=bbox,
                                  raw_text=raw, merged_span=[1, table["na_rows"]]))
    return cells


def normalize(text, field):
    """Formatting normalization only; O/0 and I/1 are deliberately NOT repaired."""
    if text is None:
        return None
    value = re.sub(r"\s+", "", str(text)).upper()
    if not value:
        return None
    if field == "base_part_number":
        return value.rstrip("*")
    if field == "data_status":
        return "source_NA" if value in {"N/A", "SOURCE_NA"} else value
    value = value.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", value):
        return value
    from decimal import Decimal
    return str(Decimal(value).normalize())


def run_engine(name, out, pdf=PDF, dpi=300, download=True):
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"Evidence already exists: {out}")
    if not 120 <= dpi <= 600:
        raise ValueError("dpi must be between 120 and 600")
    if sha256(pdf) != CATALOG_SHA256:
        raise ValueError("Fixed layout is only evaluated for the original catalog SHA-256")
    with pymupdf.open(pdf) as doc:
        if len(doc) != 4:
            raise ValueError("The fixed catalog layout requires exactly four pages")
    out.mkdir(parents=True)
    manifest = dict(engine=name, source_sha256=sha256(pdf), dpi=dpi,
                    created_utc=datetime.now(timezone.utc).isoformat(),
                    external_api_calls=0, validated_table_data=False,
                    status="started", layout="fixed-series76-v1", pages=[])
    manifest["code_sha256"] = sha256(__file__)
    manifest["settings"] = {
        "tesseract": {"language": "eng", "psm": 11, "system_dawg": False, "freq_dawg": False},
        "easyocr": {"language": "en", "gpu": False, "canvas_size": 3500,
                    "mag_ratio": 1.0, "batch_size": 8, "workers": 0, "torch_threads": 2},
        "rapidocr": {"recognition_language": "en", "detector_language": "ch/multilingual",
                     "model": "PP-OCRv5 mobile (English recognizer)", "max_side_len": 3500,
                     "det_limit_side_len": 3500, "det_limit_type": "max", "onnx_threads": 2,
                     "orientation_classifier": False, "orientation_reason": "all catalog pages are upright"},
    }[name]
    packages = {"tesseract": ("tesserocr",), "easyocr": ("easyocr", "torch"),
                "rapidocr": ("rapidocr", "onnxruntime")}[name]
    manifest["packages"] = {p: version(p) for p in ("PyMuPDF", *packages)}
    write_json(out / "manifest.json", manifest)
    try:
        engine = Engine(name, download=download)
        manifest.update(engine_version=engine.version, load_seconds=engine.load_seconds)
        pages = {}
        with pymupdf.open(pdf) as doc:
            for index, page in enumerate(doc, 1):
                png = out / f"page{index}.png"
                page.get_pixmap(dpi=dpi, alpha=False).save(png)
                start = time.perf_counter()
                pages[index] = engine.read(png)
                elapsed = time.perf_counter() - start
                write_json(out / f"page{index}.json", pages[index])
                (out / f"page{index}.txt").write_text(
                    "\n".join(t["text"] for t in pages[index]), encoding="utf-8")
                manifest["pages"].append(dict(page=index, seconds=elapsed, tokens=len(pages[index])))
                write_json(out / "manifest.json", manifest)
                print(f"{name} page {index}: {elapsed:.1f}s, {len(pages[index])} tokens", flush=True)
        write_json(out / "cells.json", reconstruct(pages, dpi))
        manifest["status"] = "ocr_completed_unvalidated"
        rapid_models = {"ch_PP-OCRv5_det_mobile.onnx", "en_PP-OCRv5_rec_mobile.onnx"}
        manifest["model_files"] = [dict(path=str(p.relative_to(ROOT)), sha256=sha256(p))
                                   for p in CACHE.rglob("*") if p.is_file() and
                                   p.suffix in {".onnx", ".pth", ".traineddata"} and
                                   ((name == "tesseract" and p.parent.name == "tessdata") or
                                    (name == "easyocr" and name in p.parts) or
                                    (name == "rapidocr" and p.name in rapid_models))]
    except Exception as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json(out / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["tesseract", "easyocr", "rapidocr"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, default=PDF)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if sha256(args.pdf) != config["source_sha256"]:
            parser.error("PDF hash differs from the evaluated catalog; review the layout first")
        args.engine, args.dpi = config["engine"], config["dpi"]
    if not args.engine:
        parser.error("Provide --engine or --config")
    run_engine(args.engine, args.out, args.pdf, args.dpi)


if __name__ == "__main__":
    main()
