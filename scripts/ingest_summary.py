"""series_76_summary.pdf -> glossary terms.json (definitions only, never catalogue numbers)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_ingest.summary import extract_terms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, nargs="?", default=ROOT / "data/raw/series_76_summary.pdf")
    parser.add_argument("--out", type=Path, default=ROOT / "data/extracted/series76_summary")
    args = parser.parse_args()
    result = extract_terms(args.pdf)
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "terms.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="ok", terms=len(result["terms"]), output=str(target),
                          document_sha256=result["document_sha256"])))


if __name__ == "__main__":
    main()
