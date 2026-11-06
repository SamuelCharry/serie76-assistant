"""Held-out integrity failures with scripted interpretation and SQL rows."""
from test_agent_scenarios import Base


class IntegrityTests(Base):
    def test_only_torque_service_inside_both_bounds_is_shown(self):
        result = self.turn('Torque between 400 and 900 Nm, 220 V, explosionproof',
                           ('search_actuators', {'enclosure': 'explosionproof', 'supply_voltage_v': 220,
                                                 'min_torque_nm': [{'value': 400, 'op': 'gte'},
                                                                   {'value': 900, 'op': 'lte'}]}))
        candidate = next(item for item in result.recommendation['items']
                         if item['part_number'] == '764Y30-11320000/A')
        self.assertIn('Modulating torque 750 Nm', candidate['reason'])
        self.assertNotIn('On/Off torque 940 Nm', candidate['reason'])

    def test_fla_reason_names_published_frequency(self):
        result = self.turn('Weatherproof modulating 110 V, need 250 Nm minimum',
                           ('search_actuators', {'enclosure': 'weatherproof', 'service': 'modulating',
                                                 'supply_voltage_v': 110, 'min_torque_nm': 250}))
        for item in result.recommendation['items']:
            self.assertRegex(item['reason'], r'FLA (50|60) Hz [\d.]+ A')

    def test_onoff_spelling_is_applied_as_service(self):
        result = self.turn('onoff 24 V at least 50 Nm',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 24,
                                                 'min_torque_nm': 50}))
        self.assertEqual(result.context['filters']['service'], 'on_off')

    def test_solar_24v_supply_keeps_dc_and_acdc_models(self):
        result = self.turn('solar battery 24 V',
                           ('search_actuators', {'supply_voltage_v': 24}))
        self.assertEqual(result.context['filters']['supply_current'], 'DC')
        self.assertIn('Solar or battery supply is DC', result.answer)
        self.assertNotIn('supply_current', [q['id'] for q in (result.interaction or {}).get('questions', [])])
        from backend.catalog.repository import get_actuator
        currents = {get_actuator(self.connection, code)['supply_current'] for code in result.context['last_ranked_list']}
        self.assertIn('DC', currents)
        self.assertIn('AC/DC', currents)

    def test_impossible_enclosure_and_phase_does_not_show_weatherproof_as_match(self):
        result = self.turn('explosionproof 3 phase',
                           ('search_actuators', {'enclosure': 'explosionproof', 'phase_count': 3}))
        self.assertEqual(result.recommendation['total'], 0)
        self.assertIn('No actuator', result.answer)
        self.assertFalse(result.products)
