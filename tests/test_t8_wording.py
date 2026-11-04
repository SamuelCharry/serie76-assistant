from test_agent_scenarios import Base


class WordingTests(Base):
    def test_questions_and_ranking_read_as_sentences(self):
        result = self.turn('I need an on/off actuator with at least 70 Nm',
                           ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        self.assertIn('To narrow it down: supply voltage and enclosure.', result.answer)
        self.assertNotIn('Which supply voltage?', result.answer)
        self.assertIn('Ranked by closest torque at or above 70 Nm', result.answer)
        self.assertIn('Ranked by closest torque at or above 70 Nm', result.lead)
        self.assertTrue(result.recommendation['ranked_by'].startswith('closest torque'))
