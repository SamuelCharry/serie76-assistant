"""Metric follow ups answer from the compared or ranked SQL rows."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class MetricContextTests(Base):
    def test_compared_faster_names_winner_or_tie_without_repeating_table(self):
        self.turn('compare 761X30-11320000/A vs 761Y30-11320000/A',
                  ('get_actuator', {'part_numbers': ['761X30-11320000/A', '761Y30-11320000/A']}))
        result = run_agent(self.connection, 'which of them is faster?', self.history, self.context,
                           model=Raising(AssertionError('no LLM needed')))
        self.assertIn('operating time', result.answer)
        self.assertNotIn('Comparing ', result.answer)

    def test_highest_duty_from_ranked_results_is_one_verdict(self):
        self.turn('on/off 110 V at least 100 Nm',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                        'min_torque_nm': 100}))
        result = run_agent(self.connection, 'the one with the highest duty among the results?',
                           self.history, self.context,
                           model=Raising(AssertionError('no LLM needed')))
        self.assertIn('duty', result.answer.lower())
        self.assertLess(len(result.answer.splitlines()), 4)

    def test_on_off_cycles_verdict_for_two_named_codes(self):
        result = self.turn('Between 761Y30-11300000/A and 762Y30-11300000/A, which one cycles more per hour on/off?',
                           ('get_actuator', {'part_numbers': ['761Y30-11300000/A', '762Y30-11300000/A']}))
        self.assertIn('761Y30-11300000/A', result.lead)
        self.assertIn('cycles', result.lead.lower())
