"""Short follow ups and result counts use natural public text."""
from backend.conversation.agent import run_agent
from backend.conversation import quality
from backend.catalog.repository import get_actuator
from test_agent_scenarios import Base, Raising


class WordingTests(Base):
    def test_singular_count(self):
        text, *_ = quality.search_presentation({'total': 1, 'facets': {}},
                                                 [get_actuator(self.connection, '761A00-11300000/A')],
                                                 {'service': 'on_off'}, [], [])
        self.assertIn('1 actuator meets', text)

    def test_thanks_without_pending(self):
        result = run_agent(self.connection, 'thanks', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertTrue(result.answer.startswith("You're welcome."))

    def test_no_pending_go_uses_ranked_list(self):
        self.turn('on/off 110 V weatherproof',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                        'enclosure': 'weatherproof'}))
        self.context.pop('pending_questions', None)
        self.context.pop('pending_clarification', None)
        result = run_agent(self.connection, 'go', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertIn('My pick:', result.answer)

    def test_partial_code_lists_all_matches(self):
        result = self.turn('762A', ('get_actuator', {'part_numbers': ['762A']}))
        self.assertEqual(len(result.clarification.get('options', [])),
                         len(result.tool_calls[0]['data']['candidates']))
