"""Round-five failures, replayed with scripted model choices and real SQL."""
import unittest
from backend.conversation import answer_planner, policy
from backend.conversation.metrics import verdict
from backend.conversation import integrity
from test_agent_scenarios import Base


class NormalizerTests(unittest.TestCase):
    def test_hazard_recommendation_postcondition(self):
        products = [{'part_number': '761A00-11320000/A', 'enclosure': 'weatherproof'}]
        self.assertFalse(integrity.hazard_recommendation_safe(products, hazard=True))
        self.assertTrue(integrity.hazard_recommendation_safe(products, hazard=False))
    def test_upper_torque_word_order(self):
        for query in ('max torque 50 Nm', 'torque no more than 50 Nm',
                      'hasta 50 Nm', 'torque como máximo 50 Nm'):
            with self.subTest(query=query):
                self.assertEqual(policy.colloquial_requirements(query)[0]['min_torque_nm'],
                                 {'value': 50, 'op': 'lte'})

    def test_positioning_phrases_imply_modulating(self):
        for query in ('position anywhere between 0 and 90 degrees', 'any position',
                      'regule caudal', 'regular caudal', 'regulate flow',
                      'hold at 30% open'):
            with self.subTest(query=query):
                self.assertEqual(policy.colloquial_requirements(query)[0].get('service'),
                                 'modulating')

    def test_difference_shape(self):
        self.assertEqual(answer_planner.plan('How much higher is LRA than FLA at 50 Hz?').shape,
                         'difference')


