"""T12 mechanism boundaries: independent service rows, exclusivity and provenance."""
import json
from pathlib import Path
import unittest

from backend.catalog.models import SearchFilters
from backend.catalog.repository import search_actuators
from backend.conversation import integrity, policy, answer_planner
from scripts.acceptance_contract import eligible_codes
from test_agent_scenarios import Base


class IntegrityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.product = dict(supply_current='AC', services=[
            dict(service='shared', torque_nm=300, duty_s4_percent=70),
            dict(service='modulating', starts_per_hour=1200),
            dict(service='on_off', cycles_per_hour=30)],
            provenance={'shared_services_confirmed': True})

    def test_shared_torque_and_service_starts_combine(self):
        self.assertTrue(integrity.satisfies(self.product, SearchFilters(
            service='modulating', min_torque_nm=300, min_starts_per_hour=1200)))

    def test_shared_torque_and_service_cycles_combine(self):
        self.assertTrue(integrity.satisfies(self.product, SearchFilters(
            service='on_off', min_torque_nm=300, min_cycles_per_hour=30)))

    def test_shared_values_need_confirmed_provenance(self):
        self.product['provenance']['shared_services_confirmed'] = False
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(service='modulating', min_torque_nm=300)))

    def test_service_value_wins_over_shared_value(self):
        self.product['services'][1]['torque_nm'] = 200
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(service='modulating', min_torque_nm=300)))

    def test_rates_cannot_come_from_opposite_service(self):
        self.product['services'][1].pop('starts_per_hour')
        self.product['services'][2]['starts_per_hour'] = 1200
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(service='modulating', min_starts_per_hour=1200)))

    def test_unspecified_service_cannot_mix_opposite_rows(self):
        self.product['services'] = [dict(service='on_off', torque_nm=500, duty_s4_percent=20),
                                    dict(service='modulating', torque_nm=200, duty_s4_percent=70)]
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(min_torque_nm=300, min_duty_s4_percent=50)))

    def test_missing_values_stay_missing(self):
        self.product['services'][0]['torque_nm'] = None
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(service='modulating', min_torque_nm=1)))

    def test_strict_bounds_are_not_loosened(self):
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(
            service='modulating', min_torque_nm={'op': 'gt', 'value': 300})))

    def test_dc_only_rejects_acdc_but_plain_dc_accepts_it(self):
        self.product['supply_current'] = 'AC/DC'
        self.assertTrue(integrity.satisfies(self.product, SearchFilters(supply_current='DC')))
        self.assertFalse(integrity.satisfies(self.product, SearchFilters(supply_current='DC', dc_only=True)))

    def test_list_question_is_not_superlative(self):
        self.assertNotEqual(answer_planner.plan('Which units provide 150 to 500 Nm for on/off duty?').shape, 'verdict')
        self.assertEqual(answer_planner.plan('Which units have the highest duty?').shape, 'verdict')

    def test_exclusive_paraphrases_and_ordinary_supply(self):
        for phrase in ('DC-only', 'DC only', 'solo DC', 'only direct current'):
            self.assertTrue(policy.current_requirement(phrase)['dc_only'])
        self.assertNotIn('dc_only', policy.current_requirement('DC'))
        self.assertEqual(policy.current_requirement('VAC/VDC')['supply_current'], 'AC/DC')

    def test_cohort_contains_every_requested_failure(self):
        cases = json.loads((Path(__file__).resolve().parents[1] / 'config/agent_acceptance_cases_t12.json').read_text(encoding='utf-8'))
        self.assertEqual({s['source_v12'] for s in cases['scenarios'] if 'source_v12' in s},
                         {f'V12-{i:02}' for i in (5,7,12,14,22,23,24,25,28,32,33,35,36,39,42,44)})

    def test_explicit_filter_withdrawal_overrides_site_inference(self):
        for query in ('Non-hazardous room; remove the explosionproof restriction.',
                      'Zona normal; retira el requisito explosionproof.',
                      'Drop explosionproof.', 'Olvida explosionproof.'):
            self.assertTrue(policy.enclosure_withdrawal(query), query)
            self.assertNotIn('enclosure', policy.colloquial_requirements(query)[0], query)

    def test_site_correction_keeps_legacy_clearance(self):
        for query in ("Forget explosionproof, it is a normal area.",
                      'Olvida explosionproof, es una zona normal.'):
            self.assertFalse(policy.enclosure_withdrawal(query), query)
            self.assertEqual(policy.colloquial_requirements(query)[0]['enclosure'], 'weatherproof')


