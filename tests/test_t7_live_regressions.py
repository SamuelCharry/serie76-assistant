"""Regressions from v6 recorded failures: scripted decisions, real SQL, no inference."""
from unittest.mock import patch

from test_agent_scenarios import Base
from backend.conversation import policy
from backend.catalog.repository import get_actuator

A = '761A00-11300000/A'
B = '761B00-11300000/A'


class RecordedFailureTests(Base):
    def test_noncanonical_query_recovers_model_omitted_suffix_from_user_code(self):
        result = self.turn('give me the specs for 761a0011300000/a',
                           ('get_actuator', {'part_numbers': ['761A0011300000']}))
        self.assertEqual(result.products[0]['base_part_number'], A)
        self.assertEqual(result.tool_calls[0]['parameters']['part_numbers'], [A])
        self.assertIn('model_prefix_replaced_from_explicit_code', result.tool_calls[0]['overrides'])
        self.assertIn("Interpreted '761a0011300000/a' as " + A, result.answer)
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)

    def test_separator_variants_preserve_explicit_suffix_and_user_prefixes(self):
        for written in ('761a0011300000/a', '761a00-11300000/a', '761a0011300000a', '761a00-11300000a'):
            with self.subTest(written=written):
                self.assertEqual(policy.codes_in_text('Show ' + written), [A])
                self.assertEqual(policy.grounded_lookup_codes(['761A0011300000'], 'Show ' + written)[0], [A])
        for written in ('761a0011300000', '761a00-11300000'):
            with self.subTest(written=written):
                self.assertEqual(policy.codes_in_text('Show ' + written), [])
                # A differently formatted explicit prefix must not be silently completed.
                self.assertEqual(policy.grounded_lookup_codes(['761A0011300000'], f'Compare {A} and {written}')[1], [])

    def test_purchase_unsupported_decision_still_looks_up_named_product(self):
        with patch('backend.conversation.agent.get_actuator', wraps=get_actuator) as lookup:
            result = self.turn(f'Buy two units of {A} and confirm delivery tomorrow.',
                               ('ask_clarification', {'field': 'unsupported'}))
        self.assertEqual([c.args[1] for c in lookup.call_args_list], [A])
        self.assertEqual(result.products[0]['base_part_number'], A)
        self.assertTrue(result.answer.startswith('The catalogue cannot process orders or confirm delivery.'))
        self.assertEqual(result.tool_calls[0]['name'], 'get_actuator')
        self.assertEqual(result.tool_calls[0]['parameters']['part_numbers'], [A])
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)
        self.assertIsNone(result.clarification)
        self.assertEqual(result.suggestions, [])

    def test_purchase_without_complete_code_and_unrelated_unsupported_do_not_lookup(self):
        for query in ('Buy 761A00-11300000 tomorrow', f'Tell me a joke about {A}'):
            with self.subTest(query=query), patch('backend.conversation.agent.get_actuator', side_effect=AssertionError('unsupported lookup')):
                result = self.turn(query, ('ask_clarification', {'field': 'unsupported'}))
            self.assertFalse(result.products)
            self.assertEqual(result.suggestions, [])

    def test_model_prefixes_do_not_poison_label_invoice_comparison(self):
        query = f'The label says {A} but my invoice says {B}. Which one is actually installed?'
        self.assertEqual(policy.codes_in_text(query), [A, B])
        with patch('backend.conversation.agent.get_actuator', wraps=get_actuator) as lookup:
            result = self.turn(query, ('get_actuator', {'part_numbers': [A, B, '761A00-11300', '761B00-11300']}))
        self.assertEqual([c.args[1] for c in lookup.call_args_list], [A, B])
        self.assertEqual(result.comparison['models'], [A, B])
        self.assertEqual(result.tool_calls[0]['parameters']['part_numbers'], [A, B])
        self.assertIn('cannot identify', result.answer)
        self.assertIn('nameplate', result.answer)

    def test_model_truncation_uses_only_complete_code_in_current_query(self):
        with patch('backend.conversation.agent.get_actuator', wraps=get_actuator) as lookup:
            result = self.turn(f'Buy two units of {A} and confirm delivery tomorrow.',
                               ('get_actuator', {'part_numbers': ['761A00-11300']}))
        self.assertEqual([c.args[1] for c in lookup.call_args_list], [A])
        self.assertEqual(result.tool_calls[0]['parameters']['part_numbers'], [A])
        self.assertEqual(result.products[0]['base_part_number'], A)
        self.assertIn('cannot process orders', result.answer)

    def test_explicit_user_prefix_with_unique_sql_match_is_resolved_visibly(self):
        for query in ('Show 761A00-11300', f'Compare {A} and 761A00-11300'):
            with self.subTest(query=query):
                result = self.turn(query, ('get_actuator', {'part_numbers': ['761A00-11300']}))
                self.assertEqual([p['base_part_number'] for p in result.products], [A])
                self.assertIn("Interpreted '761A00-11300' as " + A, result.answer)
                self.assertIn(dict(field='part_number', user_phrase='761A00-11300', value=A), result.assumptions)
                self.assertIsNone(result.clarification)
                self.assertIsNone(result.comparison)

    def test_model_prefix_without_unique_current_full_code_stays_incomplete(self):
        for query, prefix in ((f'Show {A}', '761Z00-11300'),
                              (f'Compare {A} and {B}', '761'),
                              ('Show the actuator', '761A00-11300')):
            with self.subTest(query=query), patch('backend.conversation.agent.get_actuator', side_effect=AssertionError('partial lookup')):
                result = self.turn(query, ('get_actuator', {'part_numbers': [prefix]}))
            self.assertEqual(result.clarification['field'], 'part_number')

    def test_informal_spanish_on_off_is_grounded_without_assumption(self):
        result = self.turn('lo necesito para abrir completo o cerrar completo, 110 V, al menos 50 Nm',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                            'bounds': [{'field': 'min_torque_nm', 'op': 'gte', 'value': 50}]}))
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertEqual(result.context['filters']['min_torque_nm'], {'value': '50', 'op': 'gte'})
        self.assertNotIn('ungrounded:service', result.tool_calls[0]['validation'])

    def test_unknown_rating_cannot_use_generic_definition_overlap(self):
        result = self.turn('What does IP67 mean for these actuators? Use your general knowledge if the summary does not explain it.',
                           ('explain_terms', {'term_keys': ['weatherproof']}))
        self.assertEqual(result.clarification['field'], 'term_not_in_summary')
        self.assertFalse(result.terms)
        self.assertEqual(result.tool_calls[0]['name'], 'ask_clarification')

    def test_combined_string_and_list_terms_do_not_split_into_characters(self):
        result = self.turn(f'What is the FLA of {A} at 60 Hz, and what does FLA mean?',
                           ('get_actuator', {'part_numbers': [A], 'focus': ['fla'],
                            'focus_frequency_hz': 60, 'explain_terms': 'fla'}),
                           ('explain_terms', {'term_keys': ['fla']}))
        self.assertEqual(result.tool_calls[0]['parameters']['explain_terms'], ['fla'])
        self.assertEqual(result.tool_calls[0]['model_calls'][0]['args']['explain_terms'], 'fla')
        self.assertEqual(result.tool_calls[0]['model_calls'][1]['args']['term_keys'], ['fla'])
        self.assertEqual([t['term_key'] for t in result.terms], ['fla'])
        self.assertIn('FLA at 60 Hz: 1.2 A', result.answer)
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)

    def test_multipart_keeps_supported_terms_and_names_unknown_rating(self):
        result = self.turn(f'For {A}, give me torque, current, operating time, compare it with {B}, and explain FLA, LRA, S4 and IP67.',
                           ('get_actuator', {'part_numbers': [A, B], 'explain_terms': 'FLA, LRA, S4, IP67'}),
                           ('explain_terms', {'term_keys': ['fla', 'lra', 'duty_cycle', 'weatherproof']}))
        self.assertEqual(result.comparison['models'], [A, B])
        self.assertEqual([t['term_key'] for t in result.terms], ['fla', 'lra', 'duty_cycle'])
        self.assertIn('LRA at 60 Hz: 1.4 A', result.answer)
        self.assertIn("The document doesn't define that term.", result.answer)
        self.assertNotIn('IP67', result.answer)
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)
