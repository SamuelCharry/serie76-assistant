"""P2 diagnostic oracle: ideal decisions + real SQL; never provider inference."""
from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from test_agent_scenarios import Base
from backend.catalog.models import SearchFilters, bounds, bound_value, bound_operator
from backend.catalog.repository import get_actuator
from backend.conversation import integrity
from backend.conversation import requirement_coverage


class QuantityGrounding(unittest.TestCase):
    def test_all_catalogue_identifiers_are_never_physical_quantities(self):
        from scripts.acceptance_contract import catalogue
        for code in catalogue():
            for text in ('Current of ' + code, 'Motor power and FLA at 50 Hz for ' + code,
                         code + ' locked rotor amps and operating time'):
                with self.subTest(text=text):
                    quantities, issues = requirement_coverage.apply(text, {})
                    self.assertLessEqual(set(quantities), {'frequency_hz'})
                    self.assertFalse(issues)

    def test_numeric_arguments_cannot_license_their_own_missing_dimension(self):
        for value in (1, 24, 110, 220, 764):
            with self.subTest(value=value):
                rejected = requirement_coverage.unsupported(f'I need {value} V.',
                    dict(max_fla_a=value, max_motor_power_w=value), {})
                self.assertEqual(set(rejected), {'max_fla_a', 'max_motor_power_w'})

    def test_unitless_correction_requires_one_prior_dimension(self):
        self.assertEqual(requirement_coverage.apply('Make the minimum 750.', {}, {})[0], {})
        self.assertEqual(requirement_coverage.apply('Make the minimum 750.', {},
            dict(min_torque_nm=500, max_motor_power_w=100))[0], {})


CASES = json.loads((Path(__file__).resolve().parents[1] /
                   'config/agent_acceptance_cases_p2.json').read_text(encoding='utf-8'))


def canonical(field, value):
    if field.startswith(('min_', 'max_')):
        return sorted((float(bound_value(x)), bound_operator(x, 'gte' if field.startswith('min_') else 'lte'))
                      for x in bounds(value))
    if field in ('frequency_hz', 'supply_voltage_v'):
        return float(value)
    return value


class P2Oracle(Base):
    def test_range_addition_then_upper_withdrawal_retains_floor(self):
        self.turn('Find explosionproof 220 V single-phase on/off models at or above 800 Nm.',
            ('search_actuators', dict(service='on_off', enclosure='explosionproof', supply_voltage_v=220,
                phase_count=1, bounds=[dict(field='min_torque_nm',value=800,op='gte')])))
        added = self.turn('Apply an upper limit of 2000 Nm too.', ('search_actuators',dict(refine=True,
            bounds=[dict(field='min_torque_nm',value=800,op='gte'),dict(field='min_torque_nm',value=2000,op='lte')])))
        self.assertEqual(canonical('min_torque_nm', added.context['filters']['min_torque_nm']), [(800.0,'gte'),(2000.0,'lte')])
        removed = self.turn('Withdraw the upper limit; prioritize shortest operating time at 50 Hz.',
            ('search_actuators',dict(refine=True,priority=dict(metric='operating_time',direction='lowest',frequency_hz=50))))
        self.assertEqual(canonical('min_torque_nm', removed.context['filters']['min_torque_nm']), [(800.0,'gte')])

    def check_case(self, scenario):
        self.context = deepcopy(scenario.get('context', {}))
        self.history = deepcopy(scenario.get('history', []))
        for turn in scenario['turns']:
            decision = turn.get('scripted_decision')
            result = self.turn(turn['query'], *([tuple(decision)] if decision else []))
            expected = turn.get('expect', {}).get('p2', {})
            filters = result.context.get('filters', {})
            for field, value in expected.get('filters', {}).items():
                self.assertIn(field, filters, result.answer)
                self.assertEqual(canonical(field, filters[field]), canonical(field, value), result.answer)
            for field in expected.get('absent_filters', []):
                self.assertNotIn(field, filters, result.answer)
            for pattern in expected.get('text', []):
                self.assertRegex(result.answer.lower(), pattern.lower())
            for pattern in expected.get('not_text', []):
                self.assertIsNone(re.search(pattern, result.answer, re.I), result.answer)
            cards = [p['base_part_number'] for p in result.products]
            rec = result.recommendation or {}
            ranked = [item['part_number'] for item in rec.get('items', [])]
            visible = set(cards + ranked + (result.comparison or {}).get('models', []))
            if 'visible_count' in expected:
                self.assertEqual(len(visible), expected['visible_count'], result.answer)
            if expected.get('aligned'):
                self.assertTrue(ranked, result.answer)
                if cards:
                    self.assertEqual(cards, ranked, result.answer)
                self.assertEqual(result.context.get('on_screen'), ranked)
            if 'comparison' in expected:
                self.assertEqual((result.comparison or {}).get('models'), expected['comparison'], result.answer)
            if 'focused' in expected:
                self.assertEqual(result.context.get('focused_model'), expected['focused'], result.answer)
            if 'first' in expected:
                self.assertEqual(ranked[:1], [expected['first']], result.answer)
            if expected.get('alternatives'):
                self.assertEqual(rec.get('total'), 0)
                self.assertFalse(ranked, result.answer)
                alternatives = result.context.get('zero_result_nearest', [])
                self.assertTrue(alternatives, result.answer)
                for item in alternatives:
                    self.assertIn(item['part_number'], result.answer)
                    self.assertIn('Does not meet', item['reason'])
            if 'eligible' in expected:
                scope = SearchFilters.model_validate(expected['eligible'])
                self.assertTrue(visible, result.answer)
                for code in visible:
                    self.assertTrue(integrity.satisfies(get_actuator(self.connection, code), scope), result.answer)
            if expected.get('no_positive_selection'):
                self.assertFalse(cards or (ranked if rec.get('total', 0) else []), result.answer)


for case in CASES['scenarios']:
    def check(self, scenario=case):
        self.check_case(scenario)
    setattr(P2Oracle, 'test_' + case['id'], check)
