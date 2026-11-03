"""Render one PDF page and optionally run local Tesseract. No API calls.

Produces raw OCR evidence, not validated actuator rows or a database import.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "data/raw/series_76_electric_data.pdf")
    parser.add_argument("--page", type=int, default=1, help="1-based page number")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, choices=[3, 4, 6, 11, 12], default=3)
    parser.add_argument("--out", type=Path, required=True, help="New experiment directory; existing evidence is never overwritten")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--tesseract-cmd", default=os.environ.get("TESSERACT_CMD") or "tesseract")
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")
    if not 72 <= args.dpi <= 600:
        parser.error("dpi must be between 72 and 600")
    if args.out.exists():
        parser.error("Output directory already exists. Choose a new --out to preserve evidence.")
    executable = None
    if not args.render_only:
        executable = shutil.which(args.tesseract_cmd)
        if executable is None:
            parser.error("Tesseract is not installed/on PATH. Use Docker OCR, --tesseract-cmd, or --render-only.")
    with pymupdf.open(args.pdf) as doc:
        if not 1 <= args.page <= len(doc):
            parser.error(f"page must be between 1 and {len(doc)}")
        args.out.mkdir(parents=True)
        png = args.out / "page.png"
        doc[args.page - 1].get_pixmap(dpi=args.dpi, alpha=False).save(png)
    manifest = {
        "source_file": args.pdf.name,
        "source_sha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
        "page": args.page, "dpi": args.dpi, "psm": args.psm,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pymupdf_version": pymupdf.VersionBind,
        "status": "rendered_only", "validated_table_data": False,
        "external_api_calls": 0,
    }
    if executable:
        try:
            manifest["tesseract_version"] = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True, timeout=15).stdout.splitlines()[0]
            result = subprocess.run([executable, str(png), str(args.out / "ocr"), "-l", "eng", "--psm", str(args.psm), "txt", "tsv"], capture_output=True, text=True, check=True, timeout=180)
            (args.out / "engine.log").write_text(result.stderr, encoding="utf-8")
            manifest["status"] = "ocr_completed_unvalidated"
        except (subprocess.SubprocessError, OSError) as error:
            manifest.update(status="ocr_failed", error=str(error))
            (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"OCR failed; rendered page and manifest retained in {args.out}", file=sys.stderr)
            return 1
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{manifest['status']}: {args.out.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
