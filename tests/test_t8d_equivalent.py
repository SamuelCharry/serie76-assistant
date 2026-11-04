"""A unique equivalent acts on the focused model instead of returning code names only."""
from test_agent_scenarios import Base


class EquivalentTests(Base):
    def test_voltage_sibling_shows_overview(self):
        self.turn('specs of 762X30-11320000/A',
                  ('get_actuator', {'part_numbers': ['762X30-11320000/A']}))
        result = self.turn('hmm no, the 110 V one',
                           ('get_actuator', {'reference_kind': 'focused', 'equivalent_voltage_v': 110}))
        self.assertEqual(result.products[0]['base_part_number'], '762X30-11300000/A')
        self.assertIn('Motor power', result.answer)

    def test_counterpart_comparison_chooses_nearest(self):
        self.turn('764X30-11300000/A full data',
                  ('get_actuator', {'part_numbers': ['764X30-11300000/A']}))
        result = self.turn('compare with its weatherproof counterpart',
                           ('get_actuator', {'reference_kind': 'focused',
                                             'equivalent_enclosure': 'weatherproof'}))
        self.assertEqual(result.comparison['models'][0], '764X30-11300000/A')
        self.assertEqual(len(result.comparison['models']), 2)

    def test_unique_suffixless_code_is_completed_from_sql(self):
        result = self.turn('761A00-11300000',
                           ('get_actuator', {'part_numbers': ['761A00-11300000']}))
        self.assertIn('Interpreted', result.answer)
        self.assertEqual(result.products[0]['base_part_number'], '761A00-11300000/A')
