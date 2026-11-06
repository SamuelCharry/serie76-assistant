"""Run both requested gates on one source digest, without opening .env or provider calls."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd();out=root/'reports/agent_acceptance/p1_f';out.mkdir(exist_ok=True)
code="import os,json; print(json.dumps({k:os.environ[k] for k in ['PGDATABASE','PGUSER','PGPASSWORD']}))"
settings=json.loads(subprocess.check_output(['docker','exec','serie76-assistant-backend-1','python','-c',code],text=True))
env=dict(os.environ,**settings,PGHOST='127.0.0.1',PGPORT='5432',SERIES76_TEST_DB='1',SERIES76_SKIP_DOTENV='1',PYTHONIOENCODING='utf-8',PYTHONPATH=str(root),LANGSMITH_TRACING='false',EMBEDDINGS_ENABLED='false')
for key in ('DATABASE_URL','OPENROUTER_API_KEY','OPENAI_API_KEY','GOOGLE_API_KEY','EMBEDDING_API_KEY','LANGSMITH_API_KEY'):env.pop(key,None)
def digest():
 return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('backend','scripts','tests','config') for p in Path(folder).rglob('*') if p.suffix in ('.py','.json') and '__pycache__' not in str(p)}
before=digest();summary={}
(out/'gates.json').write_text('{}\n')
for label,args in [('t14_gates',['reports/agent_acceptance/run_t14_gates.py']),('unittest',['-m','unittest','discover','-s','tests'])]:
 with (out/(label+'.log')).open('w',encoding='utf-8') as log:
  proc=subprocess.run([sys.executable,*args],env=env,stdout=log,stderr=subprocess.STDOUT)
 summary[label]=proc.returncode
 (out/'gates.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(label,proc.returncode,flush=True)
 if proc.returncode:break
summary['same_source']=before==digest();(out/'gates.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'code_manifest.json').write_text(json.dumps(before,indent=2)+'\n')
raise SystemExit(not summary.get('same_source') or any(v for k,v in summary.items() if k!='same_source'))
