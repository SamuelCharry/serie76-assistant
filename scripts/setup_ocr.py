"""Download the English Tesseract model to project cache with hash verification."""
from pathlib import Path
import hashlib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/eng.traineddata"
EXPECTED_SHA256 = "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"


def main():
    target = ROOT / ".cache/ocr/tessdata/eng.traineddata"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temp = target.with_suffix(".download")
        with urllib.request.urlopen(URL, timeout=120) as response:
            temp.write_bytes(response.read())
        if hashlib.sha256(temp.read_bytes()).hexdigest() != EXPECTED_SHA256:
            raise ValueError("Downloaded Tesseract model failed SHA-256 verification")
        temp.replace(target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Cached Tesseract model failed SHA-256 verification")
    print(f"eng.traineddata sha256={hashlib.sha256(target.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
