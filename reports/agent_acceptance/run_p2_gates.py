"""Offline P2 oracle with the existing no-.env/no-provider test wrapper."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
out = root / 'reports/agent_acceptance/p2'
out.mkdir(parents=True, exist_ok=True)
command = [sys.executable, 'reports/agent_acceptance/run_t12_no_env.py',
           '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_p2_oracle.py', '-v']
with (out / 'oracle_final.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in ('backend/conversation', 'config', 'tests')
            for p in (root / directory).rglob('*') if p.suffix in ('.py', '.json') and '__pycache__' not in str(p)}
(out / 'oracle_final.json').write_text(json.dumps(dict(exit=result.returncode,
    scenarios=len(json.loads((root / 'config/agent_acceptance_cases_p2.json').read_text(encoding='utf-8'))['scenarios']),
    provider_inference=False, manifest=manifest), indent=2) + '\n', encoding='utf-8')
print('P2 oracle exit:', result.returncode)
raise SystemExit(result.returncode)
