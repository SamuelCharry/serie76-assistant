"""Comparison must use full published differences and answer metric questions."""
from test_agent_scenarios import Base


class ComparisonTests(Base):
    def test_three_model_focus_still_hides_identical_full_fields(self):
        result = self.turn('Compare 765A00-11320000/A vs 765B00-11320000/A vs 765Y30-11320000/A',
                           ('get_actuator', {'part_numbers': ['765A00-11320000/A',
                                                              '765B00-11320000/A',
                                                              '765Y30-11320000/A'], 'focus': ['torque']}))
        fields = [row['field'] for row in result.comparison['rows']]
        self.assertIn('operating_time_60hz_s', fields)
        self.assertNotIn('motor_power_w', fields)
        self.assertFalse(any(len(set(row['values'])) == 1 for row in result.comparison['rows']))

    def test_lra_question_names_lower_winner(self):
        result = self.turn('Compare 763B00-11300000/A vs 763X30-11300000/A: which has the lowest LRA at 60 Hz?',
                           ('get_actuator', {'part_numbers': ['763B00-11300000/A',
                                                              '763X30-11300000/A'], 'focus': ['lra']}))
        self.assertIn('LRA', result.lead)
        self.assertIn('60 Hz', result.lead)
        self.assertIn(' vs ', result.lead)

    def test_more_current_names_higher_winner(self):
        result = self.turn('Compare 761A00-11300000/A vs 761B00-11300000/A: which draws more current at 60 Hz?',
                           ('get_actuator', {'part_numbers': ['761A00-11300000/A',
                                                              '761B00-11300000/A'], 'focus': ['fla']}))
        self.assertIn('more current', result.lead)
        self.assertIn('60 Hz', result.lead)

    def test_three_compared_models_metric_question_leads_with_model(self):
        result = self.turn('Which of 763B00-11300000/A, 763X30-11300000/A, and 763Y30-11300000/A has the lowest LRA at 60 Hz?',
                           ('get_actuator', {'part_numbers': ['763B00-11300000/A',
                                                              '763X30-11300000/A',
                                                              '763Y30-11300000/A']}))
        self.assertIn('LRA at 60 Hz', result.lead)
        self.assertIn(' A', result.lead)
