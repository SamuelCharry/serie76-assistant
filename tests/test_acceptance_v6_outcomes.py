"""The suite scores the required outcome, including deterministic policy guards."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.agent_acceptance import score

ROOT = Path(__file__).resolve().parents[1]
A, B = '761A00-11300000/A', '761B00-11300000/A'


class OutcomeExpectations(unittest.TestCase):
    def fixture(self, scenario, index, name, parameters, answer, clarification=None):
        cases = json.loads((ROOT/'config/agent_acceptance_cases_v6.json').read_text(encoding='utf-8'))
        turn = next(s for s in cases['scenarios'] if s['id'] == scenario)['turns'][index]
        result = dict(answer=answer, products=[], terms=[], clarification=clarification,
                      assumptions=[], suggestions=[], suggested_replies=[], active_filters=[],
                      interaction=None, comparison=None, lead=None,
                      trace=dict(name=name, parameters=parameters, context_after={}, model={'decision_calls':1}))
        return turn, result

    def test_ec04_accepts_guard_but_rejects_picking_or_recomparing(self):
        turn, result = self.fixture('EC04', 1, 'get_actuator', {'part_numbers':[A, B]},
            'Which of the previously listed actuators do you mean? Please give its complete part number.',
            {'field':'which_product'})
        self.assertTrue(score(turn, result)[0], score(turn, result)[1])
        picked = deepcopy(result)
        picked['products'] = [dict(base_part_number=A, source={'page':1}, measurements={'lra_60hz_a':1.4})]
        self.assertFalse(score(turn, picked)[0])
        compared = deepcopy(result)
        compared['comparison'] = dict(models=[A,B], layout='table', summary='Comparison', assumptions='',
                                     rows=[], hidden_rows=[], key_fields=[])
        self.assertFalse(score(turn, compared)[0])
        result['clarification'] = None
        self.assertFalse(score(turn, result)[0])

    def test_ec30_accepts_limitation_but_not_missing_price_or_weighting_limits(self):
        turn, result = self.fixture('EC30', 0, 'ask_clarification', {'field':'unsupported'},
            'The supplied catalogue has no prices. I cannot calculate a weighted overall score involving price; '
            'I can compare published torque, operating time, current and motor power.')
        self.assertTrue(score(turn, result)[0], score(turn, result)[1])
        for answer in ('The best actuator is ' + A, 'There are no prices.', 'Here is a weighted score: 85.'):
            bad = deepcopy(result)
            bad['answer'] = answer
            self.assertFalse(score(turn, bad)[0])
