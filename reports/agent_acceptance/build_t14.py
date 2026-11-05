import copy
import json
from pathlib import Path

S = []
def search(**kw): return ['search_actuators', kw]
def lookup(codes, **kw): return ['get_actuator', dict(part_numbers=codes, **kw)]
def state(f, **kw): return dict(state=dict(filters=f, questions_absent=list(f), **kw))
def turn(q, d, e): return dict(query=q, scripted_decision=d, expect=dict(contract_v6=True, t14_oracle=e))
def add(name, variants, d, e, before=()):
    for i,q in enumerate(variants):
        S.append(dict(id=f'T14_{name}_{i+1}', t14_class=name, turns=copy.deepcopy(list(before))+[turn(q,d,e)]))

base=dict(enclosure='weatherproof', supply_voltage_v=110, service='on_off', min_torque_nm=80)
seed=turn('Show weatherproof 110 V on/off actuators delivering at least 80 Nm.',search(**base),state(base))
pair=['761A00-11300000/A','762A00-11300000/A']
comp=turn('Compare '+ ' and '.join(pair)+'.',lookup(pair),{})
priority=dict(metric='operating_time',direction='lowest',frequency_hz=60)
rank=dict(column='operating_time_60hz_s',direction='lowest',label='fastest|lowest operating time')
add('search_priority',['Use minimum travel duration at 60 Hz as the primary selection criterion.','La prioridad es el menor tiempo de recorrido a 60 Hz.'],search(refine=True,priority=priority),dict(**state(dict(base,frequency_hz=60)),ranking=rank),[seed])
add('shown_priority',['Select from those two by minimum travel duration at 60 Hz.','Of the compared units, choose the one completing movement sooner at 60 Hz.'],search(refine=True,intent='pick',priority=priority),dict(pick=True,ranking=dict(rank,among=pair)),[comp])
add('torque_priority',['Choose from that pair for greater output torque in on/off service.','De esos dos elige el que entrega más par para abrir y cerrar.'],search(refine=True,intent='pick',service='on_off',priority=dict(metric='torque',direction='highest')),dict(pick=True,ranking=dict(column='on_off_torque_nm',direction='highest',label='most torque|highest torque',among=pair),forbidden_text=['delivery times']),[comp])
for name,item,qs in [('warranty','warranty',['Report the torque of 761A00-11300000/A and its warranty coverage.','Alongside torque for 761A00-11300000/A, specify the binding guarantee.']),('mounting','bolt pattern',['Give the 60 Hz travel time for 761A00-11300000/A plus the bracket hole pattern.','For 761A00-11300000/A provide operating time at 60 Hz and the drilling layout.'])]:
    field='torque' if name=='warranty' else 'operating_time'
    add(name,qs,lookup([pair[0]],focus=[field],unsupported_requests=[item]),dict(required_text=['The catalogue does not publish '+item],state=dict(published=True)))
