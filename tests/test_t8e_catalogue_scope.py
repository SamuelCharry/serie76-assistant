"""Catalogue-wide questions and unknown properties have concise grounded answers."""
from test_agent_scenarios import Base


class CatalogueScopeTests(Base):
    def test_voltage_list_comes_from_sql_with_counts(self):
        result = self.turn('what voltages do you have?', ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('24 V', result.answer)
        self.assertIn('110 V', result.answer)
        self.assertIn('220 V', result.answer)
        self.assertNotIn('What would you like to check?', result.answer)

    def test_unpublished_topic_uses_clean_noun_phrase(self):
        cases = [
            ('how long does 762A00-11320000/A last before maintenance?', 'maintenance interval'),
            ('give me the CAD drawing of 763A00-11300000/A', 'CAD drawing'),
            ('what is the IP rating of 761X30-11320000/A?', 'IP rating'),
            ('can these run on a generator?', 'generator operation'),
        ]
        for query, noun in cases:
            with self.subTest(query=query):
                result = self.turn(query, ('get_actuator', {'part_numbers': []}))
                self.assertIn(noun, result.answer)
                self.assertNotIn('Comparing ', result.answer)
                self.assertFalse(result.products)

    def test_competitor_comparison_stays_in_scope(self):
        result = self.turn('which is better, Series 76 or Bray actuators?',
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('I only cover the Series 76 catalogue', result.answer)

    def test_what_restates_pending_question_without_list(self):
        self.turn('I need an on/off actuator', ('search_actuators', {'service': 'on_off'}))
        result = self.turn('what?', ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('Which', result.answer)
        self.assertNotIn('Ranked by', result.answer)

    def test_vague_answer_names_the_questions_it_shows(self):
        result = self.turn('I need an actuator', ('search_actuators', {}))
        ids = [q['id'] for q in result.interaction['questions']]
        self.assertEqual(ids, ['supply_voltage_v', 'enclosure'])
        self.assertIn('supply voltage and enclosure', result.answer)
