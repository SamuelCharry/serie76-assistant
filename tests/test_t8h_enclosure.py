"""Unspecified enclosure must remain visible in recommendation and pick prose."""
from test_agent_scenarios import Base


class EnclosureTransparencyTests(Base):
    def test_recommendation_discloses_enclosure_once(self):
        result = self.turn('on/off 110 V at least 70 Nm',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                                 'min_torque_nm': 70}))
        self.assertEqual(result.answer.count('Enclosure not specified:'), 1)
        self.assertTrue(all(any(label in item['reason'] for label in ('Weatherproof', 'Explosionproof'))
                            for item in result.recommendation['items']))
        self.assertTrue(all(item['part_number'] + ': ' in result.answer for item in result.recommendation['items']))

    def test_pick_discloses_enclosure(self):
        self.turn('on/off 110 V at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                        'min_torque_nm': 70}))
        result = self.turn('pick one', ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(result.answer.count('Enclosure not specified:'), 1)
        self.assertTrue(any(label in result.answer for label in ('Weatherproof', 'Explosionproof')))

    def test_explicit_enclosure_has_no_disclosure(self):
        result = self.turn('explosionproof on/off 110 V',
                           ('search_actuators', {'enclosure': 'explosionproof',
                                                 'service': 'on_off', 'supply_voltage_v': 110}))
        self.assertNotIn('Enclosure not specified:', result.answer)
