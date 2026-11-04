"""Unsupported named attributes cannot fall through to a full specification dump."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class ScopeTests(Base):
    def test_unknown_attributes_get_one_limitation(self):
        for query, noun in [
            ("what's the weight of 763A00-11320000/A?", 'weight'),
            ('can you send me the wiring diagram for 761A00-11300000/A?', 'wiring diagram'),
            ('is 761A00-11300000/A compatible with a 4-20 mA signal?', 'signal compatibility'),
        ]:
            with self.subTest(query=query):
                result = run_agent(self.connection, query, self.history, self.context,
                                   model=Raising(AssertionError('no LLM needed')))
                self.assertIn(noun, result.answer)
                self.assertIn("doesn't publish", result.answer)
                self.assertFalse(result.products)

    def test_catalogue_attribute_and_full_data_are_not_limited(self):
        for query in ('what is the torque of 761A00-11300000/A?',
                      '761A00-11300000/A full data'):
            result = self.turn(query, ('get_actuator', {'part_numbers': ['761A00-11300000/A']}))
            self.assertIn('761A00-11300000/A', result.answer)
            self.assertNotIn("doesn't publish", result.answer)
