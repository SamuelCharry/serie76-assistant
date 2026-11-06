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


class PostDecisionBoundary(Base):
    """Injected faulty outputs must fail even when the route bypasses its checks."""

    def boundary(self, query, before, code, filters, route='ranked_pick'):
        from types import SimpleNamespace
        from backend.conversation.agent import AgentResult
        from backend.conversation.response_integrity import enforce
        row = get_actuator(self.connection, code)
        context = dict(filters=deepcopy(filters), on_screen=[code], focused_model=code)
        result = AgentResult('Catalogue specifications for ' + code if route == 'get_actuator'
                             else 'I recommend ' + code, products=[row], context=context)
        turn = SimpleNamespace(query=query, connection=self.connection,
                               trace=dict(name=route, context_before=deepcopy(before)))
        enforce(turn, result)
        return result

    def test_every_route_excludes_equal_reference_for_stronger_or_faster(self):
        code = '763A00-11330C00/A'
        filters = dict(service='on_off', enclosure='weatherproof', supply_voltage_v=220, frequency_hz=50)
        before = dict(filters=filters, focused_model=code, last_shown_list=[code])
        for route in ('ranked_pick', 'get_actuator', 'search_actuators', 'ask_clarification'):
            for operation, field, bound in [('stronger','min_torque_nm',(300.0,'gt')),
                                             ('faster','max_operating_time_s',(32.0,'lt'))]:
                with self.subTest(route=route, operation=operation):
                    for routed_filters in (filters, dict(filters, **{field:dict(value=bound[0],op=bound[1])})):
                        result = self.boundary(f'Is there a {operation} one than that at 50 Hz?', before, code, routed_filters, route)
                        self.assertFalse(result.products or result.recommendation)
                        self.assertNotIn('I recommend ' + code, result.answer)
                        self.assertEqual(canonical(field, result.context['filters'][field]), [bound])

    def test_wrong_ordinal_identity_is_rejected_even_for_equal_currents(self):
        first, second = '761A00-11320000/A', '761B00-11320000/A'
        before = dict(last_shown_list=[first,second], last_comparison_models=[first,second])
        for query in ('Second one. 50 Hz current?', 'Show current for the second model.',
                      'Current of the second actuator at 50 Hz, please.'):
            with self.subTest(query=query):
                result = self.boundary(query,before,first,{},'get_actuator')
                self.assertFalse(result.products)
                self.assertNotIn('focused_model',result.context)
                self.assertIn('requested displayed model',result.answer)

    def test_reference_measurement_is_not_hidden_or_converted_by_prior_bounds(self):
        code = '763A00-11330C00/A'
        for old in (dict(min_torque_nm=1000),dict(min_torque_in_lb=3000)):
            with self.subTest(old=old):
                filters = dict(service='on_off',enclosure='weatherproof',supply_voltage_v=220,**old)
                before = dict(filters=filters,focused_model=code,last_shown_list=[code])
                result = self.boundary('Is there a stronger one than that?',before,code,filters)
                self.assertFalse(result.products)
                self.assertEqual(canonical('min_torque_nm',result.context['filters']['min_torque_nm']),[(300.0,'gt')])

    def test_withdrawn_ceiling_and_its_number_cannot_reappear_at_output(self):
        first, second = '763A00-11320000/A','763B00-11320000/A'
        for ceiling in (900,1100,1800):
            filters = dict(service='on_off',enclosure='weatherproof',supply_voltage_v=220,phase_count=1,
                           min_torque_nm=[dict(value=300,op='gte'),dict(value=ceiling,op='lte')])
            before = dict(filters=filters,last_shown_list=[first,second])
            for relative in (False,True):
                with self.subTest(ceiling=ceiling,relative=relative):
                    query = (f'Find a stronger one than the second; removing the {ceiling} Nm ceiling.' if relative
                             else f'Remove the {ceiling} Nm ceiling.')
                    corrupted = dict(filters,min_torque_nm=[dict(value=ceiling,op='lte'),dict(value=ceiling,op='gte')])
                    result = self.boundary(query,before,'764B00-11320000/A',corrupted)
                    self.assertFalse(result.products or result.recommendation)
                    self.assertEqual(canonical('min_torque_nm',result.context['filters']['min_torque_nm']),
                                     [(500.0,'gt')] if relative else [(300.0,'gte')])
