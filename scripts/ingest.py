"""PDF -> local OCR -> dynamic reconstruction/cleanup -> validation -> CSV/JSON."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_ingest.ocr import LocalOCR, atomic_json
from catalog_ingest.pipeline import Config, process_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs", nargs="+", type=Path, help="PDF files or directories (recursive)"
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/catalog-ocr")
    parser.add_argument("--models", type=Path, default=ROOT / ".cache/ocr/rapidocr")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=2000)
    parser.add_argument("--max-pixels", type=int, default=20_000_000)
    parser.add_argument("--no-images", action="store_true")
    args = parser.parse_args()

    def input_paths():
        for path in args.inputs:
            yield from path.rglob("*.pdf") if path.is_dir() else [path]

    if args.threads < 1:
        parser.error("threads must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    config = Config(
        dpi=args.dpi,
        max_pages=args.max_pages,
        max_pixels=args.max_pixels,
        keep_images=not args.no_images,
    )
    ocr = LocalOCR(args.cache, args.models, args.threads)
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    )
    runs = args.out / "runs"
    runs.mkdir(exist_ok=True)
    job_log = runs / f"{run_id}.jsonl"
    total = 0
    ready = 0
    try:
        with job_log.open("w", encoding="utf-8") as log:
            for path in input_paths():
                try:
                    folder, result = process_pdf(path, args.out, ocr, config)
                    job = dict(
                        input=str(path),
                        output=str(folder),
                        status=result["status"],
                        rows=result.get("rows", 0),
                        reused=result.get("reused", False),
                    )
                except Exception as error:
                    job = dict(
                        input=str(path),
                        status="failed",
                        error=f"{type(error).__name__}: {error}",
                    )
                total += 1
                ready += job["status"] == "ready"
                import json

                log.write(json.dumps(job, ensure_ascii=False) + "\n")
                log.flush()
                atomic_json(
                    args.out / "run_manifest.json",
                    dict(
                        run_id=run_id,
                        jobs_total=total,
                        jobs_ready=ready,
                        jobs_failed_or_review=total - ready,
                        job_log=str(job_log),
                        external_api_calls=0,
                    ),
                )
                print(job, flush=True)
    finally:
        ocr.close()
    if not total:
        parser.error("No PDF inputs found")
    return 0 if ready == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
