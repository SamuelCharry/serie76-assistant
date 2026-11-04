"""Round-six scripted regressions against the active SQL catalogue."""
import unittest
from backend.conversation import policy
from test_agent_scenarios import Base


class UnderstandingTests(unittest.TestCase):
    def test_service_phrases(self):
        for query in ('open and shut', 'open/shut', 'open or close'):
            self.assertEqual(policy.colloquial_requirements(query)[0]['service'], 'on_off')
        for query in ('partial positions', 'set to partial', 'mixing positions'):
            self.assertEqual(policy.colloquial_requirements(query)[0]['service'], 'modulating')

    def test_hazard_and_nonhazard_phrases(self):
        for query in ('propane nearby', 'butane tank', 'LPG', 'natural gas', 'ammonia',
                      'acetylene', 'hydrogen off-gassing', 'combustible dust', 'classified area'):
            self.assertTrue(policy.hazard_signal(query), query)
        self.assertTrue(policy.nonhazard_signal("no, it's outside the hazardous zone"))


class RoundSixScenarios(Base):
    def test_wp_abbreviation(self):
        result = self.turn('wp on/off 220 V',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220}))
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_quickest_uses_shown_set_after_glossary(self):
        self.turn('modulating explosionproof 110 V',
                  ('search_actuators', {'service': 'modulating', 'enclosure': 'explosionproof',
                                        'supply_voltage_v': 110}))
        self.turn('what does modulating mean exactly?',
                  ('explain_terms', {'term_keys': ['modulating']}))
        result = self.turn('back to it: which of those is quickest?',
                           ('get_actuator', {'part_numbers': []}))
        self.assertIn('operating time', result.answer)
        self.assertNotIn('Comparing ', result.answer)

    def test_closest_after_conflict_names_relaxations(self):
        self.turn('DC 3-phase', ('search_actuators', {'supply_current': 'DC', 'phase_count': 3}))
        result = self.turn("what's closest?", ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('Drop 3-phase', result.answer)
        self.assertIn('Drop DC', result.answer)

    def test_stronger_verdict_pairs_codes_and_values(self):
        codes = ['765X30-11320000/A', '765Y30-11320000/A']
        self.turn('compare ' + ' and '.join(codes), ('get_actuator', {'part_numbers': codes}))
        result = self.turn('which is stronger?', ('get_actuator', {'part_numbers': []}))
        self.assertIn('765Y30-11320000/A 3000 Nm', result.answer)
        self.assertIn('765X30-11320000/A 2000 Nm', result.answer)

    def test_zero_result_recommendation_labeled_alternatives(self):
        result = self.turn('is there anything for 48 V?',
                           ('search_actuators', {'supply_voltage_v': 48}))
        self.assertEqual(result.recommendation['total'], 0)
        self.assertIn('Alternatives', result.recommendation['ranked_by'])
        self.assertTrue(all('drop' in item['reason'].lower() for item in result.recommendation['items']))

    def test_verdict_ranking_label_matches_metric(self):
        result = self.turn('Which explosionproof 220 V on/off model has the lowest operating time at 60 Hz?',
                           ('search_actuators', {'enclosure': 'explosionproof', 'supply_voltage_v': 220,
                                                 'service': 'on_off', 'frequency_hz': 60}))
        self.assertIn('operating time', result.answer)
        self.assertIn('fastest operating time', result.recommendation['ranked_by'])

    def test_pick_has_one_open_torque_assumption(self):
        self.turn('xp mod 220', ('search_actuators', {'enclosure': 'explosionproof',
                                                    'service': 'modulating', 'supply_voltage_v': 220}))
        result = self.turn('pick one', ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(result.answer.count('Assumes no'), 1)

    def test_explicit_110_beats_battery_inference(self):
        result = self.turn('valve in a battery room with hydrogen off-gassing, 110 V',
                           ('search_actuators', {'supply_voltage_v': 24, 'supply_current': 'DC',
                                                 'enclosure': 'explosionproof'}))
        self.assertEqual(int(result.context['filters']['supply_voltage_v']), 110)
        self.assertNotEqual(result.context['filters'].get('supply_current'), 'DC')
        self.assertTrue(all(p['part_number'].endswith('11300000/A') for p in result.recommendation['items']))

    def test_explicit_explosionproof_from_hazard_is_accepted(self):
        result = self.turn('propane stored nearby, modulating 220 V',
                           ('search_actuators', {'service': 'modulating', 'supply_voltage_v': 220,
                                                 'enclosure': 'explosionproof'}))
        self.assertEqual(result.context['filters']['enclosure'], 'explosionproof')
        self.assertTrue(all(p['part_number'][3] in 'XY' for p in result.recommendation['items']))

    def test_outside_hazardous_zone_answers_pending_enclosure(self):
        self.turn('valve at a gas station canopy, 220 V on/off',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220}))
        result = self.turn("no, it's outside the hazardous zone",
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_big_valve_asks_torque_without_smallest_models(self):
        result = self.turn('need something for a big valve', ('search_actuators', {}))
        self.assertIn('torque', result.answer.lower())
        self.assertFalse(result.recommendation)
        self.assertNotIn('761A00', result.answer)
        follow = self.turn('eh', ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('torque', follow.answer.lower())
        self.assertNotIn('761A00', follow.answer)

    def test_comparison_fla_difference(self):
        codes = ['763A00-11320000/A', '763A00-11330C00/A']
        self.turn('Compare ' + ' and '.join(codes), ('get_actuator', {'part_numbers': codes}))
        result = self.turn('difference in FLA at 50 Hz?', ('get_actuator', {'part_numbers': []}))
        self.assertIn('1.3 A', result.answer)
        self.assertIn('1 A', result.answer)
        self.assertIn('0.3 A', result.answer)
        self.assertNotIn('Comparing ', result.answer)

    def test_longest_service_life_is_unpublished(self):
        result = self.turn('which one lasts longest?', ('search_actuators', {}))
        self.assertIn('service life', result.answer.lower())
        self.assertFalse(result.products)

    def test_catalogue_torque_range_from_sql(self):
        result = self.turn('what torque range does the catalogue cover?',
                           ('explain_terms', {'term_keys': ['torque']}))
        self.assertIn('65', result.answer)
        self.assertIn('9000', result.answer)
        self.assertIn('On/Off', result.answer)
        self.assertIn('Modulating', result.answer)

    def test_single_field_then_code_correction(self):
        first = self.turn('cycles per hour of 763B00-11320000/A',
                          ('get_actuator', {'part_numbers': ['763B00-11320000/A'], 'focus': ['overview']}))
        self.assertIn('On/Off cycles per hour', first.answer)
        self.assertNotIn('On/Off torque', first.answer)
        second = self.turn('wrong code, 763B00-11300000/A',
                           ('get_actuator', {'part_numbers': ['763B00-11300000/A'], 'focus': ['overview']}))
        self.assertIn('On/Off cycles per hour', second.answer)
        self.assertNotIn('On/Off torque', second.answer)
