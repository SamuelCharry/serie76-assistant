"""Offline embedding contract; the fake measures mechanics, not semantic quality."""
import hashlib
import math
import os
import re
import unittest
from unittest.mock import patch

from backend.conversation import embeddings
from scripts import load_example_bank as loader


class FakeEmbedder:
    model = 'test-hashed-768'

    def embed_documents(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * 768
            for word in re.findall(r'\w+', text.lower()):
                vector[int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], 'big') % 768] += 1
            norm = math.sqrt(sum(v * v for v in vector)) or 1
            vectors.append([v / norm for v in vector])
        return vectors

    def embed_query(self, text):
        return self.embed_documents([text])[0]


class EmbeddingTests(unittest.TestCase):
    def test_langchain_client_has_bounded_requests_on_both_endpoints(self):
        for url, model in [('https://generativelanguage.googleapis.com/v1beta/openai/', 'gemini-embedding-2'),
                           ('https://openrouter.ai/api/v1', 'google/gemini-embedding-2')]:
            with patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL=model, OPENROUTER_API_KEY='test-only',
                            OPENROUTER_BASE_URL=url, EMBEDDING_BASE_URL='', EMBEDDING_API_KEY=''):
                client = embeddings.client()
                self.assertEqual(client.dimensions, 768)
                self.assertEqual(client.request_timeout, 1.5)
                self.assertEqual(client.max_retries, 0)
                self.assertFalse(client.check_embedding_ctx_length)

    def test_every_provider_batch_reserves_budget(self):
        from unittest.mock import Mock
        fake = FakeEmbedder()
        with patch.object(embeddings, 'client', return_value=fake):
            with patch('backend.conversation.agent.reserve_agent_call') as guard:
                self.assertEqual(len(embeddings.embed_documents(['gas'] * 65)), 65)
        self.assertEqual(guard.call_count, 2)
        fake.embed_documents = Mock(side_effect=AssertionError('provider must not run'))
        with patch.object(embeddings, 'client', return_value=fake):
            with patch('backend.conversation.agent.reserve_agent_call', side_effect=RuntimeError('budget')):
                with self.assertRaises(RuntimeError):
                    embeddings.embed_query('gas')
        fake.embed_documents.assert_not_called()

    def test_examples_skip_ambiguous_and_merge_provenance(self):
        cases = {'scenarios': [dict(id='a', turns=[dict(query='same', scripted_decision=['search_actuators', {'service': 'on_off'}])]),
                               dict(id='b', turns=[dict(query='same', scripted_decision=['search_actuators', {'service': 'on_off'}])]),
                               dict(id='c', turns=[dict(query='ambiguous', expect={'tool': 'get_actuator'})])]}
        rows = loader.examples_from_cases(cases)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sources'], ['a', 'b'])
        cases['scenarios'].append(dict(id='d', turns=[dict(query='same', scripted_decision=['search_actuators', {'service': 'modulating'}])]))
        self.assertEqual(loader.examples_from_cases(cases), [])

    def test_alternative_expected_decisions_are_not_training_labels(self):
        cases = {'scenarios': [dict(id='ambiguous', turns=[dict(query='help',
            scripted_decision=['search_actuators', {}], expect_any=[{'tool': 'search_actuators'}, {'tool': 'ask_clarification'}])])]}
        self.assertEqual(loader.examples_from_cases(cases), [])

    def test_flag_needs_model_and_respects_false(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(embeddings.enabled())
        with patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL='fake', EMBEDDINGS_ENABLED='false'):
            self.assertFalse(embeddings.enabled())
        with patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL='fake', EMBEDDINGS_ENABLED='true'):
            self.assertTrue(embeddings.enabled())

    def test_threshold_and_opposite_margin(self):
        self.assertEqual(embeddings.classify({'hazard': .90, 'safe_area': .89}), set())
        self.assertEqual(embeddings.classify({'hazard': .90, 'safe_area': .30}), {'hazard'})
        self.assertEqual(embeddings.classify({'on_off': .9, 'modulating': .91}), set())
        self.assertEqual(embeddings.classify({'hazard': .2}), set())

    def test_compound_hazard_queries_can_request_confirmation(self):
        # Frozen Google smoke scores: adding supply values diluted both site queries.
        self.assertIn('hazard', embeddings.classify({'hazard': .64154, 'safe_area': .61843}))
        self.assertIn('hazard', embeddings.classify({'hazard': .66432, 'safe_area': .64683}))
        for scores in [dict(hazard=.64345, safe_area=.63869),  # generic process actuator
                       dict(hazard=.71088, safe_area=.69921),  # gas-free safe area
                       dict(hazard=.73775, safe_area=.89590),  # no flammable material
                       dict(hazard=.57474, safe_area=.52067)]:  # hot water
            self.assertNotIn('hazard', embeddings.classify(scores))

    def test_bad_vectors_rejected(self):
        for vector in ([0.] * 768, [1.], [float('nan')] * 768):
            with self.assertRaises(ValueError):
                embeddings.vector_literal(vector)

    def test_failure_falls_back_without_leaking_error(self):
        with patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL='fake', EMBEDDINGS_ENABLED='true'):
            with patch.object(embeddings, 'embed_query', side_effect=TimeoutError('private payload')):
                result = embeddings.retrieve(None, 'new wording')
        self.assertFalse(result.available)
        self.assertEqual(result.accepted, set())
        self.assertNotIn('private', str(result.debug()))

    def test_disabled_does_not_embed_or_query(self):
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='false'):
            with patch.object(embeddings, 'embed_query', side_effect=AssertionError):
                result = embeddings.retrieve(None, 'query')
        self.assertEqual(result.debug(), {'examples': [], 'concepts': {}, 'embedding_ms': 0})


