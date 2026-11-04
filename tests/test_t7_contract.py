"""T7 contract: scripted decisions, SQL and HTTP; never external inference."""
from unittest.mock import patch
from test_agent_scenarios import Base, Scripted
from backend.conversation.agent import run_agent
from backend.conversation import policy, tool_wire
from backend.catalog.models import SearchFilters
from backend.catalog.repository import search_actuators
import unittest


class NumericPolicyTests(unittest.TestCase):
    def test_decimal_comma_is_not_fifteen(self):
        self.assertEqual(policy.grounding_errors({'max_fla_a': {'value': 15, 'op': 'lt'}}, [], ['FLA menor a 1,5 A']), ['max_fla_a'])
        self.assertEqual(policy.grounding_errors({'max_fla_a': {'value': 1.5, 'op': 'lt'}}, [], ['FLA menor a 1,5 A']), [])


class ExploratoryTests(Base):
    def test_range_keeps_both_bounds(self):
        args = tool_wire.canonical_arguments('search_actuators', {'service': 'on_off', 'bounds': [
            {'field': 'min_torque_nm', 'op': 'gte', 'value': 70},
            {'field': 'min_torque_nm', 'op': 'lte', 'value': 100}]})
        rows = search_actuators(self.connection, SearchFilters(**args, limit=100))['products']
        self.assertTrue(rows)
        self.assertTrue(all(70 <= p['measurements']['on_off_torque_nm'] <= 100 for p in rows))

    def test_voltage_or_is_a_question_not_silent_choice(self):
        result = self.turn('I need a 110 V or 220 V on/off actuator. Either voltage is acceptable.',
                           ('search_actuators', {'supply_voltage_v': 110, 'service': 'on_off'}))
        question = result.interaction['questions'][0]
        self.assertEqual(question['id'], 'supply_voltage_v')
        self.assertEqual([o['value'] for o in question['options']], ['110', '220'])
        self.assertNotIn('supply_voltage_v', result.context['filters'])

    def test_same_performance_retains_numeric_threshold(self):
        self.turn('Find on/off actuators with at least 70 Nm.', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn('Actually I meant modulating, but keep the same performance.',
                           ('search_actuators', {'service': 'modulating', 'refine': True}))
        self.assertEqual(result.context['filters']['min_torque_nm'], '70')
        self.assertIn('same performance', result.answer)
        self.assertTrue(result.assumptions)

    def test_price_weighting_is_explicit_limitation(self):
        result = self.turn('Which actuator is best overall if torque matters twice as much as speed and price?',
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertIn("doesn't publish prices", result.answer)
        self.assertIn('weighted', result.answer)

    def test_purchase_does_not_claim_order(self):
        result = self.turn('Buy two units of 761A00-11300000/A and confirm delivery tomorrow.',
                           ('get_actuator', {'part_numbers': ['761A00-11300000/A']}))
        self.assertIn('cannot process orders', result.answer)
        self.assertEqual(result.suggestions, [])

    def test_label_invoice_does_not_assert_installed_model(self):
        result = self.turn('The label says 761A00-11300000/A but my invoice says 761B00-11300000/A. Which one is actually installed?',
                           ('get_actuator', {'part_numbers': ['761A00-11300000/A', '761B00-11300000/A']}))
        self.assertIn('cannot identify', result.answer)
        self.assertIn('nameplate', result.answer)

    def test_multi_part_includes_supported_terms_and_explicit_omission(self):
        result = self.turn('For 761A00-11300000/A, give me torque, current, operating time, compare it with 761B00-11300000/A, and explain FLA, LRA, S4 and IP67.',
                           ('get_actuator', {'part_numbers': ['761A00-11300000/A', '761B00-11300000/A'],
                            'focus': ['torque', 'fla', 'lra', 'operating_time'], 'explain_terms': ['fla', 'lra', 'duty_cycle']}))
        self.assertEqual({t['term_key'] for t in result.terms}, {'fla', 'lra', 'duty_cycle'})
        self.assertNotIn('IP67', result.answer)
        self.assertIn("The document doesn't define that term.", result.answer)


class InteractionTests(Base):
    def test_all_required_questions_and_no_suggestions(self):
        result = self.turn('At least 70 Nm and FLA below 1.5 A', ('search_actuators', {
            'min_torque_nm': 70, 'max_fla_a': {'value': 1.5, 'op': 'lt'}}))
        self.assertEqual({q['id'] for q in result.interaction['questions']}, {'service', 'frequency_hz'})
        self.assertEqual(result.suggested_replies,
                         ['Compare top 2', f"Show all {result.recommendation['total']}"])

    def test_submit_and_remove_without_model_budget(self):
        first = self.turn('At least 70 Nm and FLA below 1.5 A', ('search_actuators', {
            'min_torque_nm': 70, 'max_fla_a': {'value': 1.5, 'op': 'lt'}}))
        with patch('backend.conversation.agent.reserve_agent_call', side_effect=AssertionError('model budget used')):
            result = run_agent(self.connection, 'On/Off · 60 Hz', self.history, first.context,
                               answers={'service': 'on_off', 'frequency_hz': '60'})
            self.assertEqual(result.context['filters']['service'], 'on_off')
            self.assertEqual(result.context['filters']['frequency_hz'], 60)
            result = run_agent(self.connection, 'Remove torque', self.history, result.context,
                               remove_filters=['min_torque_nm'])
            self.assertNotIn('min_torque_nm', result.context['filters'])

    def test_greeting_uses_authenticated_first_name(self):
        with patch('backend.conversation.agent.reserve_agent_call', side_effect=AssertionError('model budget used')):
            result = run_agent(self.connection, '¡Hola!', [], {}, user_name='Samuel Charry')
        self.assertEqual(result.answer, 'Hello, Samuel. I can look up Series 76 actuators, find models for your requirements, compare models or explain catalogue terms.')
        self.assertEqual(result.suggestions, [])

    def test_decline_shows_three_candidates_without_repeating(self):
        self.turn('I need at least 70 Nm', ('search_actuators', {'min_torque_nm': 70}))
        result = self.turn('No.', ('ask_clarification', {'field': 'decline'}))
        self.assertEqual(len(result.products), 3)
        self.assertIsNone(result.interaction)
        self.assertIn('Without service', result.answer)

    def test_unrelated_free_text_does_not_repeat_pending_questions(self):
        first = self.turn('at least 70 Nm and FLA below 1.5 A', ('search_actuators', {
            'min_torque_nm': 70, 'max_fla_a': {'value': 1.5, 'op': 'lt'}}))
        result = self.turn('I do not know those details', ('ask_clarification', {'field': 'unsupported'}))
        self.assertIsNone(result.interaction)
        self.assertEqual(len(result.products), 3)
        self.assertIn('Without service', result.answer)
        self.assertIn('service', result.answer)
        self.assertIn('frequency', result.answer)

    def test_repeated_generic_find_does_not_loop(self):
        self.turn('Find an actuator for my requirements', ('ask_clarification', {'field': 'requirements'}))
        result = self.turn('Find an actuator for my requirements', ('ask_clarification', {'field': 'requirements'}))
        self.assertIsNone(result.interaction)
        self.assertEqual(len(result.products), 3)

    def test_broader_clarification_cannot_repeat_an_unresolved_field(self):
        self.turn('at least 70 Nm', ('search_actuators', {'min_torque_nm':70}))
        result = self.turn('I cannot tell you the details', ('ask_clarification', {'field':'requirements'}))
        self.assertIsNone(result.interaction)
        self.assertEqual(len(result.products), 3)


class ComparisonTests(Base):
    def compare(self, codes):
        return self.turn('Compare ' + ' vs '.join(codes), ('get_actuator', {'part_numbers': codes}))

    def test_two_models_table_winners_and_hidden_rows(self):
        result = self.compare(['761A00-11300000/A', '761B00-11300000/A'])
        c = result.comparison
        self.assertEqual(c['layout'], 'table')
        self.assertTrue(c['summary'])
        self.assertTrue(c['assumptions'])
        self.assertTrue(c['hidden_rows'])
        torque = next(r for r in c['rows'] if r['field'] == 'on_off_torque')
        self.assertEqual(torque['values'], ['700 in-lb / 80 Nm', '880 in-lb / 100 Nm'])
        self.assertEqual(torque['better'], 1)
        self.assertIsNotNone(result.lead)
        self.assertEqual(result.suggestions, [])

    def test_three_models_cards_have_four_key_fields(self):
        result = self.compare(['761A00-11300000/A', '761B00-11300000/A', '762A00-11300000/A'])
        self.assertEqual(result.comparison['layout'], 'cards')
        self.assertEqual(len(result.comparison['key_fields']), 4)
        self.assertEqual(result.comparison['key_fields_reason'], 'Fields you filtered on, then the ones that differ most')
        self.assertTrue(all(key in [row['field'] for row in result.comparison['rows']]
                            for key in result.comparison['key_fields']))
        self.assertTrue(all(r['better'] is None and len(r['values']) == 3 for r in result.comparison['rows']))
        self.assertEqual(result.suggestions, [])

    def test_three_models_key_fields_retain_explicit_service_and_frequency(self):
        codes = ['761A00-11300000/A', '761B00-11300000/A', '762A00-11300000/A']
        result = self.turn('Compare ' + ', '.join(codes) + ' for modulating at 60 Hz', ('get_actuator', {
            'part_numbers': codes, 'focus': ['torque','operating_time','fla'], 'focus_service': 'modulating', 'focus_frequency_hz': 60}))
        self.assertTrue({'modulating_torque', 'operating_time_60hz_s', 'fla_60hz_a'} <=
                        set(result.comparison['key_fields']))


class HttpContractTests(unittest.TestCase):
    @unittest.skipUnless(__import__('os').environ.get('SERIES76_TEST_DB') == '1', 'Real database checks disabled')
    def test_submission_validation_atomicity_and_history(self):
        from scripts.agent_acceptance import scenario_environment
        from fastapi.testclient import TestClient
        from backend.conversation import store
        with scenario_environment() as (app, connection, user):
            client = TestClient(app)
            with patch('backend.conversation.agent.create_model_client', return_value=Scripted(('search_actuators', {
                'min_torque_nm': 70, 'max_fla_a': {'value': 1.5, 'op': 'lt'}}))):
                first = client.post('/api/conversation', json={'query': 'at least 70 Nm and FLA below 1.5 A'}).json()
            sid = first['session_id']
            self.assertEqual(len(first['interaction']['questions']), 2)
            with patch('backend.conversation.agent.reserve_agent_call', side_effect=AssertionError('model call')):
                for payload, code in [({'answers': {'service': 'invented'}}, 'invalid_answers'),
                                      ({'answers': {'service': 1}}, 'invalid_answers'),
                                      ({'answers': []}, 'invalid_answers'),
                                      ({'answers': {'enclosure': 'weatherproof'}}, 'invalid_answers'),
                                      ({'remove_filters': [1]}, 'invalid_filter'),
                                      ({'remove_filters': ['no-such-filter']}, 'invalid_filter')]:
                    response = client.post('/api/conversation', json={'session_id': sid, 'query': 'invalid', **payload})
                    self.assertEqual(response.status_code, 422)
                    self.assertEqual(response.json()['error_code'], code)
                self.assertEqual(len(store.history(connection, sid, owner_id=user)), 2)
                submitted = client.post('/api/conversation', json={'session_id': sid, 'query': 'On/Off · 60 Hz',
                    'answers': {'service': 'on_off', 'frequency_hz': '60'}})
                self.assertEqual(submitted.status_code, 200)
                removed = client.post('/api/conversation', json={'session_id': sid, 'query': 'Remove torque',
                    'remove_filters': ['min_torque_nm']})
                self.assertEqual(removed.status_code, 200)
            saved = store.history(connection, sid, owner_id=user)[-1]
            for field in ('lead', 'interaction', 'active_filters', 'suggestions', 'suggested_replies', 'comparison'):
                self.assertEqual(saved[field], removed.json()[field])
            self.assertNotIn('min_torque_nm', [f['field'] for f in saved['active_filters']])


class SuggestionPolicyTests(Base):
    def test_clarification_has_actions_for_provisional_ranking(self):
        result = self.turn('at least 70 Nm', ('search_actuators', {'min_torque_nm': 70}))
        self.assertEqual(result.suggested_replies[0], 'Compare top 2')

    def test_two_to_four_results_have_one_comparison(self):
        result = self.turn('Explosionproof 24 V DC modulating over 1000 in-lb', ('search_actuators', {
            'enclosure': 'explosionproof', 'supply_voltage_v': 24, 'supply_current': 'DC', 'service': 'modulating',
            'min_torque_in_lb': {'value': 1000, 'op': 'gt'}}))
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0]['action']['type'], 'compare_top')
        self.assertEqual(result.suggested_replies[0], result.suggestions[0]['label'])

    def test_over_four_without_question_has_none(self):
        result = self.turn('On/off 24 V at least 70 Nm', ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 24, 'min_torque_nm': 70}))
        self.assertIsNone(result.interaction)
        self.assertGreater(result.tool_calls[0]['data']['total'], 4)
        self.assertEqual(result.suggested_replies,
                         ['Compare top 2', f"Show all {result.recommendation['total']}"])

    def test_impossibility_has_sql_relaxations(self):
        result = self.turn('On/off torque at least 999999 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 999999}))
        self.assertTrue(1 <= len(result.suggestions) <= 3)
        self.assertTrue(all(s.startswith(('Show ', 'Find actuators with ')) for s in result.suggestions))

    def test_single_factual_answer_has_none(self):
        result = self.turn('Power of 761A00-11300000/A', ('get_actuator', {'part_numbers': ['761A00-11300000/A'], 'focus': ['motor_power']}))
        self.assertEqual(result.suggestions, [])

    def test_definition_has_none(self):
        self.assertEqual(self.turn('Explain FLA', ('explain_terms', {'term_keys': ['fla']})).suggestions, [])

    def test_comparison_has_none(self):
        result = self.turn('Compare 761A00-11300000/A vs 761B00-11300000/A', ('get_actuator', {'part_numbers': ['761A00-11300000/A', '761B00-11300000/A']}))
        self.assertEqual(result.suggestions, [])

    def test_greeting_has_none(self):
        self.assertEqual(self.turn('Hello!', ('ask_clarification', {'field': 'unsupported'})).suggestions, [])

    def test_out_of_scope_has_none(self):
        self.assertEqual(self.turn('Tell me a joke', ('ask_clarification', {'field': 'unsupported'})).suggestions, [])

    def test_cancellation_has_none(self):
        self.assertEqual(self.turn('Cancel', ('ask_clarification', {'field': 'cancel'})).suggestions, [])

