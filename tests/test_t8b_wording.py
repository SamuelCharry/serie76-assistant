"""Observed wording failures, scripted decisions and SQL values only."""
from test_agent_scenarios import Base


class WordingTests(Base):
    def test_lowest_fla_criterion_is_not_repeated(self):
        result = self.turn('On/off 110 V, least current',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                                 'sort_by': ['lowest_current']}))
        self.assertNotIn('lowest FLA, then lowest FLA', result.answer)
        self.assertNotIn('lowest FLA, then lowest FLA', result.recommendation['ranked_by'])

    def test_zero_results_have_no_ranking_line(self):
        result = self.turn('On/off 110 V at least 100000 Nm',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                                 'min_torque_nm': 100000}))
        self.assertNotIn('Ranked by', result.answer)
        self.assertIn('Closest published', result.answer)

    def test_two_matches_offer_compare_them_only(self):
        result = self.turn('On/off 110 V over 300 Nm under 30 s at 60 Hz',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                                 'min_torque_nm': {'value': 300, 'op': 'gt'},
                                                 'max_operating_time_s': {'value': 30, 'op': 'lt'},
                                                 'frequency_hz': 60}))
        self.assertEqual(result.recommendation['total'], 2)
        self.assertNotIn('Show all 2', result.suggested_replies)
        self.assertIn('Compare them', result.suggested_replies)

    def test_comparison_faster_lead_names_winner_and_values(self):
        result = self.turn('764A00-11300000/A vs 765A00-11300000/A — which is faster at 60 Hz?',
                           ('get_actuator', {'part_numbers': ['764A00-11300000/A', '765A00-11300000/A'],
                                             'focus': ['operating_time'], 'focus_frequency_hz': 60}))
        self.assertIn('764A00-11300000/A is faster at 60 Hz: 30 s vs 88 s', result.lead)
        self.assertNotIn('0 identical fields hidden', result.answer)
