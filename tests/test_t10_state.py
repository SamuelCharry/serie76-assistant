"""State deltas: scripted interpretation, CSV-derived catalogue fixtures, no inference.

Numbers in parser unit tests are hypothetical user inputs, not catalogue claims.
Integration thresholds and supply values are read from the validated CSV.
"""
import csv
from decimal import Decimal
from pathlib import Path
import unittest

from backend.catalog.models import bound_operator, bound_value, bounds
from backend.conversation import policy, requirement_coverage
from test_agent_scenarios import Base


def limits(value, field='min_torque_nm'):
    return {(Decimal(str(bound_value(b))), bound_operator(b, 'gte' if field.startswith('min_') else 'lte'))
            for b in bounds(value)}


class StateDeltaTests(unittest.TestCase):
    def test_corrections_replace_all_bounds_of_only_the_stated_field(self):
        previous = {'min_torque_nm': [{'value': 31, 'op': 'gte'}, {'value': 87, 'op': 'lte'}],
                    'max_motor_power_w': {'value': 19, 'op': 'lte'}, 'service': 'modulating'}
        for query in ('I meant at most 43 Nm.', 'Actually, a maximum of 43 Nm.',
                      'Instead use 43 Nm maximum.', 'No, sorry: up to 43 Nm.',
                      'Rather, no more than 43 Nm.', 'Quise decir como máximo 43 Nm.',
                      'Rectifico: máximo 43 Nm.', 'Reverse that torque limit: at most 43 Nm.'):
            with self.subTest(query=query):
                delta, issues = requirement_coverage.apply(query, {})
                merged, _ = policy.merge_filters(previous, delta, refine=True, remove=[], more=False, query=query)
                self.assertEqual(issues, [])
                self.assertEqual(limits(merged['min_torque_nm']), {(Decimal(43), 'lte')})
                self.assertEqual(merged['max_motor_power_w'], previous['max_motor_power_w'])
                self.assertEqual(merged['service'], 'modulating')

    def test_added_upper_bounds_keep_the_lower_bound(self):
        for query in ('Also set the upper torque limit to 83 in-lb.',
                      'Keep the minimum and add an 83 in-lb maximum.',
                      'Conserva el mínimo y agrega un máximo de 83 in-lb.'):
            with self.subTest(query=query):
                delta, _ = requirement_coverage.apply(query, {})
                merged, _ = policy.merge_filters({'min_torque_in_lb': 37}, delta,
                                                 refine=True, remove=[], more=False, query=query)
                self.assertEqual(limits(merged['min_torque_in_lb']), {(Decimal(37), 'gte'), (Decimal(83), 'lte')})

    def test_correction_does_not_spill_into_an_addition_clause(self):
        query = 'Actually at most 43 Nm; add a maximum of 29 W'
        delta, _ = requirement_coverage.apply(query, {})
        self.assertEqual(policy.replaced_fields(query, delta), {'min_torque_nm'})
        merged, _ = policy.merge_filters({'min_torque_nm': 31, 'max_motor_power_w': {'value': 11, 'op': 'gte'}},
                                         delta, refine=True, remove=[], more=False, query=query)
        self.assertEqual(limits(merged['max_motor_power_w'], 'max_motor_power_w'), {(Decimal(11), 'gte'), (Decimal(29), 'lte')})

    def test_numeric_operators_are_nearest_and_dimension_scoped(self):
        for query, op in (('at least 43 Nm', 'gte'), ('no less than 43 Nm', 'gte'),
                          ('al menos 43 Nm', 'gte'), ('más de 43 Nm', 'gt'),
                          ('menos de 43 Nm', 'lt'), ('≤ 43 Nm', 'lte'),
                          ('>=43 Nm', 'gte'), ('hasta 43 Nm', 'lte')):
            with self.subTest(query=query):
                delta, _ = requirement_coverage.apply(query, {})
                self.assertEqual(limits(delta['min_torque_nm']), {(Decimal(43), op)})
        delta, _ = requirement_coverage.apply('at least 31 Nm and no more than 83 Nm, below 19 W', {})
        self.assertEqual(limits(delta['min_torque_nm']), {(Decimal(31), 'gte'), (Decimal(83), 'lte')})
        self.assertEqual(limits(delta['max_motor_power_w']), {(Decimal(19), 'lt')})
        self.assertEqual(requirement_coverage.unsupported('43 V', {'max_motor_power_w': 43}), ['max_motor_power_w'])

    def test_removal_and_clear_phrases(self):
        for query in ('Drop the phase requirement', 'Forget the three-phase constraint',
                      'Without a phase requirement', 'Sin requisito de fases',
                      'Ya no necesito tres fases', 'Elimina el requisito trifásico',
                      'The phase requirement is no longer needed'):
            with self.subTest(query=query):
                self.assertIn('phase_count', policy.removed_fields(query))
        for query in ('Clear all filters', 'Forget every requirement', 'Elimina todas las restricciones'):
            self.assertEqual(policy.removed_fields(query), set(policy.FILTER_FIELDS))
        for query in ('no more than 43 Nm torque', 'not more than 43 Nm torque', 'no más de 43 Nm torque'):
            self.assertNotIn('min_torque_nm', policy.removed_fields(query))

    def test_hazard_clearance_and_positive_presence_are_distinct(self):
        for query in ('No fuel is stored here', 'It is an ordinary room',
                      'It is not hazardous after all', 'Sin materiales inflamables',
                      'La zona es normal; sin gas', 'There is no flammable gas'):
            with self.subTest(query=query):
                self.assertTrue(policy.nonhazard_signal(query))
                self.assertFalse(policy.hazard_signal(query))
                self.assertEqual(policy.colloquial_requirements(query)[0]['enclosure'], 'weatherproof')
        for query in ('Beside a paint booth', 'Near a spray booth', 'Al lado de una cabina de pintura',
                      'No gas, but solvent storage nearby', 'No gas but solvent storage nearby',
                      'An ordinary room beside a paint booth'):
            with self.subTest(query=query):
                self.assertFalse(policy.nonhazard_signal(query))
                self.assertTrue(policy.hazard_signal(query))

    def test_affirmed_values_win_over_negated_alternatives(self):
        for query, field in (
            ('show me any DC actuator with 300 in-lb', 'supply_current'),
            ('I need DC, not AC', 'supply_current'),
            ('no AC please, only DC', 'supply_current'),
            ('any 24 V model for on/off', 'supply_voltage_v'),
            ('necesito DC, no AC', 'supply_current'),
            ('cualquier modelo de 24 V', 'supply_voltage_v'),
            ('Drop the current requirement but use DC', 'supply_current'),
            ('No 220 V, use 24 V', 'supply_voltage_v'),
            ('Single phase, not three phase', 'phase_count'),
            ('Not explosionproof, only weatherproof', 'enclosure'),
            ('modulating rather than on/off', 'service'),
        ):
            with self.subTest(query=query):
                self.assertNotIn(field, policy.removed_fields(query))

    def test_removal_requires_no_affirmed_value_for_that_field(self):
        for query, field in (
            ('drop the current requirement', 'supply_current'),
            ('any voltage is fine', 'supply_voltage_v'),
            ('forget the phase', 'phase_count'),
            ('cualquier voltaje sirve', 'supply_voltage_v'),
            ('ya no necesito corriente AC', 'supply_current'),
            ('No AC please', 'supply_current'),
            ('The three phase requirement is no longer needed', 'phase_count'),
        ):
            with self.subTest(query=query):
                self.assertIn(field, policy.removed_fields(query))

    def test_grounding_accepts_language_variants_and_bounded_typos(self):
        examples = (
            ('supply_current', 'AC/DC', ('both AC and DC', 'AC y DC', 'corriente alterna y continua',
                                        'AC & DC', 'alternating current and direct current', 'DC as well as AC')),
            ('service', 'on_off', ('abra y cierre', 'abrir o cerrar', 'apertura y cierre')),
            ('service', 'modulating', ('modulante', 'modulación', 'modulatin')),
            ('enclosure', 'weatherproof', ('en el exterior', 'a la intemperie', 'weatherproff')),
            ('enclosure', 'explosionproof', ('a prueba de explosión', 'explosionproff', 'explosion-proof')),
        )
        for field, value, phrases in examples:
            for phrase in phrases:
                with self.subTest(phrase=phrase):
                    self.assertEqual(policy.grounding_errors({field: value}, [], [phrase]), [])
        self.assertEqual(policy.grounding_errors({'supply_current': 'AC/DC'}, [], ['AC only']), ['supply_current'])
        self.assertEqual(policy.grounding_errors({'enclosure': 'weatherproof'}, [], ['an indoor unit']), ['enclosure'])

    def test_assumptions_must_still_quote_actual_user_words(self):
        for query in ('abra y cierre', 'abrir o cerrar', 'apertura y cierre'):
            quoted = {'field': 'service', 'user_phrase': query.upper().replace(' ', '  ')}
            self.assertEqual(policy.invalid_assumptions([quoted], [query]), [])
            self.assertEqual(policy.grounding_errors({'service': 'on_off'}, [quoted], [query]), [])
            invented = {'field': 'enclosure', 'user_phrase': 'safe area'}
            self.assertEqual(policy.invalid_assumptions([invented], [query]), [invented])


