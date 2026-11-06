"""Execution-route regressions: CSV/SQL facts, scripted decisions, no inference."""
from decimal import Decimal
import unittest
from unittest.mock import patch

from backend.catalog.models import SearchFilters
from backend.catalog.repository import get_actuator, search_actuators
from backend.conversation import agent, catalogue_answers, integrity, policy, ranking
from scripts.acceptance_contract import catalogue
from test_agent_scenarios import Base


class ProjectionTests(unittest.TestCase):
    def test_removed_and_null_assumptions_for_every_field(self):
        for field in policy.FILTER_FIELDS:
            with self.subTest(field=field):
                assumptions = [dict(field=field, user_phrase='stated requirement')]
                self.assertEqual(agent.project_assumptions(assumptions, {}), [])
                self.assertEqual(agent.project_assumptions(assumptions, {field: None}), [])
        self.assertEqual(agent.project_assumptions([dict(field='csa_required', user_phrase='not required')],
                                                  {'csa_required': False}), [])

    def test_meaningful_values_for_every_field_type(self):
        values = dict(enclosure='weatherproof', service='on_off', supply_current='AC', phase_count=1,
                      csa_required=True, supply_voltage_v=1, frequency_hz=50)
        values.update({field: 0 for field in policy.NUMERIC_FIELDS if field not in values})
        for field, value in values.items():
            with self.subTest(field=field, value=value):
                shown = agent.project_assumptions([dict(field=field, user_phrase='stated requirement')], {field: value})
                self.assertEqual(shown[0]['value'], value)
                self.assertTrue(policy.describe({field: shown[0]['value']}))
        for value in ({'value': 0, 'op': 'gte'}, [{'value': 0, 'op': 'gte'}, {'value': 1, 'op': 'lt'}]):
            self.assertTrue(agent.project_assumptions([dict(field='min_torque_nm', user_phrase='range')],
                                                     {'min_torque_nm': value}))

    def test_reference_contract_rejects_unknown_operations(self):
        model = agent.schemas(['fla'])['search_actuators']
        for operation in ('stronger', 'faster', 'smaller'):
            self.assertEqual(model(reference_operation=operation).reference_operation, operation)
        with self.assertRaises(ValueError):
            model(reference_operation='invent')


