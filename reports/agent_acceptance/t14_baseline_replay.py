"""Run the original recorded decisions on archived e90c397 production code."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

root=Path.cwd()
target=Path(r'<local>\AppData\Roaming\orca\chat-scratch\97d6b63f2a41ae2054d3f6922c392659\t14_baseline')
target.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','e90c397']))) as archive:
    archive.extractall(target,filter='data')
# Only the evaluation adapter and oracle are current; backend is the original commit.
for rel in ['scripts/agent_acceptance.py','scripts/t14_oracle.py','reports/agent_acceptance/run_t12_no_env.py',
            'reports/agent_acceptance/t14_oracle_pre_fix/flash_replay_cases.json','config/agent_acceptance_t14.json']:
    dest=target/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/rel,dest)
out=root/'reports/agent_acceptance/t14_oracle_pre_fix'
with (out/'replay.log').open('w',encoding='utf-8') as log:
    result=subprocess.run([sys.executable,str(target/'reports/agent_acceptance/run_t12_no_env.py'),
        'scripts/agent_acceptance.py','selfcheck','--cases','reports/agent_acceptance/t14_oracle_pre_fix/flash_replay_cases.json',
        '--config','config/agent_acceptance_t14.json','--evidence',str(out/'replay.json')],cwd=target,stdout=log,stderr=subprocess.STDOUT)
(out/'replay.exit').write_text(str(result.returncode))
print('Baseline replay process exit',result.returncode)
raise SystemExit(result.returncode)
