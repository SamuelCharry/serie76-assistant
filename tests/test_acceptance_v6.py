"""Deliberate corruptions must fail the actual acceptance scorer (no provider/DB)."""
from copy import deepcopy
import unittest
from scripts.agent_acceptance import score


class MutationChecks(unittest.TestCase):
    def fixture(self):
        code = '761A00-11300000/A'
        turn = dict(query='On/off torque over 70 Nm, show motor power', expect=dict(contract_v6=True,
            tool='get_actuator', args={'min_torque_nm': {'value': 70, 'op': 'gt'}},
            products_include=[code], contains=['15 W'], suggestions_count=0))
        result = dict(answer=code + ': Motor power: 15 W', products=[dict(base_part_number=code,
            source={'page':1}, measurements={'motor_power_w':15}, field_status={'motor_power_w':'reported'})],
            terms=[], clarification=None, assumptions=[], suggestions=[], suggested_replies=[], active_filters=[],
            interaction=None, comparison=None, lead=None, trace=dict(name='get_actuator',
                parameters={'min_torque_nm':{'value':'70','op':'gt'}}, context_after={}, model={'decision_calls':1}))
        self.assertTrue(score(turn, result)[0])
        return turn,result

    def test_strict_operator_mutation_fails(self):
        turn,result=self.fixture()
        result['trace']['parameters']['min_torque_nm']['op']='gte'
        self.assertFalse(score(turn,result)[0])

    def test_na_to_zero_mutation_fails(self):
        turn,result=self.fixture()
        code='761A00-11330C00/A'
        turn['expect'].update(products_include=[code], contains=['N/A'])
        result['answer']=code+': Motor power: N/A in the source table'
        result['products'][0].update(base_part_number=code, source={'page':2}, measurements={'motor_power_w':None}, field_status={'motor_power_w':'source_NA'})
        self.assertTrue(score(turn,result)[0])
        result['products'][0]['measurements']['motor_power_w']=0
        self.assertFalse(score(turn,result)[0])

    def test_wrong_unit_mutation_fails(self):
        turn,result=self.fixture()
        result['answer']=result['answer'].replace('15 W','15 A')
        self.assertFalse(score(turn,result)[0])

    def test_dropped_requirement_mutation_fails(self):
        turn,result=self.fixture()
        result['trace']['parameters'].pop('min_torque_nm')
        self.assertFalse(score(turn,result)[0])

    def test_substituted_code_even_same_numeric_value_fails(self):
        turn,result=self.fixture()
        result['products'][0]['base_part_number']='761B00-11300000/A'
        self.assertFalse(score(turn,result)[0])

    def test_range_cannot_drop_upper_bound(self):
        turn,result=self.fixture()
        turn['expect']['args']['min_torque_nm']=[{'value':70,'op':'gte'},{'value':100,'op':'lte'}]
        result['trace']['parameters']['min_torque_nm']=deepcopy(turn['expect']['args']['min_torque_nm'])
        self.assertTrue(score(turn,result)[0])
        result['trace']['parameters']['min_torque_nm'].pop()
        self.assertFalse(score(turn,result)[0])
