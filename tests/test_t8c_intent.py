"""One model decision may signal discourse intent without inventing catalogue values."""
from test_agent_scenarios import Base


class IntentTests(Base):
    def test_clarification_tool_can_signal_spanish_pick(self):
        self.turn('on/off at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn('cual me recomiendas?',
                           ('ask_clarification', {'field': 'requirements', 'intent': 'pick'}))
        self.assertTrue(result.answer.startswith('I recommend '))
        self.assertEqual(result.recommendation['shown'], len(result.recommendation['items']))

    def test_search_tool_can_signal_pick_without_new_filters(self):
        self.turn('modulating 220 V',
                  ('search_actuators', {'service': 'modulating', 'supply_voltage_v': 220}))
        result = self.turn("I don't care about voltage, just recommend something",
                           ('search_actuators', {'intent': 'pick'}))
        self.assertIn('I recommend', result.answer)
        self.assertIsNone(result.interaction)

    def test_explain_pick_is_short(self):
        self.turn('on/off at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn('why that one?',
                           ('ask_clarification', {'field': 'requirements', 'intent': 'explain_pick'}))
        self.assertIn('closest torque', result.answer)
        self.assertNotIn(' vs ', result.answer)

    def test_declined_question_uses_natural_current_match_sentence(self):
        self.turn('on/off at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn('I cannot tell yet', ('ask_clarification', {'field': 'decline'}))
        self.assertNotIn('The requirement for', result.answer)
        self.assertIn('best matches', result.answer)
