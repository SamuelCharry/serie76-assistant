"""Answer shape follows the question, independently of tool selection."""
import unittest
from backend.conversation import answer_planner
from test_agent_scenarios import Base


class PlannerUnitTests(unittest.TestCase):
    def test_shapes_share_one_metric_table(self):
        self.assertEqual(answer_planner.plan('LRA/FLA ratio at 60 Hz').shape, 'ratio')
        self.assertEqual(answer_planner.plan('which has the most cycles per hour?').shape, 'verdict')
        self.assertEqual(answer_planner.plan('power and torque of this model').shape, 'fields')
        self.assertEqual(answer_planner.plan('full specs').shape, 'overview')
        self.assertEqual(answer_planner.plan('show all').shape, 'all')
        self.assertEqual(answer_planner.plan('next').shape, 'next')


class PlannerScenarioTests(Base):
    def test_ratio_uses_both_published_inputs(self):
        result = self.turn("What's the LRA/FLA ratio of 762A00-11320000/A at 60 Hz?",
                           ('get_actuator', {'part_numbers': ['762A00-11320000/A']}))
        self.assertIn('1.2 A / 1 A = 1.2', result.answer)
        self.assertNotIn('On/Off torque', result.answer)

    def test_metric_question_uses_verdict_not_table(self):
        self.turn('On/off explosionproof 220 V with at least 40% duty',
                  ('search_actuators', {'service': 'on_off', 'enclosure': 'explosionproof',
                                        'supply_voltage_v': 220, 'min_duty_s4_percent': 40}))
        result = self.turn('which has the most cycles per hour?',
                           ('get_actuator', {'part_numbers': self.context['last_ranked_list'][:3]}))
        self.assertIn('190 cycles/h', result.answer)
        self.assertNotIn('Comparing ', result.answer)
        self.assertNotIn('Motor power:', result.answer)

    def test_named_two_fields_do_not_dump_overview(self):
        result = self.turn('power and torque of 763Y30-11300000/A',
                           ('get_actuator', {'part_numbers': ['763Y30-11300000/A']}))
        self.assertIn('Motor power', result.answer)
        self.assertIn('torque', result.answer.lower())
        self.assertNotIn('Operating time', result.answer)

    def test_show_all_and_next_have_key_values(self):
        self.turn('On/Off at least 70 Nm, 110 V', ('search_actuators', {
            'service': 'on_off', 'min_torque_nm': 70, 'supply_voltage_v': 110}))
        next_page = self.turn('next', ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('torque', next_page.answer.lower())
        self.assertIn('FLA', next_page.answer)
        full = self.turn('show all', ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(len(full.context['last_shown_list']), len(full.context['last_ranked_list']))
        self.assertIn('torque', full.answer.lower())

    def test_voltage_equivalent_keeps_requested_field(self):
        self.turn('Rated motor power of 763Y30-11300000/A?',
                  ('get_actuator', {'part_numbers': ['763Y30-11300000/A']}))
        follow = self.turn('and at 220 V?', ('get_actuator', {
            'reference_kind': 'focused', 'equivalent_voltage_v': 220}))
        self.assertIn('763Y30-11320000/A', follow.answer)
        self.assertIn('Motor power', follow.answer)
        self.assertNotIn('On/Off torque', follow.answer)

    def test_show_all_with_filter_returns_full_list_without_question(self):
        result = self.turn('show all explosionproof', ('search_actuators', {'enclosure': 'explosionproof'}))
        self.assertEqual(len(result.context['on_screen']), result.recommendation['total'])
        self.assertIsNone(result.interaction)
        self.assertIn('torque', result.answer.lower())

    def test_show_all_overrides_missing_service_question(self):
        result = self.turn('show all models with at least 70 Nm',
                           ('search_actuators', {'min_torque_nm': 70}))
        self.assertIsNone(result.interaction)
        self.assertEqual(len(result.context['on_screen']), result.recommendation['total'])

    def test_superlative_search_returns_one_verdict(self):
        result = self.turn('cual gasta menos corriente de los de 24v?',
                           ('search_actuators', {'supply_voltage_v': 24, 'sort_by': ['lowest_current']}))
        self.assertIn('FLA', result.answer)
        self.assertNotIn('To narrow it down', result.answer)
        self.assertNotIn('Ranked by', result.answer)
