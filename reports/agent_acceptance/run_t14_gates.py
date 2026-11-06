"""Sequential offline gates, exact process exits and a code digest manifest."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path.cwd()
out=root/os.environ.get('SERIES76_GATE_OUTPUT', 'reports/agent_acceptance/t14_final')
out.mkdir(parents=True,exist_ok=True)
wrapper='reports/agent_acceptance/run_t12_no_env.py'
gates=[('unittest',['-m','unittest','discover','-s','tests'])]
for label in ('v7','t10','t12','t14'):
    gates.append((label,['scripts/agent_acceptance.py','selfcheck','--cases',f'config/agent_acceptance_cases_{label}.json',
                        '--config',f'config/agent_acceptance_{label}.json','--evidence',str(out/f'{label}.json')]))
gates += [('schema',['scripts/check_tool_schemas.py']),('public_text',['scripts/check_public_text.py']),
          ('ranking',['scripts/eval_ranking.py','--out',str(out/'ranking.json')]),
          ('replay',['scripts/agent_acceptance.py','selfcheck','--cases','reports/agent_acceptance/t14_oracle_pre_fix/flash_replay_cases.json',
                     '--config','config/agent_acceptance_t14.json','--evidence',str(out/'replay.json')])]
env=dict(os.environ,PYTHONPATH=str(root),PYTHONIOENCODING='utf-8',SERIES76_TEST_DB='1')
summary={}
for label,args in gates:
    with (out/f'{label}.log').open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,wrapper,*args],env=env,stdout=log,stderr=subprocess.STDOUT)
    summary[label]=result.returncode
    (out/f'{label}.exit').write_text(str(result.returncode))
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(label,result.returncode,flush=True)
manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('backend','scripts','tests','config')
          for p in Path(folder).rglob('*') if p.suffix in ('.py','.json') and '__pycache__' not in str(p)}
(out/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
raise SystemExit(any(code for label,code in summary.items() if label!='replay'))