class RoundFiveScenarios(Base):
    def test_tie_names_every_model(self):
        self.turn('compare 764A00-11320000/A and 764B00-11320000/A',
                  ('get_actuator', {'part_numbers': ['764A00-11320000/A', '764B00-11320000/A']}))
        result = self.turn('which needs less power?', ('get_actuator', {'part_numbers': []}))
        self.assertIn('764A00-11320000/A', result.answer)
        self.assertIn('764B00-11320000/A', result.answer)
        self.assertIn('180 W', result.answer)

    def test_best_duty_without_service_reports_each_service(self):
        codes = ['761X30-11320000/A', '762X30-11320000/A', '763X30-11320000/A']
        self.turn('compare ' + ' and '.join(codes),
                  ('get_actuator', {'part_numbers': codes}))
        result = self.turn('which one has the best duty?', ('get_actuator', {'part_numbers': codes}))
        self.assertIn('On/Off', result.answer)
        self.assertIn('Modulating', result.answer)
        self.assertNotIn('Which service duty', result.answer)

    def test_power_draw_and_cycles_are_focused(self):
        power = self.turn('power draw at full load of 764Y30-11300000/A?',
                          ('get_actuator', {'part_numbers': ['764Y30-11300000/A']}))
        self.assertIn('Motor power', power.answer)
        self.assertIn('FLA', power.answer)
        self.assertNotIn('On/Off torque', power.answer)
        cycles = self.turn('cuantos ciclos por hora aguanta el 762B00-11320000/A?',
                           ('get_actuator', {'part_numbers': ['762B00-11320000/A']}))
        self.assertIn('cycles per hour', cycles.answer)
        self.assertNotIn('Modulating starts', cycles.answer)
        self.assertNotIn('On/Off torque', cycles.answer)

    def test_three_phase_sibling(self):
        self.turn('specs for 763C00-11320000/A',
                  ('get_actuator', {'part_numbers': ['763C00-11320000/A']}))
        result = self.turn('the 3-phase version instead', ('search_actuators', {'phase_count': 3}))
        self.assertIn('763C00-11330C00/A', result.answer)
        self.assertNotIn('763A00-11330C00/A', result.answer)

    def test_voltage_sibling_is_not_torque_filter(self):
        self.turn('specs for 763C00-11320000/A',
                  ('get_actuator', {'part_numbers': ['763C00-11320000/A']}))
        result = self.turn('hmm no, the 110 V one',
                           ('search_actuators', {'supply_voltage_v': 110, 'min_torque_in_lb': 4800}))
        self.assertIn('763C00-11300000/A', result.answer)
        self.assertIsNone(result.recommendation)

    def test_cheapest_torque_is_proxy_on_filtered_set(self):
        result = self.turn("what's the cheapest way to get 1000 Nm?",
                           ('search_actuators', {'min_torque_nm': 1000}))
        self.assertIn("doesn't publish prices", result.answer)
        self.assertIn('motor power', result.answer.lower())
        self.assertGreater(result.recommendation['total'], 0)
        self.assertTrue(all('1000' not in item['reason'] or 'torque' in item['reason'].lower()
                            for item in result.recommendation['items']))

    def test_filtered_catalogue_count(self):
        result = self.turn('How many models do you have at 24 V?',
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('10 models', result.answer)
        self.assertNotIn('64 models', result.answer)

    def test_upper_bound_overrides_bad_model_decision(self):
        result = self.turn('max torque 50 Nm, cualquier voltaje',
                           ('search_actuators', {'min_torque_nm': 50}))
        self.assertEqual(result.context['filters']['min_torque_nm'], {'value': 50, 'op': 'lte'})
        self.assertEqual(result.recommendation['total'], 0)
        self.assertIn('65 Nm', result.answer)
        self.assertIn('No model is at or below 50 Nm', result.answer)

    def test_upper_bound_correction_keeps_other_filters(self):
        self.turn('on/off 220 V at least 400 Nm',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220,
                                        'min_torque_nm': 400}))
        result = self.turn('make that at most 400 Nm',
                           ('search_actuators', {'min_torque_nm': 400}))
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertEqual(int(result.context['filters']['supply_voltage_v']), 220)
        self.assertEqual(result.context['filters']['min_torque_nm'], {'value': 400, 'op': 'lte'})

    def test_hazard_override_cannot_show_weatherproof(self):
        result = self.turn('on/off 220 V, solvent fumes, weatherproof',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220,
                                                 'enclosure': 'weatherproof'}))
        self.assertIsNotNone(result.interaction)
        self.assertTrue(all(item['part_number'][3] in 'XY' for item in result.recommendation['items']))

    def test_hazard_preview_and_yes(self):
        first = self.turn('on/off 220 V with solvent fumes',
                          ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220}))
        self.assertTrue(all(item['part_number'][3] in 'XY' for item in first.recommendation['items']))
        second = self.turn('yes', ('search_actuators', {}))
        self.assertEqual(second.context['filters']['enclosure'], 'explosionproof')

    def test_classified_zone_answers_pending_hazard_question(self):
        self.turn('valve near a hydrogen electrolyser, 110 V on/off',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110}))
        result = self.turn("correct, it's a classified zone", ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(result.context['filters']['enclosure'], 'explosionproof')

    def test_change_only_keeps_filters(self):
        self.turn('on/off 24 V', ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 24}))
        result = self.turn('actually modulating', ('search_actuators', {'service': 'modulating'}))
        self.assertEqual(result.context['filters']['service'], 'modulating')
        self.assertEqual(int(result.context['filters']['supply_voltage_v']), 24)

    def test_difference_uses_sql(self):
        result = self.turn('How much higher is LRA than FLA at 50 Hz for 761A00-11300000/A?',
                           ('get_actuator', {'part_numbers': ['761A00-11300000/A']}))
        self.assertIn('0.2 A', result.answer)
        self.assertNotIn('On/Off torque', result.answer)

    def test_unpublished_attributes_do_not_dump_specs(self):
        for query in ("what's the operating temperature range of 761A00-11300000/A?",
                      'how do I install 762A00-11300000/A on a ball valve?'):
            with self.subTest(query=query):
                result = self.turn(query, ('get_actuator', {'part_numbers': [policy.codes_in_text(query)[0]]}))
                self.assertIn('catalogue', result.answer.lower())
                self.assertNotIn('On/Off torque', result.answer)
