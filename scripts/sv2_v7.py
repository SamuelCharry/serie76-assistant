"""Measure frozen v7 against authored full-state decisions, offline only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.agent_acceptance import run_scenario, IdealModel, IDEAL
from scripts.convert_sv2_cases import convert


def main():
    folder = ROOT / 'reports/agent_acceptance/sv2_v7'
    folder.mkdir(exist_ok=True)
    cases = json.loads((ROOT / 'config/agent_acceptance_cases_v7.json').read_text(encoding='utf8'))
    baseline_file = folder / 'v1_snapshots.json'
    if baseline_file.exists():
        baseline = json.loads(baseline_file.read_text(encoding='utf8'))
    else:
        baseline = {}
        os.environ['AGENT_STATE_MODE'] = 'v1'
        for i, scenario in enumerate(cases['scenarios']):
            baseline[scenario['id']] = run_scenario(scenario, lambda s, n: IdealModel(s['turns'][n].get('scripted_decision') or IDEAL[s['id']][n]))
            if i % 50 == 0:
                print('v1 snapshot', i, flush=True)
        baseline_file.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf8')
    converted = []
    for scenario in cases['scenarios']:
        source = deepcopy(scenario)
        for n, turn in enumerate(source['turns']):
            if not turn.get('scripted_decision') and source['id'] in IDEAL:
                turn['scripted_decision'] = IDEAL[source['id']][n]
        converted.append(convert(source, baseline[source['id']]))
    (folder / 'cases.json').write_text(json.dumps(dict(cases, scenarios=converted), ensure_ascii=False, indent=2), encoding='utf8')
    os.environ['AGENT_STATE_MODE'] = 'v2'
    results = []
    for i, scenario in enumerate(converted):
        result = run_scenario(scenario, lambda s, n: IdealModel(s['turns'][n]['scripted_decision']))
        results.append(dict(scenario=scenario['id'], **result))
        if i % 50 == 0:
            print('v2 replay', i, flush=True)
    failed = [r for r in results if r['status'] != 'passed']
    summary = dict(mode='scripted full-state oracle; no inference', scenarios=len(results),
                   passed=len(results) - len(failed), failed=len(failed),
                   baseline_passed=sum(r['status'] == 'passed' for r in baseline.values()))
    summary['target_95_percent_met'] = summary['passed'] / summary['scenarios'] >= 0.95
    summary['strict_selfcheck_exit'] = int(bool(failed))
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    (folder / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    differences = [dict(scenario=r['scenario'], status=r['status'], turns=[dict(query=t['query'],
                        failures=t['failures'], validation=t['trace']['validation']) for t in r['turns'] if not t['passed']]) for r in failed]
    (folder / 'differences.json').write_text(json.dumps(differences, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(summary), flush=True)
    return int(not summary['target_95_percent_met'])


if __name__ == '__main__':
    raise SystemExit(main())
