"""Explicit negations remove carried filters even if a model repeats them."""
from test_agent_scenarios import Base


class NegationTests(Base):
    def test_forget_enclosure_normal_area(self):
        self.turn('explosionproof on/off 220 V',
                  ('search_actuators', {'enclosure': 'explosionproof', 'service': 'on_off',
                                        'supply_voltage_v': 220}))
        result = self.turn("forget explosionproof, it's a normal area",
                           ('search_actuators', {'enclosure': 'explosionproof'}))
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertEqual(int(result.context['filters']['supply_voltage_v']), 220)
        self.assertEqual(result.context['filters']['enclosure'], 'weatherproof')

    def test_any_voltage_removes_carried_voltage(self):
        self.turn('on/off 220 V', ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220}))
        result = self.turn('any voltage, it does not matter',
                           ('search_actuators', {'supply_voltage_v': 220}))
        self.assertNotIn('supply_voltage_v', result.context['filters'])
        self.assertEqual(result.context['filters']['service'], 'on_off')

    def test_drop_torque_removes_only_torque(self):
        self.turn('on/off 110 V at least 70 Nm',
                  ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 110,
                                        'min_torque_nm': 70}))
        result = self.turn('drop the torque requirement',
                           ('search_actuators', {'min_torque_nm': 70}))
        self.assertNotIn('min_torque_nm', result.context['filters'])
        self.assertEqual(result.context['filters']['service'], 'on_off')

