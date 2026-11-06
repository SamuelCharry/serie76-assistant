import unittest

from scripts.eval_retrieval import metrics, rank_bank, signature


def example(identifier, text, vector, service='on_off', model='fake'):
    return dict(id=identifier, text=text, vector=vector, model=model,
                interpretation=dict(tool='search_actuators', args=dict(service=service)))


class RetrievalTests(unittest.TestCase):
    def test_known_vectors_ranks_and_missing_slots(self):
        bank = [example(1, 'a', [1, 0]), example(2, 'b', [1, .1]),
                example(3, 'c', [0, 1], 'modulating'),
                example(4, 'd', [.1, 1], 'modulating')]
        ranked = rank_bank(bank)
        self.assertEqual([r[0][1] for r in ranked], [2, 1, 4, 3])
        self.assertEqual(metrics(ranked, 1)['precision'], 1)
        self.assertEqual(metrics(ranked, 3)['precision'], 1/3)
        self.assertEqual(metrics(ranked, 5)['precision'], 1/5)
        self.assertEqual(metrics(ranked, 5)['mrr'], 1)
        self.assertEqual(metrics(ranked, 5, .999)['coverage'], 0)

    def test_self_duplicate_and_other_models_excluded(self):
        bank = [example(1, 'same', [1, 0]), example(2, 'same', [1, 0]),
                example(3, 'other', [1, 0], model='other')]
        self.assertEqual(rank_bank(bank), [[], [], []])

    def test_relevant_at_second_rank_and_queries_with_no_match(self):
        bank = [example(1, 'a', [1, 0]), example(2, 'b', [.9, .1], 'modulating'),
                example(3, 'c', [0, 1])]
        ranked = rank_bank(bank)
        self.assertEqual(metrics(ranked, 1)['mrr'], 0)
        self.assertEqual(metrics(ranked, 5)['mrr'], 1/3)
        self.assertEqual(metrics(ranked, 1, .9)['coverage'], 2/3)

    def test_fields_and_bound_operators_must_agree(self):
        base = dict(tool='search_actuators', args=dict(service='on_off', min_torque_nm=70))
        equivalent = dict(tool='search_actuators', args=dict(service='on_off', min_torque_in_lb={'op': 'gte', 'value': 9}))
        self.assertEqual(signature(base), signature(equivalent))
        for field, value in [('service', 'modulating'), ('enclosure', 'explosionproof'),
                             ('supply_voltage_v', 110), ('min_torque_nm', {'op': 'lt', 'value': 70}),
                             ('min_torque_nm', [{'op': 'gte', 'value': 70}, {'op': 'lte', 'value': 100}])]:
            changed = dict(tool=base['tool'], args={**base['args'], field: value})
            self.assertNotEqual(signature(base), signature(changed))
        self.assertNotEqual(signature(base), signature(dict(tool='ask_clarification', args=base['args'])))
