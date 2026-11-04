"""Answer the requested shape over the complete visible search context."""
from test_agent_scenarios import Base


class FollowupTests(Base):
    def test_catalogue_superlatives_do_not_ask_questions(self):
        result = self.turn('What is the lowest motor power?', ('search_actuators', {}))
        self.assertIsNone(result.interaction)
        self.assertIn('W', result.answer)

    def test_compared_difference_in_operating_time(self):
        self.turn('Compare 762A00-11320000/A vs 762X30-11320000/A',
                  ('get_actuator', {'part_numbers': ['762A00-11320000/A', '762X30-11320000/A']}))
        result = self.turn('How much faster is the quicker one at 50 Hz?', None)
        self.assertIn('difference', result.answer.lower())
        self.assertIn('s', result.answer)

    def test_compare_all_visible_models(self):
        self.turn('On/off 24 V', ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 24}))
        result = self.turn('compare all', None)
        self.assertIsNotNone(result.comparison)

    def test_why_that_after_pick(self):
        self.turn('On/off 110 V', ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110}))
        self.turn('best?', None)
        result = self.turn('why that?', None)
        self.assertIn('rank', result.answer.lower())

    def test_manufacturer_is_not_a_spec_dump(self):
        result = self.turn('Who manufactures 761A00-11300000/A?', None)
        self.assertIn('manufacturer', result.answer.lower())
        self.assertNotIn('Motor power', result.answer)

    def test_question_rephrase(self):
        self.turn('Need on/off 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn("I don't understand", None)
        self.assertIn('?', result.answer)
        self.assertNotIn('models:', result.answer.lower())

    def test_thanks_after_cancel_does_not_restart(self):
        self.turn('Need on/off 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        self.turn('drop it', None)
        result = self.turn('great thanks', None)
        self.assertIn("You're welcome", result.answer)
        self.assertIsNone(result.recommendation)

    def test_nearest_after_zero_results_names_a_model(self):
        self.turn('On/off 24 V Explosionproof at least 2000 Nm',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 24,
                                        'enclosure': 'explosionproof', 'min_torque_nm': 2000}))
        result = self.turn('and the nearest one?', None)
        self.assertIn('/A', result.answer)
        self.assertIn('relax', result.answer.lower())

    def test_frequency_and_code_correction_preserves_single_field(self):
        self.turn('LRA at 50 Hz for 761A00-11300000/A',
                  ('get_actuator', {'part_numbers': ['761A00-11300000/A'], 'focus': ['lra'],
                                    'focus_frequency_hz': 50}))
        result = self.turn('sorry, at 60 Hz and for 761B00-11300000/A', None)
        self.assertIn('LRA', result.answer)
        self.assertIn('60 Hz', result.answer)
        self.assertNotIn('Comparing ', result.answer)
