"""Execute both OCR notebooks using the isolated, registered project kernel."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse", type=Path, help="Explicitly reuse a completed three-engine run")
    args = parser.parse_args()
    subprocess.run([sys.executable, "-m", "ipykernel", "install", "--sys-prefix",
                    "--name", "serie76-ocr", "--display-name", "Serie76 OCR (Python 3.12)"], check=True)
    if args.reuse:
        os.environ["SERIE76_BENCHMARK_DIR"] = str(args.reuse.resolve())
    else:
        os.environ.pop("SERIE76_BENCHMARK_DIR", None)
    for name in ("01_comparar_ocr.ipynb", "02_exploracion_ydata.ipynb"):
        path = ROOT / "notebooks" / name
        notebook = nbformat.read(path, as_version=4)
        print(f"Executing {name}", flush=True)
        try:
            NotebookClient(notebook, timeout=1800, kernel_name="serie76-ocr",
                           resources={"metadata": {"path": str(ROOT)}}).execute()
        finally:
            nbformat.write(notebook, path)
        print(f"Completed {name}", flush=True)


if __name__ == "__main__":
    main()