add('voltage_hyphen',['Find weatherproof on/off units on 110-volt power with minimum 100 Nm.','Select outdoor open/close units needing 100 Nm from a 110-volt source.'],search(**dict(base,min_torque_nm=100)),state(dict(base,min_torque_nm=100),nonempty=True))
add('keep_voltage',['Do not alter the voltage or service; leave those requirements intact.','Conserva la tensión y el servicio que indiqué.'],search(refine=True,keep=['supply_voltage_v','service'],remove=['supply_voltage_v']),state(base,nonempty=True),[seed])
add('keep_quantity',['Leave my torque floor in place without asking me to confirm it again.','Mantén el mínimo de par ya indicado.'],search(refine=True,min_torque_nm=80,keep=['min_torque_nm']),dict(**state(base,nonempty=True),forbidden_text=['Please confirm minimum torque']),[seed])
impossible=dict(supply_voltage_v=24,service='modulating',min_torque_nm=5000)
imp=turn('Find 24 V modulating units with a minimum of 5000 Nm.',search(**impossible),state(impossible))
add('keep_impossible',['Do not weaken that torque limit; is there a matching unit?','The torque floor remains mandatory; reconsider availability under that requirement.'],search(refine=True,keep=['min_torque_nm'],remove=['min_torque_nm']),dict(**state(impossible),required_text=['No actuator']),[imp])
dc=dict(supply_voltage_v=24,supply_current='DC',dc_only=True,service='modulating',min_torque_nm=130)
dcseed=turn('Find 24 V DC-only modulating units with at least 130 Nm.',search(**dc),state(dc))
add('keep_dc_exclusion',['Units labelled AC/DC must stay excluded.','Continue to exclude dual AC/DC ratings.'],search(refine=True,keep=['dc_only','supply_current']),dict(**state(dc,nonempty=True),dc_only=True),[dcseed])
add('spanish_service',['Necesito 24 V exclusivamente de corriente continua para regulación, mínimo 130 Nm.','Para regular caudal busco 24 V solamente continua con al menos 130 Nm.'],search(**dc,assumptions=[dict(field='service',user_phrase='regulación')]),state(dc,nonempty=True))
add('contradiction',['I require DC-only at 24 V and also acceptance of alternating current.','Only DC ratings are acceptable, but the actuator must also run on AC.'],['ask_clarification',dict(field='supply')],dict(clarify=True))
add('capabilities',['What assistance can you provide when selecting this product range?','How can you support my Series 76 selection?'],['ask_clarification',dict(field='requirements')],dict(required_text=['supply|voltage','torque']))
add('na_explanation',['Please explain what N/A means for this missing value.','Explícame N/A sin completar el dato ausente.'],['ask_clarification',dict(field='term_not_in_summary',topic='source_na')],dict(required_text=['N/A','not published|not available|source']),[turn('Torque of 762A00-11330C00/A?',lookup(['762A00-11330C00/A'],focus=['torque']),dict(required_text=['N/A']))])
add('single_reference',['Also tell me its opening torque.','What opening torque does that same unit provide?'],lookup([],reference_kind='focused',focus=['torque']),dict(state=dict(published=True)),[turn('Show 761Y30-11380000/A.',lookup(['761Y30-11380000/A']),{})])
add('safe_site',['This water installation is away from all flammable substances, 220 V, open/close at 100 Nm.','Nonflammable indoor water service, 220 V, on/off, at least 100 Nm.'],search(enclosure='weatherproof',supply_voltage_v=220,service='on_off',min_torque_nm=100),state(dict(supply_voltage_v=220,service='on_off',min_torque_nm=100),hazard_clear=True))
add('site_question',['For a nonflammable workshop, is explosionproof required?','Does a general area without flammable materials need explosionproof?'],['ask_clarification',dict(field='requirements',topic='enclosure_guidance')],dict(required_text=['Weatherproof','Explosionproof','confirm|classification']))
add('supply_overview',['Summarize the electrical supply options briefly.','Give an overview of the available power supplies.'],['ask_clarification',dict(field='requirements',topic='supply_overview')],dict(required_text=['24','110','220','AC','DC']))
add('compound_overview',['List the published supply voltages together with enclosure categories.','Summarize enclosure choices and supply voltages in this catalogue.'],['ask_clarification',dict(field='requirements',topic='catalogue_overview')],dict(required_text=['24','110','220','Weatherproof','Explosionproof']))
add('scoped_service_overview',['At 24 V, compare the service options for DC-only versus AC/DC ratings.','For 24 V supplies, which services go with DC-only and with AC/DC?'],['ask_clarification',dict(field='requirements',topic='supply_services')],dict(required_text=['DC','AC/DC','Modulating','On/Off']))
add('retain_site_refinement',['Reevaluate the selection, retaining voltage, service and torque.','Keep those electrical and torque requirements when reviewing the list again.'],search(refine=True,keep=['supply_voltage_v','service','min_torque_nm']),state(base,nonempty=True),[seed])
for scenario in S:
    if scenario['id'] == 'T14_spanish_service_2':
        scenario['turns'][0]['scripted_decision'][1]['assumptions'][0]['user_phrase'] = 'regular caudal'
Path('config/agent_acceptance_cases_t14.json').write_text(json.dumps(dict(version='t14-oracle',cohort='t14',scenarios=S),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
Path('config/agent_acceptance_t14.json').write_text(json.dumps(dict(purpose='Offline Plan B ideal decisions; diagnostic paraphrases, not held-out.',provider='scripted',model='IdealModel',inference_allowed=False),indent=2)+'\n',encoding='utf-8')
print(len(S))
