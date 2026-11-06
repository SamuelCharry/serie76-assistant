"""Read-only SQL audit of every saved v15 response against reviewed request scopes."""
import argparse
import hashlib
import json
from pathlib import Path
from backend.catalog.db import connect
from backend.catalog.repository import get_actuator
from backend.catalog.models import SearchFilters
from backend.conversation import integrity,shown_recommendation,policy
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=Path(r'<local>\AppData\Roaming\orca\chat-scratch\97d6b63f2a41ae2054d3f6922c392659'))
source=parser.parse_args().source/'behavior/out_v15_v1/results.json'
data=json.loads(source.read_text(encoding='utf-8'))
out=Path('reports/agent_acceptance/p1_f')
scopes=json.loads((out/'reviewed_scopes.json').read_text())
review=[];cards=0
with connect() as c,c.transaction(force_rollback=True):
 c.execute('SET TRANSACTION READ ONLY')
 for scenario in data['results']:
  for i,t in enumerate(scenario['turns'],1):
   r=t.get('response',{});mid=r.get('message_id')
   if not mid:continue
   scope=next(x for x in scopes[scenario['id']] if x['message_id']==mid)
   filters=SearchFilters.model_validate(scope['filters'])
   codes=set(policy.codes_in_text(r['answer']))|{p['base_part_number'] for p in r.get('products',[])}
   codes.update((r.get('comparison') or {}).get('models',[]))
   codes.update(p['part_number'] for p in (r.get('recommendation') or {}).get('items',[]))
   cards+=len(r.get('products',[]))
   failures={}
   for code in sorted(codes):
    row=get_actuator(c,code)
    if row and not integrity.satisfies(row,filters):failures[code]=shown_recommendation.failures(row,scope['filters'])[0]
   reviewed=dict(id=scenario['id'],turn=i,message_id=mid,query=t['turn'],filters=scope['filters'],codes=sorted(codes),failures=failures)
   reviewed['review_class']=scope['review_class']
   if 'scope_violation' in scope:reviewed['scope_violation']=scope['scope_violation']
   if failures:reviewed['answer']=r['answer'];print(scenario['id'],i,json.dumps(failures))
   review.append(reviewed)
summary=dict(conversations=len(data['results']),turns=len(review),product_cards=cards,code_occurrences=sum(len(t['codes']) for t in review),flagged_turns=sum(bool(t['failures']) for t in review),turns_reviewed=review)
summary['results_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
summary['review_note']='Scopes and classifications are an independent diagnostic reading of requests, not model-state ground truth; L7-01 uses the rendered On/Off scope, and selecting the reference itself also fails under Modulating service.'
(out/'scan.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print({k:v for k,v in summary.items() if k!='turns_reviewed'})
