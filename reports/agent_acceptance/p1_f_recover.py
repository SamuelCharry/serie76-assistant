import json
from pathlib import Path
from backend.catalog.db import connect
src=Path(r'C:\Users\nrir\AppData\Roaming\orca\chat-scratch\97d6b63f2a41ae2054d3f6922c392659')
data=json.loads((src/'behavior/out_v15_v1/results.json').read_text(encoding='utf-8'))
out=Path('reports/agent_acceptance/p1_f');out.mkdir(exist_ok=True)
traces={}
with connect() as c,c.transaction(force_rollback=True):
 c.execute('SET TRANSACTION READ ONLY')
 for s in data['results']:
  traces[s['id']]=[]
  for i,t in enumerate(s['turns'],1):
   mid=t.get('response',{}).get('message_id')
   if not mid: continue
   tr=c.execute('SELECT tool_calls FROM series76.messages WHERE id=%s',(mid,)).fetchone()['tool_calls'][0]
   traces[s['id']].append(dict(turn=i,query=t['turn'],message_id=mid,trace=tr))
   if s['id'] in ('L1-01','L4-04'):
    print(s['id'],i,mid,t['turn']); print('ANSWER',t['response']['answer']); print(json.dumps({k:tr.get(k) for k in ['name','raw_parameters','parameters','model_calls','context_before','context_after','validation']},default=str))
(out/'recorded_traces.json').write_text(json.dumps(traces,indent=2,default=str)+'\n',encoding='utf-8')
print('recovered',sum(map(len,traces.values())))
