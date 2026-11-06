"""T8c references are resolved against persisted compared and shown rows."""
from test_agent_scenarios import Base


class ReferenceTests(Base):
    def test_bare_specs_after_focused_answer_expands_overview_without_model(self):
        self.turn('Torque of 761A00-11300000/A',
                  ('get_actuator', {'part_numbers': ['761A00-11300000/A'], 'focus': ['torque']}))
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, 'specs', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertIn('Motor power: 15 W', result.answer)
        self.assertFalse(result.debug['llm_called'])

    def test_compared_winner_and_followup_power(self):
        self.turn('Compare 762A00-11300000/A vs 762B00-11300000/A',
                  ('get_actuator', {'part_numbers': ['762A00-11300000/A', '762B00-11300000/A']}))
        winner = self.turn('the faster one',
                           ('get_actuator', {'reference_kind': 'compared_winner',
                                             'reference_metric': 'operating_time',
                                             'reference_direction': 'lower', 'reference_frequency_hz': 60,
                                             'focus': ['overview']}))
        self.assertEqual(winner.products[0]['base_part_number'], '762A00-11300000/A')
        power = self.turn('its power?',
                          ('get_actuator', {'reference_kind': 'focused', 'focus': ['motor_power']}))
        self.assertIn('762A00-11300000/A', power.answer)
        self.assertIn('Motor power', power.answer)

    def test_shown_position_and_full_specs(self):
        self.turn('On/off at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        last = self.turn('the last one',
                         ('get_actuator', {'reference_kind': 'last_shown', 'focus': ['torque']}))
        self.assertEqual(last.products[0]['base_part_number'], self.context['last_shown_list'][-1])
        full = self.turn('full specs',
                         ('get_actuator', {'reference_kind': 'focused', 'focus': ['overview']}))
        self.assertIn('Motor power', full.answer)
        self.assertIn('Operating time', full.answer)

    def test_three_model_comparison_uses_full_differing_rows(self):
        result = self.turn('Compare 765A00-11320000/A vs 765B00-11320000/A vs 765Y30-11320000/A',
                           ('get_actuator', {'part_numbers': ['765A00-11320000/A',
                                                              '765B00-11320000/A',
                                                              '765Y30-11320000/A'],
                                             'focus': ['overview']}))
        labels = {row['label'] for row in result.comparison['rows']}
        self.assertIn('On/Off duty S4', labels)
        self.assertNotIn('Motor power', labels)
        self.assertIn('Motor power', {row['label'] for row in result.comparison['hidden_rows']})
        self.assertTrue(all(len(set(row['values'])) > 1 for row in result.comparison['rows']))
