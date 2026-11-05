"""The picked model becomes the referent for electrical follow ups."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class PickFocusTests(Base):
    def test_pick_then_draw_current_power(self):
        self.turn('220 V', ('search_actuators', {'supply_voltage_v': 220}))
        picked = run_agent(self.connection, 'just pick one', self.history, self.context,
                           model=Raising(AssertionError('no LLM')))
        self.assertIn('I recommend', picked.answer)
        self.assertIn('Assumes no torque requirement', picked.answer)
        code = picked.recommendation['items'][0]['part_number']
        result = run_agent(self.connection, 'what does that one draw?', self.history, picked.context,
                           model=Raising(AssertionError('no LLM')))
        self.assertIn(code, result.answer)
        self.assertIn('FLA', result.answer)
        self.assertIn('LRA', result.answer)
        self.assertIn('Motor power', result.answer)
        self.assertNotIn('On/Off torque', result.answer)
