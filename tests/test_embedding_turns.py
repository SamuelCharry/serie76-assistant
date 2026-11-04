"""Scripted chat + semantic suggestions; no external inference."""
import os
from unittest.mock import patch

from backend.conversation import embeddings
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Scripted


class SemanticTurnTests(Base):
    def semantic_turn(self, query, accepted, args=None):
        retrieval = embeddings.Retrieval(concepts={c: .9 for c in accepted}, accepted=set(accepted), available=True)
        with patch.object(embeddings, 'retrieve', return_value=retrieval):
            return self.turn(query, ('search_actuators', args or {}))

    def test_new_hazard_phrasing_requires_confirmation_before_weatherproof(self):
        result = self.semantic_turn('actuator for an ethanol tank farm, 110 V', {'hazard'},
                                    {'supply_voltage_v': 110, 'enclosure': 'weatherproof'})
        self.assertTrue(result.context['hazard_signal'])
        self.assertEqual(result.interaction['questions'][0]['id'], 'enclosure')
        self.assertTrue(all(item['part_number'][3] in 'XY' for item in result.recommendation['items']))
        self.assertEqual(result.debug['retrieval']['concepts'], {'hazard': .9})

    def test_service_suggestion_retains_exact_numeric_bounds(self):
        result = self.semantic_turn('que abra y cierre, 110 V, at least 70 Nm', {'on_off'},
                                    {'supply_voltage_v': 110, 'min_torque_nm': 70})
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertIn('70', str(result.context['filters']['min_torque_nm']))

    def test_explicit_service_wins_over_semantic_suggestion(self):
        result = self.semantic_turn('on/off actuator, 110 V', {'modulating'}, {'service': 'modulating'})
        self.assertEqual(result.context['filters']['service'], 'on_off')

    def test_safe_area_applies_weatherproof(self):
        result = self.semantic_turn('ordinary location, 110 V', {'safe_area'})
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_code_negation_wins_over_hazard_suggestion(self):
        result = self.semantic_turn('not a hazardous area, 110 V', {'hazard'})
        self.assertFalse(result.context.get('hazard_signal'))
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_service_negation_prevents_suggestion(self):
        result = self.semantic_turn('not modulating, 110 V', {'modulating'})
        self.assertNotIn('service', result.context['filters'])

    def test_negation_does_not_erase_affirmative_service_in_another_clause(self):
        for query, service in [('not a hazardous area, on/off, 110 V', 'on_off'),
                               ('not modulating, just on/off, 110 V', 'on_off'),
                               ('modulating service, not on/off, 110 V', 'modulating')]:
            self.context, self.history = {}, []
            result = self.semantic_turn(query, {'on_off'})
            self.assertEqual(result.context['filters'].get('service'), service, query)

    def test_negated_flammable_word_cannot_force_hazard(self):
        result = self.semantic_turn('no flammable materials in this area, 110 V', {'hazard'})
        self.assertFalse(result.context.get('hazard_signal'))

    def test_fewshot_is_prompt_data_and_cannot_supply_numbers(self):
        retrieval = embeddings.Retrieval(examples=[dict(id=7, similarity=.93, text='plant 999 V',
            interpretation={'tool': 'search_actuators', 'args': {'supply_voltage_v': 999}})], available=True)
        chat = Scripted(('search_actuators', {'supply_voltage_v': 999}))
        with patch.object(embeddings, 'retrieve', return_value=retrieval):
            result = run_agent(self.connection, 'Help select for my process', [], {}, model=chat)
        self.assertIn('Similar requests', chat.seen[0].content)
        self.assertNotIn('supply_voltage_v', result.context.get('filters', {}))

    def test_deterministic_greeting_never_embeds(self):
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL='fake'):
            with patch.object(embeddings, 'embed_query', side_effect=AssertionError('no embedding on fast path')):
                result = run_agent(self.connection, 'hello', [], {})
        self.assertFalse(result.debug['llm_called'])
        self.assertEqual(result.debug['retrieval']['embedding_ms'], 0)

    def test_flag_off_and_failure_preserve_answer_and_context(self):
        query = 'outside actuator that opens and closes, 110 V'
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='false'):
            before = run_agent(self.connection, query, [], {}, model=Scripted(('search_actuators', {'supply_voltage_v': 110})))
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL='fake'):
            with patch.object(embeddings, 'embed_query', side_effect=TimeoutError):
                after = run_agent(self.connection, query, [], {}, model=Scripted(('search_actuators', {'supply_voltage_v': 110})))
        self.assertEqual(before.answer, after.answer)
        self.assertEqual(before.context, after.context)
