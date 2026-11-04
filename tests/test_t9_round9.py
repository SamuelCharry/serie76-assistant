"""Round-nine deterministic regressions; scripted decisions and real PostgreSQL only."""
from backend.conversation import requirement_coverage, policy
from test_agent_scenarios import Base
import unittest


class NumericEvidenceTests(unittest.TestCase):
    def test_wp_is_not_a_watt_unit_typo(self):
        applied, issues = requirement_coverage.apply('onoff 220 wp 500nm', {})
        self.assertNotIn('max_motor_power_w', applied)
        self.assertEqual(applied['supply_voltage_v'], 220)
        self.assertEqual(issues, [])

    def test_reverse_coverage_rejects_cross_unit_and_unitless_numbers(self):
        for field in policy.NUMERIC_FIELDS:
            if field == 'supply_voltage_v':
                continue
            with self.subTest(field=field):
                self.assertIn(field, requirement_coverage.unsupported('220 V', {field: 220}))
                self.assertIn(field, requirement_coverage.unsupported('220', {field: 220}))
        self.assertEqual(requirement_coverage.unsupported('220', {'supply_voltage_v': 220}), [])
        self.assertEqual(requirement_coverage.unsupported('230', {'supply_voltage_v': 230}), ['supply_voltage_v'])

    def test_opposite_bounds_combine_same_direction_replaces(self):
        previous = {'min_torque_nm': 200}
        merged, _ = policy.merge_filters(previous, {'min_torque_nm': {'value': 400, 'op': 'lte'}},
                                          refine=True, remove=[], more=False)
        self.assertEqual(merged['min_torque_nm'], [{'value': 200, 'op': 'gte'}, {'value': 400, 'op': 'lte'}])
        merged, _ = policy.merge_filters(merged, {'min_torque_nm': 250}, refine=True, remove=[], more=False)
        self.assertEqual(merged['min_torque_nm'], [{'value': 400, 'op': 'lte'}, {'value': 250, 'op': 'gte'}])


class RoundNineScenarios(Base):
    def test_safe_correction_runs_without_model(self):
        self.turn('Explosionproof on/off 220 V', ('search_actuators', {}))
        result = self.turn('actually the area is safe, no gas', None)
        self.assertEqual(result.context['filters'].get('enclosure'), 'weatherproof')
        self.assertFalse(result.context.get('hazard_signal'))
        self.assertFalse(result.tool_calls[0]['model'].get('llm_called', True))

    def test_fuel_and_paint_context_requires_hazard_confirmation(self):
        for query in ['paint mixing room, modulating, 110 V',
                      'deposito de gasolina, on/off 220 V',
                      'valve beside a diesel generator fuel tank, 110 V, open/close']:
            with self.subTest(query=query):
                self.history, self.context = [], {}
                result = self.turn(query, ('search_actuators', {}))
                self.assertTrue(result.context.get('hazard_signal'))
                self.assertEqual(result.context.get('proposed_enclosure'), 'explosionproof')
                self.assertIn('enclosure', [q['id'] for q in result.interaction['questions']])
                self.assertTrue(all(item['part_number'][3] in 'XY' for item in result.recommendation['items']))

    def test_generator_question_remains_a_limitation(self):
        result = self.turn('Can it operate from a diesel generator?', None)
        self.assertIn('generator operation', result.answer)

    def test_deterministic_service_paraphrases(self):
        for query, service in [('it just opens or shuts, 220 V', 'on_off'),
                               ('dose steam gradually, 220 V', 'modulating')]:
            self.history, self.context = [], {}
            result = self.turn(query, ('search_actuators', {}))
            self.assertEqual(result.context['filters'].get('service'), service)

    def test_no_invented_power_from_220_wp(self):
        result = self.turn('onoff 220 wp 500nm', ('search_actuators', {
            'supply_voltage_v': 220, 'max_motor_power_w': 220, 'min_torque_nm': 500}))
        self.assertNotIn('max_motor_power_w', result.context['filters'])
        self.assertEqual(float(result.context['filters']['supply_voltage_v']), 220)

    def test_followup_ceiling_keeps_floor_and_four_matches(self):
        self.turn('at least 200 Nm on/off 220 V', ('search_actuators', {}))
        result = self.turn('and no more than 400 Nm', ('search_actuators', {'refine': True}))
        self.assertEqual(result.recommendation['total'], 4)
        self.assertEqual(result.context['quantity_requirements']['min_torque_nm'],
                         [{'value': 200, 'op': 'gte'}, {'value': 400, 'op': 'lte'}])
