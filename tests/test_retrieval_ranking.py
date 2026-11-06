import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from backend.conversation import retrieval_ranking as ranking
from scripts.eval_retrieval import prompt_useful, signature


def row(identifier, text, similarity, **args):
    return dict(id=identifier, text=text, similarity=similarity,
                interpretation=dict(tool='search_actuators', args=args))


class RankingTests(unittest.TestCase):
    def test_prompt_useful_ignores_voltage_values_but_not_fields_or_mapping(self):
        a = row(1, '', 1, service='on_off', supply_voltage_v=110)['interpretation']
        b = row(2, '', 1, service='on_off', supply_voltage_v=220)['interpretation']
        self.assertTrue(prompt_useful(a, b))
        self.assertNotEqual(signature(a), signature(b))
        self.assertFalse(prompt_useful(a, row(3, '', 1, service='on_off')['interpretation']))
        self.assertFalse(prompt_useful(a, row(4, '', 1, service='modulating', supply_voltage_v=110)['interpretation']))

    def test_detects_existing_normalizer_fields_and_bound_direction(self):
        detected = ranking.detected_fields('on/off, XP, 110 V, 3 phases, above 300 Nm')
        self.assertEqual(detected, dict(service='on_off', enclosure='explosionproof',
                                       supply_voltage_v=110, phase_count=3, torque_operators=('gt',)))

    def test_rerank_uses_query_text_and_counts_conflicts(self):
        rows = [row(1, 'wrong', .9, service='modulating', supply_voltage_v=220),
                row(2, 'right', .8, service='on_off', supply_voltage_v=110)]
        ranked = ranking.rerank('on/off 110 V', rows, .1)
        self.assertEqual([r['id'] for r in ranked], [2, 1])
        self.assertAlmostEqual(ranked[0]['rank_score'], 1)
        self.assertAlmostEqual(ranked[1]['rank_score'], .7)
        self.assertNotIn('rank_score', rows[0])

    def test_tokens_preserve_domain_cues(self):
        self.assertEqual(ranking.tokens('ON-OFF XP WP 110 V 24v modulación'),
                         ['on/off', 'xp', 'wp', '110v', '24v', 'modulacion'])

    def test_bm25_and_rrf_have_known_order(self):
        rows = [row(1, 'modulating 220 V', .9), row(2, 'on/off 110V', .8)]
        lexical = ranking.BM25(rows)
        self.assertEqual(lexical.rank('110 V', [1, 2])[0][0], 2)
        self.assertEqual(ranking.hybrid('110 V', rows, lexical)[0]['id'], 2)
        self.assertEqual(ranking.hybrid('unseen', rows, lexical)[0]['id'], 1)

    def test_mask_units_but_never_bare_part_codes(self):
        self.assertEqual(ranking.mask_values('110 V, 300 Nm, 60 Hz, 24v, 1.2 kNm, 761A00-11300000/A'),
                         '<VOLTAGE>, <TORQUE>, <FREQ>, <VOLTAGE>, <TORQUE>, 761A00-11300000/A')

    def test_google_single_embedding_allows_omitted_zero_index_and_usage(self):
        from scripts.embed_masked_bank import embed_one
        client = Mock()
        vector = [1.0] + [0.0]*767
        client.embeddings.create.return_value = SimpleNamespace(
            data=[SimpleNamespace(index=None, embedding=vector)], usage=None)
        self.assertEqual(embed_one(client, '<VOLTAGE>'), (vector, None))
        self.assertEqual(client.embeddings.create.call_args.kwargs['input'], '<VOLTAGE>')
        client.embeddings.create.return_value = SimpleNamespace(data=None, usage=None)
        with self.assertRaises(ValueError):
            embed_one(client, '<VOLTAGE>')

    def test_mmr_penalizes_redundant_second_result(self):
        rows = [row(1, 'a', 1), row(2, 'b', .95), row(3, 'c', .8), row(4, 'd', .1)]
        similarities = {(i, j): (.99 if {i, j} == {1, 2} else 0) for i in range(1, 5) for j in range(1, 5)}
        ranked = ranking.mmr(rows, similarities, .5)
        self.assertEqual([r['id'] for r in ranked[:2]], [1, 3])