class RoutesTests(Base):
    def setUp(self):
        super().setUp()
        self.rows = list(catalogue().values())
        candidates = [r for r in self.rows if r['data_status'] == 'reported' and r['enclosure'] == 'weatherproof'
                      and r.get('on_off_torque_nm') and r.get('motor_power_w')]
        self.reference = min(candidates, key=lambda r: (Decimal(r['on_off_torque_nm']), r['base_part_number']))
        self.code = self.reference['base_part_number']

    def fresh(self):
        self.history, self.context = [], {}

    def keyless(self, query):
        with patch.object(agent, 'create_model_client', side_effect=AssertionError('Unexpected inference')):
            result = self.turn(query)
        self.assertFalse(result.debug['llm_called'])
        return result

    def test_objective_survives_three_refinements_and_changes(self):
        voltage = self.reference['supply_voltage_v']
        for first, follow in (
            ('Find on/off models using the least electricity.', f'Keep that preference, at {voltage} V outdoors.'),
            ('Find on/off actuators with the lowest motor power.', f'Also use weatherproof at {voltage} V.'),
            ('Busco actuadores on/off que consuman menos energía.', f'Además, para exterior a {voltage} V.'),
        ):
            with self.subTest(query=first):
                self.fresh()
                self.turn(first, ('search_actuators', dict(service='on_off', sort_by=['lowest_power'])))
                result = self.turn(follow, ('search_actuators', dict(refine=True, enclosure='weatherproof', supply_voltage_v=voltage)))
                self.assertEqual(result.context['filters']['sort_by'], ['lowest_power'])
                self.assertTrue(result.recommendation['ranked_by'].startswith('lowest motor power'))
                self.assertIn('N/A', result.answer)
                candidates = search_actuators(self.connection, SearchFilters.model_validate(
                    dict(result.context['filters'], limit=100)), allow_ambiguous=True)['products']
                expected = ranking.rank(candidates, result.context['filters'], 'lowest_power')[0]['base_part_number']
                self.assertEqual(result.recommendation['items'][0]['part_number'], expected)
                self.keyless('Which one do you recommend?')
                self.assertEqual(self.context['filters']['sort_by'], ['lowest_power'])
                changed = self.turn('Now prefer the fastest.', ('search_actuators', dict(refine=True, sort_by=['fastest'])))
                self.assertEqual(changed.context['filters']['sort_by'], ['fastest'])

    def test_stronger_reference_uses_sql_and_closest_strict_torque(self):
        for query in ('Find the next stronger model with the same supply and enclosure.',
                      'More on/off torque than that one, keeping its voltage and enclosure.',
                      'Busca más par on/off que el anterior, con el mismo voltaje y protección.'):
            with self.subTest(query=query):
                self.fresh()
                self.turn(f'Show the full on/off specifications of {self.code}.',
                          ('get_actuator', dict(part_numbers=[self.code], focus='overview')))
                result = self.turn(query, ('search_actuators', dict(reference_operation='stronger')))
                filters = result.context['filters']
                self.assertEqual(filters['enclosure'], self.reference['enclosure'])
                self.assertEqual(Decimal(str(filters['supply_voltage_v'])), Decimal(self.reference['supply_voltage_v']))
                self.assertEqual(filters['min_torque_nm']['op'], 'gt')
                self.assertEqual(Decimal(str(filters['min_torque_nm']['value'])), Decimal(self.reference['on_off_torque_nm']))
                rows = search_actuators(self.connection, SearchFilters.model_validate(dict(filters, limit=100)),
                                       allow_ambiguous=True)['products']
                self.assertTrue(rows)
                self.assertEqual(result.recommendation['items'][0]['part_number'], ranking.rank(rows, filters)[0]['base_part_number'])

    def test_ambiguous_reference_and_unpublished_size_are_not_invented(self):
        other = next(r['base_part_number'] for r in self.rows if r['base_part_number'] != self.code and r['data_status'] == 'reported')
        self.context = {'on_screen': [self.code, other]}
        result = self.turn('Find a stronger one.', ('search_actuators', dict(reference_operation='stronger')))
        self.assertEqual(result.clarification['field'], 'which_product')
        self.context = {'focused_model': self.code, 'reference_service': 'on_off'}
        result = self.turn('Find one physically smaller than that.', ('search_actuators', dict(reference_operation='smaller')))
        self.assertIn('dimensions are not published', result.answer)

    def test_faster_reference_requires_frequency_and_uses_published_time(self):
        self.context = {'focused_model': self.code, 'reference_service': 'on_off'}
        result = self.turn('Find one faster than that.', ('search_actuators', dict(reference_operation='faster')))
        self.assertEqual(result.clarification['field'], 'frequency')
        source = get_actuator(self.connection, self.code)
        hz = next(r['frequency_hz'] for r in source['frequencies'] if r.get('frequency_hz'))
        result = self.turn(f'Faster than that at {hz} Hz.', ('search_actuators', dict(reference_operation='faster')))
        bound = result.context['filters']['max_operating_time_s']
        self.assertEqual(bound['op'], 'lt')
        self.assertEqual(Decimal(str(bound['value'])), ranking.measurement(source, 'operating_time', {'frequency_hz': hz}))

    def test_compound_declines_preserve_published_parts_without_model(self):
        for query in (f'Give torque, price and lead time for {self.code}.',
                      f'For {self.code}, give motor power, pricing and how soon it ships.',
                      f'Para {self.code}, indica torque, precio y plazo de entrega.',
                      f'Give the supply voltage and enclosure, price and lead time for {self.code}.'):
            with self.subTest(query=query):
                self.fresh()
                result = self.keyless(query)
                self.assertIn("doesn't publish prices", result.answer)
                self.assertIn('does not publish delivery times or lead times', result.answer)
                self.assertTrue(result.products)

    def test_unpublished_properties_all_named_and_specs_offered(self):
        for query in (f'Give weight and SIL certification of {self.code}.',
                      f'How much does {self.code} weigh and what is its SIL rating?',
                      f'Indica el peso y SIL de {self.code} y compara con serie 99.'):
            with self.subTest(query=query):
                self.fresh()
                result = self.keyless(query)
                self.assertIn("doesn't publish weight", result.answer)
                self.assertIn('does not publish SIL', result.answer)
                self.assertEqual(result.products, [])
                self.assertIn('show published specs for ' + self.code, result.answer)
                if '99' in query:
                    self.assertIn('Other series', result.answer)

    def test_all_paraphrases_return_every_match(self):
        expected = {r['base_part_number'] for r in self.rows if r['data_status'] == 'reported'
                    and r['enclosure'] == 'weatherproof' and (r.get('on_off_torque_nm') or r.get('shared_torque_nm'))}
        for query in ('Give every weatherproof on/off model.', 'List all on/off actuators with weatherproof enclosures.',
                      'Quiero todos los modelos on/off weatherproof.'):
            with self.subTest(query=query):
                self.fresh()
                result = self.turn(query, ('search_actuators', dict(service='on_off', enclosure='weatherproof')))
                self.assertEqual({r['part_number'] for r in result.recommendation['items']}, expected)
                self.assertEqual(result.recommendation['shown'], len(expected))
                self.assertIsNone(result.interaction)

    def test_voltage_overview_paraphrases_and_product_search_boundary(self):
        voltages = {Decimal(r['supply_voltage_v']) for r in self.rows if r['data_status'] == 'reported'}
        for query in ('How many supply voltages are available?', 'Count distinct voltage options in Series 76.',
                      '¿Cuántos voltajes diferentes hay?', 'Voltajes disponibles'):
            with self.subTest(query=query):
                self.fresh()
                result = self.keyless(query)
                self.assertIn(f'{len(voltages)} published supply voltages', result.answer)
                for voltage in voltages:
                    self.assertIn(f'{voltage:g} V', result.answer)
        for query in ('Show models with weatherproof enclosures.', 'List actuators for these supply voltages.',
                      'Busca modelos con voltajes disponibles.'):
            self.assertIsNone(catalogue_answers.answer(self.connection, query))

    def test_known_weatherproof_hazard_suitability_is_sql_grounded(self):
        for query in (f'Is {self.code} suitable beside a gas line?',
                      f'Can {self.code} operate near solvent storage safely?',
                      f'Would {self.code} be acceptable next to a paint booth?',
                      f'¿Puedo usar {self.code} junto a una cabina de pintura?'):
            with self.subTest(query=query):
                self.fresh()
                result = self.keyless(query)
                self.assertIn('is Weatherproof', result.answer)
                self.assertIn('not Explosionproof', result.answer)
                self.assertIn('Confirm the area classification', result.answer)
                self.assertIn('find Explosionproof equivalents', result.answer)

    def test_applied_bound_labels_and_range(self):
        torque = Decimal(self.reference['on_off_torque_nm'])
        for op, label in (('gt', 'above'), ('lt', 'below'), ('gte', 'at or above'), ('lte', 'at or below')):
            with self.subTest(op=op):
                text = ranking.ranked_by({'min_torque_nm': dict(value=torque, op=op)})
                self.assertIn(f'closest torque {label} {torque:g} Nm', text)
                if op in ('gt', 'lt'):
                    self.assertNotIn('at or', text)
        self.assertIn('and below', ranking.ranked_by({'min_torque_nm': [dict(value=0, op='gte'), dict(value=torque, op='lt')]}))

    def test_corrected_upper_bound_nearest_is_scoped_and_not_recommended(self):
        # Inject the correctly merged state: this test does not depend on D1's parser.
        torque = min(Decimal(r['on_off_torque_nm']) for r in self.rows if r.get('on_off_torque_nm')
                     and r['enclosure'] == self.reference['enclosure'] and r['data_status'] == 'reported')
        limit = torque / 2
        for query in ('Apply the corrected limit.', 'Keep the corrected upper bound.', 'Conserva el límite corregido.'):
            with self.subTest(query=query):
                self.fresh()
                self.context = {'filters': dict(service='on_off', enclosure=self.reference['enclosure'],
                                               min_torque_nm=dict(value=float(limit), op='lte'))}
                result = self.turn(query, ('search_actuators', dict(refine=True)))
                self.assertEqual(result.recommendation['total'], 0)
                self.assertEqual(result.recommendation['items'], [])
                closest = result.tool_calls[0]['data']['closest']
                self.assertEqual(Decimal(str(closest[0]['value'])), torque)
                self.assertIn('Does not meet', result.answer)
                self.assertTrue(result.context['zero_result_nearest'])

    def test_false_csa_assumption_never_has_empty_interpretation(self):
        for phrase in ('CSA approval is not required', 'No CSA certification is necessary', 'CSA listing does not matter'):
            with self.subTest(phrase=phrase):
                self.fresh()
                result = self.turn('Find weatherproof on/off actuators; ' + phrase,
                                   ('search_actuators', dict(service='on_off', enclosure='weatherproof', csa_required=False,
                                        assumptions=[dict(field='csa_required', user_phrase=phrase)])))
                self.assertNotIn('read as .', result.answer)
                self.assertNotIn('csa_required', result.context['filters'])
                self.assertFalse(result.assumptions)