@unittest.skipUnless(os.getenv('SERIES76_TEST_DB') == '1', 'local PostgreSQL opt-in')
class EmbeddingDatabaseTests(unittest.TestCase):
    def setUp(self):
        from backend.catalog.cli import local_environment
        from backend.catalog.db import connect, migrate
        local_environment()
        self.connection = connect()
        migrate(self.connection)
        self.connection.commit()
        self.addCleanup(self.connection.close)
        self.addCleanup(self.connection.rollback)
        self.fake = FakeEmbedder()
        self.connection.execute('DELETE FROM series76.example_bank WHERE model=%s', (self.fake.model,))
        self.connection.execute('DELETE FROM series76.concept_anchor WHERE model=%s', (self.fake.model,))

    def test_loader_idempotence_retrieval_order_and_heldout_exclusion(self):
        rows = [dict(text=t, interpretation={'tool': 'search_actuators', 'args': {}}, sources=[source])
                for t, source in [('valve gas', 'heldout'), ('valve gas plant', 'training')]]
        anchors = {'hazard': ['valve gas'], 'safe_area': ['safe zone']}
        count = loader.load(self.connection, rows, anchors, self.fake.model, self.fake.embed_documents)
        self.assertEqual(count, 4)
        self.assertEqual(loader.load(self.connection, rows, anchors, self.fake.model,
                                     lambda _: self.fail('idempotent load made a paid call')), 0)
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model):
            with patch.object(embeddings, 'embed_query', self.fake.embed_query):
                result = embeddings.retrieve(self.connection, 'valve gas')
                heldout = embeddings.retrieve(self.connection, 'valve gas', exclude_sources=['heldout'])
        self.assertTrue(result.available)
        self.assertEqual([r['text'] for r in result.examples], ['valve gas', 'valve gas plant'])
        self.assertEqual(len(heldout.examples), 1)
        self.assertEqual(heldout.examples[0]['text'], 'valve gas plant')
        self.assertIn('hazard', result.accepted)

    def test_subset_reload_preserves_heldout_source_association(self):
        original = [dict(text='valve gas', interpretation={'tool': 'search_actuators', 'args': {}},
                         sources=['training', 'heldout'])]
        loader.load(self.connection, original, {'hazard': ['valve gas']}, self.fake.model, self.fake.embed_documents)
        subset = [dict(original[0], sources=['training'])]
        loader.load(self.connection, subset, {}, self.fake.model, lambda _: self.fail('unexpected embedding'))
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model):
            with patch.object(embeddings, 'embed_query', self.fake.embed_query):
                result = embeddings.retrieve(self.connection, 'valve gas', exclude_sources=['heldout'])
        self.assertEqual(result.examples, [])

    def test_authoritative_version_retires_conflicting_and_withdrawn_examples(self):
        cases = {'scenarios': [dict(id='original', turns=[dict(query='valve gas',
                  scripted_decision=['search_actuators', {'service': 'on_off'}])])]}
        original = loader.examples_from_cases(cases)
        withdrawn = dict(text='withdrawn text', interpretation={'tool': 'search_actuators', 'args': {}}, sources=['withdrawn'])
        loader.load(self.connection, original + [withdrawn], {'hazard': ['valve gas']}, self.fake.model,
                    self.fake.embed_documents, dataset_version='v1', authoritative=True)
        cases['scenarios'].append(dict(id='conflicting', turns=[dict(query='valve gas',
                  scripted_decision=['search_actuators', {'service': 'modulating'}])]))
        loader.load(self.connection, loader.examples_from_cases(cases), {}, self.fake.model,
                    lambda _: self.fail('unexpected embedding'), dataset_version='v2', authoritative=True,
                    provenance=loader.source_associations(cases))
        rows = list(self.connection.execute('SELECT text,source,active FROM series76.example_bank WHERE model=%s', (self.fake.model,)))
        self.assertEqual(len(rows), 2)
        self.assertFalse(any(r['active'] for r in rows))
        import json
        sources = json.loads(next(r['source'] for r in rows if r['text'] == 'valve gas'))
        self.assertEqual(set(sources), {'original', 'conflicting'})
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model):
            with patch.object(embeddings, 'embed_query', self.fake.embed_query):
                self.assertEqual(embeddings.retrieve(self.connection, 'valve gas').examples, [])

    def test_authoritative_versions_are_required_and_immutable(self):
        row = dict(text='gas', interpretation={'tool': 'search_actuators', 'args': {}}, sources=['a'])
        with self.assertRaises(ValueError):
            loader.load(self.connection, [row], {}, self.fake.model, self.fake.embed_documents, authoritative=True)
        loader.load(self.connection, [row], {}, self.fake.model, self.fake.embed_documents,
                    authoritative=True, dataset_version='immutable')
        with self.assertRaises(ValueError):
            loader.load(self.connection, [], {}, self.fake.model, lambda _: self.fail('unexpected embedding'),
                        authoritative=True, dataset_version='immutable')

    def test_sql_failure_preserves_outer_transaction(self):
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model):
            with patch.object(embeddings, 'embed_query', self.fake.embed_query):
                # Invalid provenance fails within retrieval's real SQL savepoint.
                self.connection.execute('''INSERT INTO series76.example_bank
                    (text,interpretation,source,model,dim,embedding) VALUES ('bad','{}','not-json',%s,768,%s::vector)''',
                    (self.fake.model, embeddings.vector_literal(self.fake.embed_query('bad'))))
                result = embeddings.retrieve(self.connection, 'bad')
        self.assertFalse(result.available)
        self.assertEqual(self.connection.execute('SELECT 1 AS n').fetchone()['n'], 1)

    def test_unloaded_model_uses_legacy_normalizer(self):
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model):
            with patch.object(embeddings, 'embed_query', self.fake.embed_query):
                result = embeddings.retrieve(self.connection, 'new wording')
        self.assertFalse(result.available)

    def test_sql_uses_remaining_deadline_and_restores_caller_timeout(self):
        import time
        connection = self.connection
        before = connection.execute('SHOW statement_timeout').fetchone()['statement_timeout']
        class DelayedConnection:
            def transaction(self, **kwargs):
                return connection.transaction(**kwargs)
            def execute(self, sql, params=None):
                if 'SELECT id, text, interpretation' in sql:
                    connection.execute('SELECT pg_sleep(.25)')
                return connection.execute(sql, params)
        def embed(text):
            time.sleep(.06)
            return self.fake.embed_query(text)
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL=self.fake.model), \
             patch.object(embeddings, 'RETRIEVAL_TIMEOUT_S', .15), \
             patch.object(embeddings, 'embed_query', side_effect=embed):
            start = time.monotonic()
            result = embeddings.retrieve(DelayedConnection(), 'gas')
            elapsed = time.monotonic() - start
        self.assertFalse(result.available)
        self.assertLess(elapsed, .3)
        self.assertEqual(connection.execute('SHOW statement_timeout').fetchone()['statement_timeout'], before)
        self.assertEqual(connection.execute('SELECT 1 AS n').fetchone()['n'], 1)


if __name__ == '__main__':
    unittest.main()
