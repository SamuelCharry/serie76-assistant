"""Frozen expectations are not weakened by full-state oracle authoring."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.agent_acceptance import t10_oracle

ROOT = Path(__file__).resolve().parents[1]


class FrozenStateOracles(unittest.TestCase):
    def test_original_queries_and_assertions_are_unchanged(self):
        converted = json.loads((ROOT / 'config/agent_acceptance_cases_sv2.json').read_text(encoding='utf8'))
        cases = {s['id']: s for s in converted['scenarios']}
        count = 0
        for cohort in ('t10', 't12', 't14'):
            source = json.loads((ROOT / f'config/agent_acceptance_cases_{cohort}.json').read_text(encoding='utf8'))
            for scenario in source['scenarios']:
                expected = t10_oracle().resolve(deepcopy(scenario))
                actual = deepcopy(cases[scenario['id']])
                for turn in expected['turns'] + actual['turns']:
                    turn.pop('scripted_decision', None)
                self.assertEqual(actual, expected, scenario['id'])
                count += 1
        self.assertEqual(count, 137)


if __name__ == '__main__':
    unittest.main()
