"""Scripted chat + semantic suggestions; no external inference."""
import os
import json
from pathlib import Path
from unittest.mock import patch

from backend.conversation import embeddings
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Scripted


class SemanticTurnTests(Base):
    def test_abstention_keeps_legacy_service_and_hazard_recognition(self):
        for phrase, expected in [('open and close', 'on_off'), ('mod', 'modulating'),
                                 ('que module', 'modulating'), ('abrir y cerrar', 'on_off'),
                                 ('regulating', 'modulating')]:
            with self.subTest(phrase=phrase):
                self.context, self.history = {}, []
                result = self.semantic_turn(phrase + ', 110 V', set())
                self.assertEqual(result.context['filters'].get('service'), expected)
        self.context, self.history = {}, []
        result = self.semantic_turn('wood dust, 110 V', set())
        self.assertTrue(result.context.get('hazard_signal'))

    def test_uncertain_classifier_does_not_preview_explosionproof_in_safe_context(self):
        for phrase in ['chlorine, open and close, 110 V', 'office actuator, 110 V',
                       'clean office basement, nothing flammable around, 220 V on/off',
                       'no flammable atmosphere, 110 V']:
            self.context, self.history = {}, []
            result = self.semantic_turn(phrase, set())
            self.assertNotEqual(result.context.get('proposed_enclosure'), 'explosionproof', phrase)
            self.assertFalse(result.context.get('hazard_signal'), phrase)

    def test_no_flammable_atmosphere_rejects_previous_hazard_preview(self):
        first = self.semantic_turn('ethanol tank farm, on/off, 110 V', {'hazard'})
        self.assertEqual(first.context.get('proposed_enclosure'), 'explosionproof')
        result = self.semantic_turn('no, no flammable atmosphere there', set(), {'refine': True})
        self.assertFalse(result.context.get('hazard_signal'))
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_v7_normalizer_suggestions_only_fill_unstated_fields(self):
        from backend.conversation import policy
        cases = json.loads(Path('config/agent_acceptance_cases_v7.json').read_text(encoding='utf-8'))
        for scenario in cases['scenarios']:
            for turn in scenario['turns']:
                query = turn.get('query', '')
                before, _ = policy.colloquial_requirements(query)
                for accepted in [set(), {'safe_area', 'modulating'}, {'hazard', 'on_off'}]:
                    after, _ = policy.colloquial_requirements(query, accepted)
                    self.assertEqual({k: after.get(k) for k in before}, before, (scenario['id'], query, accepted))

    def test_all_v7_agent_filters_survive_enabled_classifier_abstention(self):
        from scripts.agent_acceptance import IDEAL
        cases = json.loads(Path('config/agent_acceptance_cases_v7.json').read_text(encoding='utf-8'))
        with patch('backend.conversation.agent.reserve_agent_call'):
            for scenario in cases['scenarios']:
                states, histories = [{}, {}], [[], []]
                for index, turn in enumerate(scenario['turns']):
                    outputs = []
                    for mode in (0, 1):
                        with patch.object(embeddings, 'retrieve', return_value=embeddings.Retrieval(available=bool(mode))), \
                             patch('backend.conversation.agent.create_model_client', side_effect=lambda:
                                   Scripted(tuple(turn.get('scripted_decision') or IDEAL[scenario['id']][index]))):
                            result = run_agent(self.connection, turn['query'], histories[mode], states[mode],
                                **{k: turn[k] for k in ('answers', 'remove_filters', 'action') if k in turn})
                        states[mode] = result.context
                        histories[mode] += [dict(role='user', content=turn['query']), dict(role='assistant', content=result.answer)]
                        outputs.append(result.context.get('filters', {}))
                    self.assertEqual({k: outputs[1].get(k) for k in outputs[0]}, outputs[0],
                                     (scenario['id'], index, turn['query']))

    def test_explicit_enclosure_spellings_precede_semantic_suggestions(self):
        for spelling, enclosure, suggestion in [
            ('explosion-proof', 'explosionproof', 'safe_area'),
            ('explosion proof', 'explosionproof', 'safe_area'),
            ('weather-proof', 'weatherproof', 'safe_area'),
            ('weather proof', 'weatherproof', 'safe_area'),
        ]:
            with self.subTest(spelling=spelling):
                self.context, self.history = {}, []
                result = self.semantic_turn(spelling + ' actuator, 110 V', {suggestion})
                self.assertEqual(result.context['filters']['enclosure'], enclosure)
                self.assertNotIn('Interpreted the site', result.answer)

    def test_no_preference_service_is_not_affirmative(self):
        for phrase in ["on/off service does not matter", "on/off service doesn't matter",
                       'no preference for on/off service', "I don't care about on/off service"]:
            with self.subTest(phrase=phrase):
                self.context, self.history = {'filters': {'service': 'on_off'}}, []
                result = self.semantic_turn(phrase + ', 110 V', {'on_off'}, {'service': 'on_off', 'refine': True})
                self.assertNotIn('service', result.context['filters'])
                self.assertEqual(result.context['filters']['supply_voltage_v'], 110)

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

    def test_grounded_service_and_carried_filters_are_not_replaced_by_suggestions(self):
        result = self.semantic_turn('two-position actuator, 110 V', {'modulating'}, {'service': 'on_off'})
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.context = {'filters': {'service': 'on_off', 'enclosure': 'weatherproof', 'supply_voltage_v': 110}}
        result = self.semantic_turn('and at least 70 Nm', {'modulating', 'hazard'}, {'refine': True, 'min_torque_nm': 70})
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

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
