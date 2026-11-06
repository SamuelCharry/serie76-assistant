"""Public round-nine conversations and recorded decisions; no provider calls."""
import json
from pathlib import Path
from unittest.mock import patch

from backend.conversation import embeddings
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Scripted


class RoundNineReplay(Base):
    def test_all_recorded_on_off_conversations(self):
        fixture = json.loads(Path('config/agent_replay_v9.json').read_text(encoding='utf-8'))
        self.assertEqual(len(fixture['runs']), 82)
        with patch('backend.conversation.agent.reserve_agent_call'), \
             patch.object(embeddings, 'embed_query', side_effect=AssertionError('offline replay')):
            for scenario in fixture['runs']:
                self.context, self.history = {}, []
                for index, turn in enumerate(scenario['turns']):
                    with self.subTest(mode=scenario['mode'], scenario=scenario['id'], turn=index):
                        concepts = turn['retrieval_concepts']
                        retrieval = embeddings.Retrieval(available=scenario['mode'] == 'on',
                            concepts=concepts, accepted=embeddings.classify(concepts))
                        calls = [(c['name'], c['args']) for c in turn['model_calls']]
                        with patch.object(embeddings, 'retrieve', return_value=retrieval), \
                             patch('backend.conversation.agent.create_model_client', return_value=Scripted(*calls)):
                            result = run_agent(self.connection, turn['query'], self.history, self.context)
                        self.assertTrue(result.answer)
                        self.context = result.context
                        self.history += [dict(role='user', content=turn['query']),
                                         dict(role='assistant', content=result.answer)]
                        self.check_repaired_behavior(scenario['id'], index, result)

    def check_repaired_behavior(self, case, index, result):
        filters = result.context.get('filters') or {}
        if case == 'Y3-02':
            self.assertNotIn('max_motor_power_w', filters)
            self.assertEqual(float(filters['supply_voltage_v']), 220)
        if case == 'Y4-04' and index == 1:
            self.assertEqual(result.recommendation['total'], 4)
        if case == 'Y4-01' and index == 1:
            self.assertEqual(filters['enclosure'], 'weatherproof')
        if case in ('Y2-02', 'Y2-04', 'Y5-02'):
            self.assertTrue(result.context.get('hazard_signal'))
            self.assertIn('enclosure', [q['id'] for q in result.interaction['questions']])
            self.assertTrue(all(item['part_number'][3] in 'XY' for item in result.recommendation['items']))
        if case in ('Y2-01', 'Y2-03'):
            self.assertEqual(filters['service'], 'on_off' if case == 'Y2-01' else 'modulating')
        if case == 'Y1-04' and index == 1:
            self.assertIn('difference 79 cycles/h', result.answer)
        if case == 'Z-IMPOSSIBLE-01' and index == 1:
            self.assertIn('relax', result.answer.lower())
        if case == 'Z-CORRECTION-01' and index == 1:
            self.assertIn('40%', result.answer)
            self.assertNotIn('torque', result.answer.lower())
        if case == 'Y6-02':
            self.assertIn("doesn't publish position feedback output", result.answer)
            self.assertEqual(result.answer.count('.'), 1)
