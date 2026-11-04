"""Categorical impossibility explains SQL alternatives and preserves new limits."""
from test_agent_scenarios import Base


class ImpossibleTests(Base):
    def test_weatherproof_24v_has_two_relaxations(self):
        result = self.turn('weatherproof 24 V',
                           ('search_actuators', {'enclosure': 'weatherproof', 'supply_voltage_v': 24}))
        self.assertEqual(result.recommendation['total'], 0)
        self.assertIn('24 V models are only Explosionproof', result.answer)
        self.assertIn('Explosionproof at 24 V', result.suggested_replies)
        self.assertTrue(any('Weatherproof at ' in x for x in result.suggested_replies))

    def test_new_torque_constraint_survives_empty_followup(self):
        self.turn('weatherproof 24 V',
                  ('search_actuators', {'enclosure': 'weatherproof', 'supply_voltage_v': 24}))
        result = self.turn('and modulating at least 100 Nm',
                           ('search_actuators', {'refine': True, 'service': 'modulating'}))
        self.assertEqual(result.context['filters']['min_torque_nm'], 100)
        self.assertIn('100 Nm', result.answer)
