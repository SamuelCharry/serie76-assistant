# Local Windows experiment environment. No OpenRouter key is read or required.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv-ocr/Scripts/python.exe')) {
        python -m venv .venv-ocr
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the OCR environment' }
    }
    & ./.venv-ocr/Scripts/python.exe -m pip install -r requirements-ocr.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'OCR dependency installation failed' }
    & ./.venv-ocr/Scripts/python.exe scripts/setup_ocr.py
    if ($LASTEXITCODE -ne 0) { throw 'English model setup failed' }
    & ./.venv-ocr/Scripts/python.exe -m ipykernel install --sys-prefix --name serie76-ocr --display-name 'Serie76 OCR (Python 3.12)'
    if ($LASTEXITCODE -ne 0) { throw 'Kernel registration failed' }
    & ./.venv-ocr/Scripts/python.exe -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'OCR dependency check failed' }
} finally {
    Pop-Location
}
