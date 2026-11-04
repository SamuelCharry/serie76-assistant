"""Observed wording failures, scripted decisions and SQL values only."""
from test_agent_scenarios import Base


class WordingTests(Base):
    def test_search_with_interpretation_starts_with_count(self):
        result = self.turn('Open and close at least 1.5 kNm',
                           ('search_actuators', {'min_torque_nm': 1500}))
        self.assertTrue(result.answer.startswith('15 actuators meet:'), result.answer)

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

    def test_comparison_missing_note_appears_once_per_model(self):
        result = self.turn('Compare 761X30-11370000/A vs 761X30-11380000/A',
                           ('get_actuator', {'part_numbers': ['761X30-11370000/A', '761X30-11380000/A'],
                                             'focus': ['overview']}))
        self.assertNotIn('not published in this table layout', result.answer)
        self.assertLessEqual(result.answer.count('not published for this model'), 2)
        self.assertIn('not published for this model', result.answer)

    def test_shared_duty_followup_is_one_sentence(self):
        self.turn('Duty cycle of 763C00-11330C00/A',
                  ('get_actuator', {'part_numbers': ['763C00-11330C00/A'], 'focus': ['duty']}))
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, 'is that for on/off or modulating?', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertEqual(result.answer, 'It applies to both On/Off and Modulating (shared).')

    def test_cancel_without_pending_does_not_claim_cancellation(self):
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Scripted
        result = run_agent(self.connection, 'Cancel', [], {},
                           model=Scripted(('ask_clarification', {'field': 'cancel'})))
        self.assertNotIn('Cancelled', result.answer)