class T12DatabaseTests(Base):
    def test_r22_all_seven_pass_sql_and_integrity(self):
        filters = SearchFilters(enclosure='weatherproof', supply_voltage_v=220, supply_current='AC',
            phase_count=3, service='modulating', frequency_hz=60, min_torque_nm=300, min_starts_per_hour=1200, limit=100)
        rows = search_actuators(self.connection, filters)['products']
        self.assertEqual(len(rows), 7)
        self.assertEqual({p['base_part_number'] for p in rows}, set(eligible_codes(filters.model_dump(exclude_none=True))))
        self.assertTrue(all(integrity.satisfies(p, filters) for p in rows))
        too_high = filters.model_copy(update={'min_starts_per_hour': 1201})
        self.assertFalse(any(integrity.satisfies(p, too_high) for p in rows))

    def test_dc_only_and_plain_dc_sql_sets(self):
        for exclusive, service, count in ((False,'on_off',5),(True,'on_off',0),(True,'modulating',5)):
            filters = SearchFilters(supply_voltage_v=24,supply_current='DC',dc_only=exclusive,service=service,limit=100)
            rows = search_actuators(self.connection, filters)['products']
            self.assertEqual(len(rows), count)
            self.assertEqual({p['base_part_number'] for p in rows}, set(eligible_codes(filters.model_dump(exclude_none=True))))

    def test_recorded_redundant_range_keeps_both_bounds(self):
        self.turn('Weatherproof 110 V AC on/off torque no more than 300 Nm.',
                  ('search_actuators',dict(enclosure='weatherproof',supply_voltage_v=110,supply_current='AC',service='on_off',min_torque_nm={'op':'lte','value':300})))
        result = self.turn('Also require at least 150 Nm.', ('search_actuators',dict(refine=True,
            bounds=[dict(field='min_torque_nm',op='lte',value=300),dict(field='min_torque_nm',op='gte',value=150)])))
        bound = result.context['filters']['min_torque_nm']
        self.assertEqual({(x['op'],int(x['value'])) for x in bound}, {('lte',300),('gte',150)})
        self.assertTrue(result.products or result.recommendation)

    def test_unrequested_removals_do_not_erase_retained_supply(self):
        self.turn('Explosionproof 24 V DC modulating units.', ('search_actuators',dict(enclosure='explosionproof',supply_voltage_v=24,supply_current='DC',service='modulating')))
        result = self.turn('Keep the hazardous-site requirement.', ('search_actuators',dict(refine=True,enclosure='explosionproof',remove=['supply_current','supply_voltage_v'])))
        self.assertEqual(result.context['filters']['supply_voltage_v'],24)
        self.assertEqual(result.context['filters']['supply_current'],'DC')

    def test_dc_only_can_be_withdrawn_with_current(self):
        self.turn('24 V DC-only modulating units.', ('search_actuators',dict(supply_voltage_v=24,supply_current='DC',service='modulating')))
        result = self.turn('Remove the current restriction.', ('search_actuators',dict(refine=True,remove=['supply_current'])))
        self.assertNotIn('dc_only',result.context['filters'])

    def test_model_cannot_silently_relax_exclusivity(self):
        self.turn('24 V DC-only modulating units.', ('search_actuators',dict(supply_voltage_v=24,supply_current='DC',service='modulating')))
        result = self.turn('Add a minimum torque of 100 Nm.', ('search_actuators',dict(refine=True,min_torque_nm=100,dc_only=False)))
        self.assertTrue(result.context['filters']['dc_only'])

    def test_model_omitted_power_objective_is_grounded(self):
        result = self.turn('List weatherproof 110 V AC on/off models with least watts.',
                          ('search_actuators',dict(enclosure='weatherproof',supply_voltage_v=110,supply_current='AC',service='on_off')))
        self.assertEqual(result.context['filters']['sort_by'],['lowest_power'])

    def test_new_search_can_replace_empty_dc_only_set(self):
        self.turn('24 V DC-only on/off units.', ('search_actuators',dict(supply_voltage_v=24,supply_current='DC',service='on_off')))
        result = self.turn('List weatherproof 110 V AC on/off models.',
                          ('search_actuators',dict(refine=False,enclosure='weatherproof',supply_voltage_v=110,supply_current='AC',service='on_off')))
        self.assertFalse(result.context['filters'].get('dc_only'))
        self.assertTrue(result.context['last_ranked_list'])

