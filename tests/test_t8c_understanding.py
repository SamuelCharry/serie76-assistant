"""Normalized requirements and published enclosure confirmation."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class UnderstandingTests(Base):
    def test_flow_precisely_means_modulating(self):
        result = self.turn('I need to control the flow precisely at 220 V',
                           ('search_actuators', {'supply_voltage_v': 220}))
        self.assertEqual(result.context['filters']['service'], 'modulating')

    def test_fuzzy_enclosure_token_is_stated_and_filtered(self):
        result = self.turn('explsionproof 220 V',
                           ('search_actuators', {'supply_voltage_v': 220}))
        self.assertEqual(result.context['filters']['enclosure'], 'explosionproof')
        self.assertIn("Interpreted 'explsionproof' as Explosionproof.", result.answer)

    def test_explosive_vapours_asks_confirmation(self):
        result = self.turn('something for explosive vapours',
                           ('search_actuators', {}))
        self.assertEqual(result.interaction['questions'][0]['id'], 'enclosure')
        self.assertNotIn('enclosure', result.context['filters'])

    def test_petrochemical_site_asks_confirmation(self):
        result = self.turn('for a petrochemical plant', ('search_actuators', {}))
        self.assertEqual(result.interaction['questions'][0]['id'], 'enclosure')

    def test_outdoors_not_hazardous_answers_pending_enclosure(self):
        first = self.turn('we have a refinery', ('search_actuators', {}))
        result = run_agent(self.connection, "no, it's outdoors, not hazardous", self.history, first.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_voltage_sibling_keeps_frame_code(self):
        self.turn('Show 761B00-11300000/A',
                  ('get_actuator', {'part_numbers': ['761B00-11300000/A']}))
        result = self.turn('the 220 V version',
                           ('get_actuator', {'reference_kind': 'focused', 'equivalent_voltage_v': 220}))
        self.assertIn('761B00-11320000/A', result.answer)
        self.assertNotIn('torque ≥', result.answer)

    def test_explosionproof_equivalent_lists_same_size_candidates(self):
        self.turn('Show 763B00-11320000/A',
                  ('get_actuator', {'part_numbers': ['763B00-11320000/A']}))
        result = self.turn('the explosionproof equivalent',
                           ('get_actuator', {'reference_kind': 'focused',
                                             'equivalent_enclosure': 'explosionproof'}))
        self.assertIn('763X30-11320000/A', result.answer)
        self.assertIn('763Y30-11320000/A', result.answer)
