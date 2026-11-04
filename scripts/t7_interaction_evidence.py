"""Collect real HTTP/SQL T7 interaction payloads with a scripted model and rollback."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.agent_acceptance import scenario_environment, IdealModel
from backend.auth.api import require_user
from fastapi.testclient import TestClient


def main():
    output = {}
    with scenario_environment() as (app, connection, user):
        app.dependency_overrides[require_user] = lambda: {'id': user, 'name': 'Samuel Charry'}
        client = TestClient(app)
        with patch('backend.conversation.agent.create_model_client', return_value=IdealModel(('search_actuators', {
            'min_torque_nm': {'value':70,'op':'gte'}, 'max_fla_a':{'value':1.5,'op':'lt'}}))):
            first = client.post('/api/conversation', json={'query':'At least 70 Nm and FLA below 1.5 A'})
            assert first.status_code == 200
            output['two_questions'] = first.json()
        session = first.json()['session_id']
        with patch('backend.conversation.agent.reserve_agent_call', side_effect=AssertionError('unexpected model call')):
            for name, body in [
                ('answers_submit', {'query':'On/Off · 60 Hz', 'answers':{'service':'on_off','frequency_hz':'60'}}),
                ('remove_filters', {'query':'Remove torque', 'remove_filters':['min_torque_nm']}),
            ]:
                response = client.post('/api/conversation', json={'session_id':session, **body})
                assert response.status_code == 200
                output[name] = response.json()
            hello = client.post('/api/conversation', json={'query':'¡Hola!'})
            assert hello.status_code == 200
            output['greeting'] = hello.json()
        for name, codes in [('compare_two',['761A00-11300000/A','761B00-11300000/A']),
                            ('compare_three',['761A00-11300000/A','761B00-11300000/A','762A00-11300000/A'])]:
            with patch('backend.conversation.agent.create_model_client', return_value=IdealModel(('get_actuator',{'part_numbers':codes}))):
                response = client.post('/api/conversation', json={'query':'Compare ' + ' vs '.join(codes)})
                assert response.status_code == 200
                output[name] = response.json()
    (ROOT/'reports/submission/T7-interactions.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'http_cases':len(output), 'status':'passed', 'model_inference':False}))


if __name__ == '__main__':
    main()
