"""Numeric requirements cannot disappear between interpretation and SQL."""
import random
import unittest
from backend.conversation import requirement_coverage
from test_agent_scenarios import Base


class QuantityPropertyTests(unittest.TestCase):
    def test_random_clear_quantities_are_applied_or_disclosed(self):
        generator = random.Random(76)
        templates = [
            ('at least {} Nm', 'min_torque_nm'), ('at most {}Nm', 'min_torque_nm'),
            ('{} V', 'supply_voltage_v'), ('{} Hz', 'frequency_hz'),
            ('max motor power {} W', 'max_motor_power_w'),
        ]
        for _ in range(80):
            number = generator.randint(1, 9000)
            pattern, field = generator.choice(templates)
            text = pattern.format(number)
            applied, disclosures = requirement_coverage.apply(text, {})
            self.assertTrue(field in applied or disclosures, text)

    def test_range_and_approximation(self):
        applied, issues = requirement_coverage.apply('modulating torque 300 to 700 Nm', {})
        self.assertEqual(applied['min_torque_nm'],
                         [{'value': 300, 'op': 'gte'}, {'value': 700, 'op': 'lte'}])
        self.assertEqual(issues, [])
        applied, issues = requirement_coverage.apply('about 400Nm', {})
        self.assertEqual(applied['min_torque_nm'], 400)
        self.assertEqual(issues, [])

    def test_unmapped_measurement_is_disclosed(self):
        applied, issues = requirement_coverage.apply('needs 20 A', {})
        self.assertNotIn('max_fla_a', applied)
        self.assertIn('20 A', issues[0])

    def test_unit_typo_is_applied_or_disclosed(self):
        for phrase in ('500nmm', '60hzz', '220vv'):
            with self.subTest(phrase=phrase):
                applied, issues = requirement_coverage.apply(phrase, {})
                self.assertTrue(applied or issues)


class CoverageScenarios(Base):
    def test_search_recovers_dropped_torque_and_range(self):
        result = self.turn('Modulating 110 V torque 300 to 700 Nm',
                           ('search_actuators', {'service': 'modulating',
                                                 'supply_voltage_v': 110,
                                                 'min_torque_nm': 300}))
        self.assertEqual(result.context['filters']['min_torque_nm'],
                         [{'value': 300, 'op': 'gte'}, {'value': 700, 'op': 'lte'}])
        self.assertTrue(all('torque' in item['reason'].lower() for item in result.recommendation['items']))

    def test_no_space_torque_is_applied(self):
        result = self.turn('explosionprooff 220v onof 500nm',
                           ('search_actuators', {'enclosure': 'explosionproof',
                                                 'supply_voltage_v': 220}))
        self.assertIn('min_torque_nm', result.context['filters'])
        self.assertEqual(result.context['filters']['min_torque_nm'], 500)

    def test_about_torque_is_a_minimum(self):
        result = self.turn('open and close only, 220 V, about 400 Nm',
                           ('search_actuators', {'service': 'on_off', 'supply_voltage_v': 220}))
        self.assertEqual(result.context['filters']['min_torque_nm'], 400)
