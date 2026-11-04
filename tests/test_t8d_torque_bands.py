"""Torque choices must be feasible SQL-backed reductions, not guessed ranges."""
from test_agent_scenarios import Base
from backend.conversation.agent import run_agent


class TorqueBandTests(Base):
    def test_torque_bands_when_categories_are_known(self):
        result = self.turn('On/Off, 110 V, Weatherproof', ('search_actuators', {
            'service': 'on_off', 'supply_voltage_v': 110, 'enclosure': 'weatherproof'}))
        questions = (result.interaction or {}).get('questions', [])
        self.assertEqual([q['id'] for q in questions], ['min_torque_nm'])
        self.assertTrue(all(0 < o['count'] < result.recommendation['total'] for o in questions[0]['options']))
        self.assertTrue(all('Nm' in o['label'] for o in questions[0]['options']))

    def test_no_torque_question_when_threshold_given(self):
        result = self.turn('On/Off, 110 V, Weatherproof, at least 70 Nm', ('search_actuators', {
            'service': 'on_off', 'supply_voltage_v': 110, 'enclosure': 'weatherproof', 'min_torque_nm': 70}))
        self.assertNotIn('min_torque_nm', [q['id'] for q in (result.interaction or {}).get('questions', [])])

    def test_torque_band_can_be_submitted(self):
        first = self.turn('On/Off, 110 V, Weatherproof', ('search_actuators', {
            'service': 'on_off', 'supply_voltage_v': 110, 'enclosure': 'weatherproof'}))
        option = first.interaction['questions'][0]['options'][0]
        second = run_agent(self.connection, 'that torque', self.history, self.context,
                           answers={'min_torque_nm': option['value']})
        self.assertEqual(second.context['filters']['min_torque_nm'], option['value'])
        self.assertEqual(second.recommendation['total'], option['count'])
