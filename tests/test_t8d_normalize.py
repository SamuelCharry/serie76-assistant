"""Explicit colloquial requirements survive model argument omissions."""
from backend.conversation.agent import run_agent
from test_agent_scenarios import Base, Raising


class NormalizeTests(Base):
    def test_spanish_phase_and_torque(self):
        result = self.turn('min torque 1.2kNm, 3 fases', ('search_actuators', {}))
        self.assertEqual(result.context['filters']['phase_count'], 3)
        self.assertEqual(result.context['filters']['min_torque_nm'], 1200)

    def test_que_module_exteriores(self):
        result = self.turn('busco uno para exteriores, 110v, que module',
                           ('search_actuators', {'supply_voltage_v': 110}))
        self.assertEqual(result.context['filters']['service'], 'modulating')
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')
        self.assertFalse(result.interaction and any(q['id'] == 'enclosure' for q in result.interaction['questions']))

    def test_partial_open_means_modulating(self):
        result = self.turn('hold a valve at 30% open', ('search_actuators', {}))
        self.assertEqual(result.context['filters']['service'], 'modulating')

    def test_mine_shaft_asks_and_explicit_yes_applies(self):
        first = self.turn('mine shaft ventilation damper, 220 V',
                          ('search_actuators', {'supply_voltage_v': 220}))
        self.assertIn('enclosure', [q['id'] for q in first.interaction['questions']])
        self.assertNotIn('enclosure', first.context['filters'])
        answer = run_agent(self.connection, "yes it's a hazardous area", self.history, first.context,
                           model=Raising(AssertionError('no LLM needed')))
        self.assertEqual(answer.context['filters']['enclosure'], 'explosionproof')

    def test_explicit_hazard_applies_without_confirmation(self):
        result = self.turn('the area is classified as hazardous because of methane',
                           ('search_actuators', {}))
        self.assertEqual(result.context['filters']['enclosure'], 'explosionproof')
