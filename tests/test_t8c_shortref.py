"""Short references after comparison stay tied to the compared models."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class ShortReferenceTests(Base):
    def test_faster_one_then_its_power_without_model(self):
        self.turn('compare 762A00-11300000/A and 762B00-11300000/A',
                  ('get_actuator', {'part_numbers': ['762A00-11300000/A',
                                                     '762B00-11300000/A']}))
        faster = run_agent(self.connection, 'the faster one', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertIn('762A00-11300000/A', faster.answer)
        self.context = faster.context
        power = run_agent(self.connection, 'its power?', self.history, self.context,
                          model=Raising(AssertionError('LLM must not run')))
        self.assertIn('Motor power', power.answer)
        self.assertIn('762A00-11300000/A', power.answer)

    def test_delivery_question_is_one_limitation(self):
        result = run_agent(self.connection, 'what is the delivery time for 762A00-11320000/A?',
                           self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertEqual(result.answer.count('catalogue'), 1)
        self.assertIn('does not publish delivery times', result.answer)
