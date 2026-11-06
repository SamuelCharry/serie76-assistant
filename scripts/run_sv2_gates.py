"""Run the isolated, non-billable SV2 experiment and record exact exit codes.

Usage: python scripts/sv2_offline.py scripts/run_sv2_gates.py
Database: docker compose --env-file <empty-file> -p serie76-sv2 -f docker/compose.sv2.yml up -d --wait
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/agent_acceptance/sv2_final'


def main():
    if os.environ.get('PGPORT') != '55433' or os.environ.get('SERIES76_OFFLINE_DB_EXPLICIT') != '1':
        raise SystemExit('Use scripts/sv2_offline.py; the isolated database is mandatory.')
    OUT.mkdir(exist_ok=True)
    summary = dict(started_at=datetime.now(timezone.utc).isoformat(), gates={})
    stages = [
        ('v1_t14_gates', 'v1', ['reports/agent_acceptance/run_t14_gates.py']),
        ('v2_validators', 'v2', ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_state_v2*.py']),
        ('v2_oracle', 'v2', ['scripts/agent_acceptance.py', 'selfcheck', '--cases', 'config/agent_acceptance_cases_sv2.json',
                            '--config', 'config/agent_acceptance_t14.json', '--evidence', str(OUT / 'oracle.json')]),
        ('v2_schema', 'v2', ['scripts/check_tool_schemas.py']),
        ('v2_public_text', 'v2', ['scripts/check_public_text.py']),
        ('v2_ranking', 'v2', ['scripts/eval_ranking.py', '--out', str(OUT / 'ranking.json')]),
        ('v2_v7_target', 'v2', ['scripts/sv2_v7.py']),
    ]
    for label, mode, args in stages:
        env = dict(os.environ, AGENT_STATE_MODE=mode, SERIES76_GATE_OUTPUT='reports/agent_acceptance/sv2_v1')
        with (OUT / f'{label}.log').open('w', encoding='utf8') as log:
            result = subprocess.run([sys.executable, 'scripts/sv2_offline.py', *args], cwd=ROOT, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
        summary['gates'][label] = result.returncode
        (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
        print(label, result.returncode, flush=True)
    rank_path = OUT / 'ranking.json'
    if rank_path.exists():
        rank = json.loads(rank_path.read_text(encoding='utf8'))
        summary['ranking_target_met'] = rank['means']['3']['ndcg'] >= 0.965 and rank['means']['3']['compliance_returned'] == 1.0
    summary['completed_at'] = datetime.now(timezone.utc).isoformat()
    summary['mandatory_gates_passed'] = not any(code for label, code in summary['gates'].items() if label != 'v2_v7_target') and summary.get('ranking_target_met', False)
    summary['v7_target_met'] = summary['gates'].get('v2_v7_target') == 0
    paths = [p for folder in ('backend', 'scripts', 'tests', 'config') for p in (ROOT / folder).rglob('*')
             if p.suffix in ('.py', '.json') and '__pycache__' not in str(p)]
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT / 'source_manifest.json').write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding='utf8')
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    # A missed v7 target is visible as a nonzero experiment exit, never called green.
    return int(not summary['mandatory_gates_passed'] or not summary['v7_target_met'])


if __name__ == '__main__':
    raise SystemExit(main())
