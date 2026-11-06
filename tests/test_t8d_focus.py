"""A single-field question overrides an overly broad model focus."""
from test_agent_scenarios import Base


class FocusTests(Base):
    def test_starts_followup_does_not_repeat_duty(self):
        self.turn("What's the modulating duty of 762Y30-11320000/A?",
                  ('get_actuator', {'part_numbers': ['762Y30-11320000/A'], 'focus': ['duty']}))
        result = self.turn('and starts per hour?',
                           ('get_actuator', {'part_numbers': ['762Y30-11320000/A'], 'focus': ['overview']}))
        self.assertIn('Modulating starts per hour', result.answer)
        self.assertNotIn('Duty S4', result.answer)
        self.assertNotIn('On/Off cycles', result.answer)

    def test_spanish_starting_current_is_lra_only(self):
        result = self.turn('cuanto consume en arranque el 762A00-11300000/A',
                           ('get_actuator', {'part_numbers': ['762A00-11300000/A'], 'focus': ['overview']}))
        self.assertIn('LRA', result.answer)
        self.assertNotIn('On/Off torque', result.answer)
        self.assertNotIn('Motor power', result.answer)
