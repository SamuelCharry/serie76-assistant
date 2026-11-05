"""Shown-set recommendations: real SQL, scripted intent, no inference."""
import json
from pathlib import Path
from unittest.mock import patch

from backend.catalog.models import SearchFilters
from backend.catalog.repository import get_actuator
from backend.conversation import agent, integrity, policy, shown_recommendation
from scripts.check_public_text import response_text_issues
from test_agent_scenarios import Base, Scripted

PAIR = ['761A00-11300000/A', '761B00-11300000/A']
TRIPLE = ['762A00-11320000/A', '763A00-11320000/A', '764A00-11320000/A']


class ShownRecommendationTests(Base):
    def compare(self, codes=PAIR):
        return self.turn('Compare ' + ' vs '.join(codes), ('get_actuator', {'part_numbers': codes}))

    def recommend(self, query):
        shown = set(self.context['on_screen'])
        with patch('backend.conversation.agent.create_model_client', side_effect=AssertionError('LLM called')):
            result = agent.run_agent(self.connection, query, self.history, self.context)
        self.assertEqual(response_text_issues(vars(result)), [])
        self.assertFalse(result.debug['llm_called'])
        if result.recommendation:
            for item in result.recommendation['items']:
                self.assertIn(item['part_number'], shown)
                self.assertTrue(integrity.satisfies(get_actuator(self.connection, item['part_number']),
                                SearchFilters.model_validate(result.context.get('filters') or {})))
        return result

    def test_probe_a_compared_pair_kept_and_reasoned(self):
        compared = self.compare()
        self.assertIn('10 identical fields hidden.', compared.answer)
        result = self.recommend('which one do you recommend and why?')
        self.assertEqual(result.recommendation['items'][0]['part_number'], PAIR[0])
        self.assertIn('FLA at 50 Hz: 1.1 A vs 1.2 A', result.answer)
        self.assertIn('100 Nm vs 700 in-lb / 80 Nm', result.answer)
        self.assertIsNone(result.interaction)
        self.assert_probe('R-A', result)

    def test_probe_b_top_two_never_expand_to_full_search(self):
        self.turn('on/off 220 V weatherproof at least 150 Nm', ('search_actuators', {
            'service': 'on_off', 'supply_voltage_v': 220, 'enclosure': 'weatherproof', 'min_torque_nm': 150}))
        self.turn('compare the top 2', ('get_actuator', {'from_results_top': 2}))
        result = self.recommend('which is better for me?')
        self.assertEqual(result.recommendation['items'][0]['part_number'], '762A00-11320000/A')
        self.assertEqual(result.recommendation['total'], 2)
        self.assertEqual(len(result.context['last_ranked_list']), 2)
        self.assert_probe('R-B', result)

    def test_probe_c_new_bound_before_priority_and_purchase_advice(self):
        self.compare(TRIPLE)
        result = self.recommend('I need at least 200 Nm on/off and low current, which should I buy?')
        self.assertEqual(result.recommendation['items'][0]['part_number'], TRIPLE[1])
        self.assertIn('762A00-11320000/A is out: On/Off torque 150 Nm < 200 Nm.', result.answer)
        self.assertEqual(result.context['filters']['min_torque_nm'], 200)
        self.assertNotIn('process orders', result.answer)
        self.assert_probe('R-C', result)

    def assert_probe(self, name, result):
        expected = json.loads((Path(__file__).parent / 'fixtures/shown_recommendation_answers.json').read_text(encoding='utf-8'))
        self.assertEqual(result.answer, expected[name])

    def test_spanish_recommendation(self):
        self.compare()
        result = self.recommend('¿cuál me recomiendas?')
        self.assertTrue(result.answer.startswith('I recommend ' + PAIR[0] + ':'))

    def test_shown_list_low_power(self):
        self.turn('on/off 220 V weatherproof at least 150 Nm', ('search_actuators', {
            'service': 'on_off', 'supply_voltage_v': 220, 'enclosure': 'weatherproof', 'min_torque_nm': 150}))
        result = self.recommend('of those, which one for low power?')
        self.assertEqual(result.recommendation['items'][0]['part_number'], '762A00-11320000/A')
        self.assertIn('Motor power 40 W', result.answer)

    def test_priority_tie_uses_declared_next_key(self):
        self.compare()
        result = self.recommend('which do you recommend for low power?')
        self.assertIn('The priority ties at 15 W; lowest FLA breaks the tie.', result.answer)
        self.assertEqual(result.recommendation['items'][0]['part_number'], PAIR[0])

    def test_no_qualifier_names_nearest_without_recommending_it(self):
        self.compare()
        result = self.recommend('I need at least 200 Nm on/off, which is best?')
        self.assertIn('None of the shown models meets every requirement.', result.answer)
        self.assertIn('Nearest shown model: ' + PAIR[1], result.answer)
        self.assertEqual(result.recommendation['items'], [])
        self.assertIsNone(result.context.get('focused_model'))

    def test_strict_and_frequency_limits_remain_hard_requirements(self):
        self.compare(TRIPLE)
        result = self.recommend('which is best with on/off torque above 300 Nm and FLA below 3 A at 60 Hz?')
        self.assertEqual(result.recommendation['items'], [])
        self.assertIn('3.2 A >= 3 A', result.answer)
        self.assertIn('300 Nm <= 300 Nm', result.answer)

    def test_active_upper_bound_is_retained_with_new_lower_bound(self):
        self.compare(TRIPLE)
        self.context['filters'] = {'service': 'on_off', 'min_torque_nm': {'value': 500, 'op': 'lte'}}
        result = self.recommend('at least 200 Nm, which is best for low current?')
        self.assertEqual([i['part_number'] for i in result.recommendation['items']], [TRIPLE[1]])
        self.assertIn('750 Nm > 500 Nm', result.answer)

    def test_model_only_signals_intent_priority_not_new_filters_or_codes(self):
        self.compare(TRIPLE)
        model = Scripted(('search_actuators', {'intent': 'pick', 'sort_by': ['lowest_power'],
                                             'min_torque_nm': 1000, 'supply_voltage_v': 110}))
        result = agent.run_agent(self.connection, 'the sensible choice please, at least 200 Nm on/off',
                                 self.history, self.context, model=model)
        self.assertIsNotNone(model.seen)
        self.assertEqual(result.context['filters']['min_torque_nm'], 200)
        self.assertNotIn('supply_voltage_v', result.context['filters'])
        self.assertEqual(result.recommendation['items'][0]['part_number'], TRIPLE[1])
        self.assertEqual(response_text_issues(vars(result)), [])

    def test_cycles_and_duty_constraints_and_priority(self):
        self.compare(TRIPLE)
        result = self.recommend('which is best for highest duty with on/off and at least 24 cycles/hour?')
        self.assertEqual(result.recommendation['items'][0]['part_number'], TRIPLE[1])
        self.assertEqual(result.context['filters']['min_cycles_per_hour'], 24)
        self.assertIn('13 cycles/h < 24 cycles/h', result.answer)

    def test_unrepresented_quantity_does_not_get_a_verdict(self):
        self.compare()
        result = self.recommend('which is best at 50 Hz and 60 Hz?')
        self.assertIsNone(result.recommendation)
        self.assertIsNotNone(result.clarification)

    def test_rate_range_keeps_both_bounds(self):
        self.compare(TRIPLE)
        result = self.recommend('which is best for on/off with between 20 and 29 cycles/hour?')
        self.assertEqual(result.context['filters']['min_cycles_per_hour'],
                         [{'value': 20, 'op': 'gte'}, {'value': 29, 'op': 'lte'}])
        self.assertEqual([i['part_number'] for i in result.recommendation['items']], [TRIPLE[1]])
        self.assertIn('30 cycles/h > 29 cycles/h', result.answer)
        self.assertIn('13 cycles/h < 20 cycles/h', result.answer)

    def test_post_condition_rejects_a_corrupted_winner(self):
        self.compare(TRIPLE)
        original = shown_recommendation.verdict
        for bad_code, text_only in [(TRIPLE[0], False), ('762B00-11320000/A', False), (TRIPLE[0], True)]:
            def corrupt(*args):
                answer, rec, rows = original(*args)
                if text_only:
                    answer = answer.replace('I recommend ' + TRIPLE[1], 'I recommend ' + bad_code)
                else:
                    rec['items'][0]['part_number'] = bad_code
                return answer, rec, rows
            with self.subTest(code=bad_code, text_only=text_only), patch.object(shown_recommendation, 'verdict', side_effect=corrupt):
                result = self.recommend('at least 200 Nm on/off, which is best?')
                self.assertIsNone(result.recommendation)
                self.assertNotIn('I recommend', result.answer)
                self.assertIn('recommendation_integrity_failed', result.tool_calls[0]['validation'])

    def test_new_enclosure_requirement_is_enforced_and_readable(self):
        self.compare()
        result = self.recommend('which do you recommend for an explosionproof enclosure?')
        self.assertEqual(result.recommendation['items'], [])
        self.assertIn('Enclosure Weatherproof does not meet Explosionproof', result.answer)

    def test_buying_advice_is_not_order_placement(self):
        for query in ('which should I buy?', 'which one do you recommend?', '¿cuál debería comprar?'):
            self.assertFalse(policy.purchase_request(query))
        for query in ('buy 761A00-11300000/A', 'which should I buy and what is the delivery time?'):
            self.assertTrue(policy.purchase_request(query))
