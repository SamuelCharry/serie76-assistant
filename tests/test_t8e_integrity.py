"""Published results must satisfy the user's stated service and bounds."""
import random
import unittest
from backend.catalog.models import SearchFilters
from backend.catalog.repository import search_actuators
from backend.conversation import policy
from test_agent_scenarios import Base


class IntegrityTests(Base):
    def test_upper_torque_bound_is_not_dropped(self):
        result = self.turn('Torque no more than 100 Nm, weatherproof, 220 V',
                           ('search_actuators', {'enclosure': 'weatherproof', 'supply_voltage_v': 220}))
        self.assertEqual(result.recommendation['total'], 2)
        self.assertEqual(set(result.context['last_ranked_list']),
                         {'761A00-11320000/A', '761B00-11320000/A'})
        self.assertEqual(result.context['filters']['min_torque_nm'], {'value': 100, 'op': 'lte'})
        self.assertIn('at or below 100 Nm', result.recommendation['ranked_by'])
        self.assertEqual(result.recommendation['items'][0]['part_number'], '761B00-11320000/A')

    def test_short_mod_keeps_service_for_pick(self):
        first = self.turn('110 mod 200nm', ('search_actuators', {'supply_voltage_v': 110, 'min_torque_nm': 200}))
        self.assertEqual(first.context['filters']['service'], 'modulating')
        picked = self.turn('best', ('ask_clarification', {'field': 'requirements', 'intent': 'pick'}))
        code = picked.recommendation['items'][0]['part_number']
        row = next(p for p in search_actuators(self.connection, SearchFilters(supply_voltage_v=110,
                          service='modulating', min_torque_nm=200, limit=100), allow_ambiguous=True)['products']
                   if p['base_part_number'] == code)
        self.assertGreaterEqual(row['measurements'].get('modulating_torque_nm') or row['measurements'].get('shared_torque_nm'), 200)

    def test_upper_bound_phrases(self):
        for phrase in ('no more than', 'at most', 'up to', 'max', '≤', 'below', 'under', 'hasta', 'máximo'):
            with self.subTest(phrase=phrase):
                values, _ = policy.colloquial_requirements(f'torque {phrase} 100 Nm')
                self.assertEqual(values['min_torque_nm'], {'value': 100, 'op': 'lt' if phrase in ('below', 'under') else 'lte'})

    def test_random_searches_obey_postcondition(self):
        from backend.conversation.integrity import satisfies
        random.seed(76)
        for _ in range(80):
            scope = SearchFilters(service=random.choice([None, 'on_off', 'modulating']),
                                  min_torque_nm={'value': random.randrange(50, 1501, 50),
                                                 'op': random.choice(['gte', 'lte'])},
                                  supply_voltage_v=random.choice([None, 110, 220]), limit=100)
            result = search_actuators(self.connection, scope, allow_ambiguous=True)
            for product in result['products']:
                self.assertTrue(satisfies(product, scope), product['base_part_number'])
