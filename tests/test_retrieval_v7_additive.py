"""v7 replay: actual dense SQL retrieval with fake vectors and scripted chat only."""
import json
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from psycopg.types.json import Jsonb
from backend.conversation import embeddings
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Scripted


class RetrievalReplayTests(Base):
    def test_dense_examples_preserve_off_filters_for_all_v7_turns(self):
        from scripts.agent_acceptance import IDEAL
        model = 'test-t9s2-' + uuid4().hex
        vector = [1.0] + [0.0]*767
        literal = embeddings.vector_literal(vector)
        # Conflicting example values must remain prompt examples, never filters.
        self.connection.execute('''INSERT INTO series76.example_bank
            (text,interpretation,source,model,dim,embedding) VALUES (%s,%s,'[]',%s,768,%s::vector)''',
            ('conflicting illustrative requirement, 24 V modulating XP',
             Jsonb(dict(tool='search_actuators', args=dict(supply_voltage_v=24,
                        service='modulating', enclosure='explosionproof'))), model, literal))
        cases = json.loads(Path('config/agent_acceptance_cases_v7.json').read_text(encoding='utf-8'))
        retrieved = 0
        with patch('backend.conversation.agent.reserve_agent_call'), \
             patch.object(embeddings, 'embed_query', return_value=vector) as embed, \
             patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL=model, EMBEDDING_EXCLUDE_SOURCES=''):
            for scenario in cases['scenarios']:
                states, histories = [{}, {}], [[], []]
                for index, turn in enumerate(scenario['turns']):
                    outputs = []
                    for mode in (0, 1):
                        with patch.dict(os.environ, EMBEDDINGS_ENABLED=str(bool(mode)).lower()), \
                             patch('backend.conversation.agent.create_model_client', side_effect=lambda:
                                   Scripted(tuple(turn.get('scripted_decision') or IDEAL[scenario['id']][index]))):
                            result = run_agent(self.connection, turn['query'], histories[mode], states[mode],
                                **{k: turn[k] for k in ('answers', 'remove_filters', 'action') if k in turn})
                        states[mode] = result.context
                        histories[mode] += [dict(role='user', content=turn['query']), dict(role='assistant', content=result.answer)]
                        outputs.append(result.context.get('filters', {}))
                        if mode and result.debug.get('retrieval', {}).get('examples'):
                            retrieved += 1
                    self.assertEqual({k: outputs[1].get(k) for k in outputs[0]}, outputs[0],
                                     (scenario['id'], index, turn['query']))
            self.assertGreater(embed.call_count, 0)
            self.assertGreater(retrieved, 0, 'The replay must actually exercise SQL retrieval')
