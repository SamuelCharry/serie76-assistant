import unittest

from scripts.eval_stats import bootstrap_ci, evaluate, mcnemar_exact, minimum_one_way


class StatsTests(unittest.TestCase):
    def test_known_exact_mcnemar(self):
        self.assertEqual(mcnemar_exact(6, 0), .03125)
        self.assertEqual(mcnemar_exact(1, 7), .0703125)
        self.assertEqual(minimum_one_way(41), 6)
        self.assertIsNone(minimum_one_way(5))

    def test_identical_runs(self):
        result = evaluate(dict(aggregate_rounds=[], paired={'same': {
            'one': {'A': 1, 'B': 1}, 'two': {'A': 0, 'B': 0}}}))
        pair = result['paired'][0]
        self.assertEqual(pair['p_value'], 1)
        self.assertEqual(pair['ci95'], [0, 0])

    def test_seeded_interval_reproducible(self):
        first = bootstrap_ci([1]*28 + [0]*13)
        self.assertEqual(first, bootstrap_ci([1]*28 + [0]*13))
        self.assertLess(first[0], 28/41)
        self.assertGreater(first[1], 28/41)

    def test_reject_unpaired_or_nonbinary_input(self):
        for rows in ({'x': {'A': 1, 'B': 2}},
                     {'x': {'A': 1, 'B': 0}, 'y': {'A': 1}}):
            with self.assertRaises(ValueError):
                evaluate(dict(aggregate_rounds=[], paired={'bad': rows}))
