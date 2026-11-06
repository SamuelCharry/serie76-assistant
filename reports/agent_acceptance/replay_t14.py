"""Recover original v13 decisions read-only by message ID; never invoke a provider."""
import json
from pathlib import Path
from backend.catalog.db import connect

scratch = Path(r'<local>\AppData\Roaming\orca\chat-scratch\97d6b63f2a41ae2054d3f6922c392659')
source = json.loads((scratch/'behavior/out_v13or_google_gemini-3.6-flash/results.json').read_text(encoding='utf-8'))
out = Path('reports/agent_acceptance/t14_oracle_pre_fix')
scenarios, traces = [], {}
with connect() as connection, connection.transaction(force_rollback=True):
    connection.execute('SET TRANSACTION READ ONLY')
    for scenario in source['results']:
        turns = []
        traces[scenario['id']] = []
        for index, turn in enumerate(scenario['turns']):
            stored = connection.execute('SELECT tool_calls FROM series76.messages WHERE id=%s',
                                        (turn['response']['message_id'],)).fetchone()
            if not stored or not stored['tool_calls']:
                raise RuntimeError('Missing recorded trace: ' + scenario['id'])
            trace = stored['tool_calls'][0]
            traces[scenario['id']].append(trace)
            calls = trace.get('model_calls') or []
            if calls:
                decision = [calls[0]['name'], calls[0]['args']]
            elif trace.get('model', {}).get('decision_calls'):
                decision = [trace['name'], trace['raw_parameters']]
            else:
                # Deterministic turns had no model decision. If the new routing
                # invokes this sentinel, mark the replay unsupported, never invent
                # a decision that Flash did not actually make.
                decision = ['ask_clarification', {'field': 'unsupported'}]
            expect = dict(contract_v6=True)
            if scenario['id'] == 'L2-08':
                expect['t14_oracle'] = dict(state=dict(filters=dict(supply_voltage_v=110),questions_absent=['supply_voltage_v']))
            if scenario['id'] == 'L4-03':
                expect['t14_oracle'] = dict(state=dict(filters=dict(supply_voltage_v=220,service='modulating')))
            if scenario['id'] == 'L7-04':
                expect['t14_oracle'] = dict(state=dict(filters=dict(min_torque_nm=5000)))
            if scenario['id'] == 'L6-03':
                expect['t14_oracle'] = dict(required_text=[r'(?:not|unavailable)[^.\n]*(?:bolt|mounting|drill)'])
            if scenario['id'] == 'L6-04':
                expect['t14_oracle'] = dict(required_text=[r'(?:not|unavailable)[^.\n]*warranty'])
            checks = {
                ('L1-03',1): dict(state=dict(filters=dict(supply_current='DC',dc_only=True)),dc_only=True),
                ('L2-02',0): dict(required_text=['look up|find|compare|supply|voltage']),
                ('L2-04',1): dict(state=dict(hazard_clear=True)),
                ('L2-09',0): dict(required_text=['Weatherproof','confirm|classification|general area']),
                ('L3-02',1): dict(state=dict(published=True)),
                ('L3-03',1): dict(pick=True,required_text=['fastest|lowest operating time|shortest']),
                ('L3-04',0): dict(required_text=['24','110','220']),
                ('L4-01',1): dict(forbidden_text=['Please confirm minimum torque']),
                ('L4-01',2): dict(forbidden_text=['Please confirm minimum torque']),
                ('L5-02',0): dict(state=dict(filters=dict(service='modulating',dc_only=True))),
                ('L5-03',1): dict(required_text=['761Y30-11380000/A'],forbidden_text=['delivery times']),
                ('L5-05',1): dict(required_text=['N/A','source|not available|not published']),
                ('L7-01',3): dict(pick=True,required_text=['fastest|shortest|lowest operating time','761A00-11300000/A']),
                ('L7-02',1): dict(required_text=['Ranked by fastest|Ranked by lowest operating time']),
                ('L7-03',2): dict(pick=True,ranking=dict(column='on_off_torque_nm',direction='highest',
                    label='most torque|highest torque',among=['761Y30-11380000/A','762X30-11380000/A'])),
                ('L7-07',0): dict(clarify=True),
                ('L7-08',0): dict(required_text=['Weatherproof','Explosionproof','24','110','220']),
                ('L7-08',1): dict(required_text=['DC','AC/DC','Modulating','On/Off']),
                ('L7-09',2): dict(state=dict(filters=dict(enclosure='explosionproof',supply_voltage_v=110,
                    service='on_off',min_torque_nm=100),nonempty=True)),
            }
            if (scenario['id'],index) in checks:
                expect['t14_oracle'] = checks[(scenario['id'],index)]
            turns.append(dict(query=turn['turn'],scripted_decision=decision,expect=expect,
                              original_message_id=turn['response']['message_id'],
                              original_decision_present=bool(calls or trace.get('model', {}).get('decision_calls'))))
        scenarios.append(dict(id='T14_REPLAY_'+scenario['id'],t14_class='recorded_v13',turns=turns))
(out/'flash_decisions.json').write_text(json.dumps(traces,indent=2,default=str)+'\n',encoding='utf-8')
(out/'flash_replay_cases.json').write_text(json.dumps(dict(scenarios=scenarios),indent=2)+'\n',encoding='utf-8')
print('Recovered', len(scenarios), 'conversations by PostgreSQL message IDs; no inference.')
