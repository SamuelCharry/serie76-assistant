"""Hand-computed IR metrics and independent CSV judgment boundary checks."""
import copy
import json
import math
import unittest

from scripts.eval_ranking import ranking_metrics
from scripts.ranking_judgments import ROOT, judge_query, load_catalog, violations


class RankingMetricTests(unittest.TestCase):
    def test_binary_ap_and_recall_use_full_relevant_set(self):
        # Relevant A,C,D; ranking B,A,C: hits at 2 and 3.
        grades = {'A': 3, 'B': 0, 'C': 2, 'D': 1}
        result = ranking_metrics(['B', 'A', 'C'], grades, 3)
        self.assertAlmostEqual(result['precision'], 2 / 3)
        self.assertAlmostEqual(result['recall'], 2 / 3)
        self.assertAlmostEqual(result['ap'], (1 / 2 + 2 / 3) / 3)
        # DCG = 0 + 7/log2(3) + 3/2; IDCG = 7 + 3/log2(3) + 1/2.
        self.assertAlmostEqual(result['ndcg'], (7 / math.log2(3) + 1.5) /
                               (7 + 3 / math.log2(3) + .5))

    def test_short_safe_list_is_not_standard_precision_one(self):
        result = ranking_metrics(['A'], {'A': 3, 'B': 1}, 5)
        self.assertEqual(result['precision'], .2)
        self.assertEqual(result['compliance_returned'], 1)
        self.assertEqual(result['recall'], .5)
        self.assertEqual(result['ap'], .5)
        self.assertAlmostEqual(result['ndcg'], 7 / (7 + 1 / math.log2(3)))

    def test_missing_relevant_products_reduce_ap(self):
        result = ranking_metrics(['A', 'B'], {'A': 2, 'B': 1, 'C': 3, 'D': 2}, 3)
        self.assertEqual(result['ap'], .5)
        self.assertEqual(result['recall'], .5)

    def test_perfect_graded_ranking_and_ties(self):
        grades = {'A': 3, 'B': 3, 'C': 2, 'D': 1, 'E': 0}
        for k in (3, 5):
            result = ranking_metrics(['B', 'A', 'C', 'D', 'E'], grades, k)
            self.assertEqual(result['ndcg'], 1)
        self.assertEqual(ranking_metrics(['A', 'B', 'C', 'D', 'E'], grades, 5)['ap'], 1)

    def test_empty_and_no_relevant_queries_not_perfect(self):
        for grades in ({'A': 0}, {'A': 3}, {}):
            result = ranking_metrics([], grades, 3)
            self.assertEqual([result[k] for k in ('precision', 'recall', 'ap', 'ndcg')], [0] * 4)
            self.assertIsNone(result['compliance_returned'])

    def test_invalid_rankings_rejected(self):
        for ranked, grades, k in [(['A', 'A'], {'A': 3}, 3), (['B'], {'A': 3}, 3),
                                  (['A'], {'A': 4}, 3), ([], {}, 0), ([], {}, True)]:
            with self.assertRaises(ValueError):
                ranking_metrics(ranked, grades, k)

    def test_map_is_macro_average(self):
        # Query 1: AP=1; query 2: relevant item only at rank 2 -> AP=1/2.
        ap1 = ranking_metrics(['A'], {'A': 1}, 3)['ap']
        ap2 = ranking_metrics(['B', 'A'], {'A': 1, 'B': 0}, 3)['ap']
        self.assertEqual((ap1 + ap2) / 2, .75)


class IndependentJudgmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_catalog()
        cls.config = json.loads((ROOT / 'config/ranking_eval_t11.json').read_text(encoding='utf-8'))

    def test_exhaustive_judgments_and_no_code_targeting(self):
        self.assertEqual(len(self.config['queries']), 40)
        for query in self.config['queries']:
            with self.subTest(query=query['id']):
                grades = judge_query(self.rows, query)
                self.assertEqual(len(grades), 68)
                if query['id'] == 'T11-R36':
                    # No 24 V on/off product supplies the requested 400 Nm.
                    self.assertTrue(all(v['grade'] == 0 for v in grades.values()))
                else:
                    self.assertTrue(any(v['grade'] == 3 for v in grades.values()))
                self.assertNotRegex(query['request'], r'76\w{4}-')

    def test_missing_data_and_strict_torque_boundary(self):
        query = copy.deepcopy(self.config['queries'][0])
        row = self.rows[0]  # Published 80 Nm at on/off service.
        query['filters']['bounds'] = [{'field': 'min_torque_nm', 'op': 'gte', 'value': 80}]
        self.assertEqual(violations(row, query['filters']), [])
        query['filters']['bounds'][0]['op'] = 'gt'
        self.assertTrue(violations(row, query['filters']))
        for source_na in (r for r in self.rows if r['data_status'] == 'source_NA'):
            self.assertIn('catalogue values not reported', violations(source_na, query['filters']))

    def test_default_smallest_adequate_then_current_and_oversizing(self):
        query = copy.deepcopy(self.config['queries'][0])
        query['filters']['bounds'] = [{'field': 'min_torque_nm', 'op': 'gte', 'value': 80}]
        grades = judge_query(self.rows, query)
        self.assertEqual(grades[self.rows[0]['base_part_number']]['grade'], 3)
        self.assertEqual(grades[self.rows[1]['base_part_number']]['grade'], 2)
        self.assertEqual(grades[self.rows[3]['base_part_number']]['grade'], 1)

    def test_objective_ties_and_missing_power(self):
        query = copy.deepcopy(self.config['queries'][0])
        query['objective'] = 'lowest_power'
        query['filters']['bounds'] = [{'field': 'min_torque_nm', 'op': 'gte', 'value': 80}]
        rows = copy.deepcopy(self.rows)
        grades = judge_query(rows, query)
        self.assertEqual(grades[rows[0]['base_part_number']]['grade'], 3)
        self.assertEqual(grades[rows[1]['base_part_number']]['grade'], 3)
        rows[0]['motor_power_w'] = None
        grades = judge_query(rows, query)
        self.assertEqual(grades[rows[0]['base_part_number']]['grade'], 1)
        query['filters']['bounds'].append({'field': 'max_motor_power_w', 'op': 'lte', 'value': 40})
        self.assertEqual(judge_query(rows, query)[rows[0]['base_part_number']]['grade'], 0)

    def test_shared_and_service_specific_values(self):
        shared = next(r for r in self.rows if r['service_layout'] == 'shared' and r['data_status'] == 'reported')
        query = copy.deepcopy(self.config['queries'][16])
        query['filters']['service'] = 'modulating'
        self.assertEqual(violations(shared, query['filters']), [])
        query = copy.deepcopy(self.config['queries'][0])
        query['filters']['bounds'] = [{'field': 'min_torque_nm', 'op': 'gte', 'value': 75}]
        self.assertEqual(violations(self.rows[0], query['filters']), [])
        query['filters']['service'] = 'modulating'
        self.assertTrue(violations(self.rows[0], query['filters']))


if __name__ == '__main__':
    unittest.main()