class StateDeltaScenarios(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with (Path(__file__).resolve().parents[1] / 'data/extracted/series76/catalog.csv').open(newline='', encoding='utf-8-sig') as stream:
            cls.catalogue = list(csv.DictReader(stream))
        cls.torques = sorted({Decimal(row['modulating_torque_nm']) for row in cls.catalogue if row['modulating_torque_nm']})

    def reset_context(self):
        self.context, self.history = {}, []

    def test_correction_updates_both_filters_and_quantity_ledger(self):
        threshold = float(self.torques[1])
        for phrase in ('Actually at most {n} Nm', 'Quise decir máximo {n} Nm', 'Instead use {n} Nm maximum',
                       'No sorry: maximum torque {n} Nm'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                self.turn(f'modulating at least {threshold} Nm', ('search_actuators', {'service': 'modulating'}))
                result = self.turn(phrase.format(n=threshold), ('search_actuators', {'refine': True}))
                expected = {(Decimal(str(threshold)), 'lte')}
                self.assertEqual(limits(result.context['filters']['min_torque_nm']), expected)
                self.assertEqual(limits(result.context['quantity_requirements']['min_torque_nm']), expected)
                self.assertEqual(result.context['filters']['service'], 'modulating')
                self.assertNotIn('unrepresented_quantity', str(result.tool_calls))

    def test_addition_keeps_a_range_through_search(self):
        lower, upper = map(float, (self.torques[0], self.torques[2]))
        for phrase in ('Also add a maximum of {n} Nm', 'Keep the minimum and add {n} Nm maximum',
                       'Conserva el mínimo y agrega máximo {n} Nm'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                self.turn(f'modulating at least {lower} Nm', ('search_actuators', {'service': 'modulating'}))
                result = self.turn(phrase.format(n=upper), ('search_actuators', {'refine': True}))
                expected = {(Decimal(str(lower)), 'gte'), (Decimal(str(upper)), 'lte')}
                self.assertEqual(limits(result.context['filters']['min_torque_nm']), expected)
                self.assertEqual(limits(result.context['quantity_requirements']['min_torque_nm']), expected)

    def test_removal_suppresses_the_removed_question(self):
        for phrase in ('Drop my phase requirement', 'Without a phase constraint', 'Ya no necesito tres fases'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                self.turn('three-phase AC on/off', ('search_actuators', {'phase_count': 3, 'supply_current': 'AC', 'service': 'on_off'}))
                result = self.turn(phrase, ('search_actuators', {'refine': True}))
                self.assertNotIn('phase_count', result.context['filters'])
                self.assertNotIn('phase_count', [q['id'] for q in (result.interaction or {}).get('questions', [])])

    def test_clearance_removes_hazard_and_does_not_ask_enclosure_again(self):
        for phrase in ('No fuel stored here; regular enclosure is acceptable',
                       'It is an ordinary room', 'Sin materiales inflamables'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                self.turn('on/off near solvent storage', ('search_actuators', {'service': 'on_off'}))
                self.assertTrue(self.context.get('hazard_signal'))
                result = self.turn(phrase, ('search_actuators', {'refine': True}))
                self.assertFalse(result.context.get('hazard_signal'))
                self.assertEqual(result.context['filters'].get('enclosure'), 'weatherproof')
                self.assertNotIn('enclosure', [q['id'] for q in (result.interaction or {}).get('questions', [])])

    def test_paint_sites_keep_confirmation_and_explosionproof_previews(self):
        enclosures = {row['base_part_number']: row['enclosure'] for row in self.catalogue}
        for phrase in ('near a paint booth', 'beside a spray booth', 'junto a una cabina de pintura'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                result = self.turn('on/off ' + phrase, ('search_actuators', {'service': 'on_off'}))
                self.assertTrue(result.context.get('hazard_signal'))
                self.assertIn('enclosure', [q['id'] for q in (result.interaction or {}).get('questions', [])])
                for item in (result.recommendation or {}).get('items', []):
                    self.assertEqual(enclosures[item['part_number']], 'explosionproof')

    def test_dual_current_and_spanish_grounding_survive_search(self):
        for phrase in ('both AC and DC', 'AC y DC', 'corriente alterna y continua'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                result = self.turn('on/off ' + phrase, ('search_actuators', {'service': 'on_off', 'supply_current': 'AC/DC'}))
                self.assertEqual(result.context['filters'].get('supply_current'), 'AC/DC')
        for phrase in ('abra y cierre en el exterior', 'abrir o cerrar a la intemperie', 'apertura y cierre en exteriores'):
            with self.subTest(phrase=phrase):
                self.reset_context()
                result = self.turn(phrase, ('search_actuators', {'service': 'on_off', 'enclosure': 'weatherproof'}))
                self.assertEqual(result.context['filters'].get('service'), 'on_off')
                self.assertEqual(result.context['filters'].get('enclosure'), 'weatherproof')

    def test_affirmed_current_and_voltage_are_not_popped_after_merge(self):
        voltage = int(next(row['supply_voltage_v'] for row in self.catalogue if row['supply_current'] == 'AC/DC'))
        torque = next(row['on_off_torque_in_lb'] for row in self.catalogue if row['supply_current'] == 'AC/DC' and row['on_off_torque_in_lb'])
        for query in (f'show me any DC actuator with {torque} in-lb', 'I need DC, not AC',
                      'no AC please, only DC', 'necesito DC, no AC', 'DC rather than AC'):
            with self.subTest(query=query):
                self.reset_context()
                result = self.turn(query, ('search_actuators', {'supply_current': 'DC'}))
                self.assertEqual(result.context['filters'].get('supply_current'), 'DC')
                self.assertIn('supply_current', [item['field'] for item in result.active_filters])
        for query in (f'any {voltage} V model for on/off', f'cualquier modelo de {voltage} V',
                      f'Any actuator using {voltage} V'):
            with self.subTest(query=query):
                self.reset_context()
                result = self.turn(query, ('search_actuators', {'supply_voltage_v': voltage}))
                self.assertEqual(result.context['filters'].get('supply_voltage_v'), voltage)
