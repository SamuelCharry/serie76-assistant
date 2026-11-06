"""No inference: exercise startup, contention and cold-provider deadline boundaries."""
import concurrent.futures
import os
import threading
import time
import unittest
from unittest.mock import Mock, patch

from backend.conversation import embeddings


class EmbeddingDeadlineTests(unittest.TestCase):
    def test_delayed_budget_reservation_cannot_start_an_abandoned_request(self):
        release, finished = threading.Event(), threading.Event()
        fake = Mock()
        def reserve():
            release.wait(2)
            finished.set()
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL='fake'), \
             patch.object(embeddings, 'RETRIEVAL_TIMEOUT_S', .08), \
             patch.object(embeddings, 'client', return_value=fake), \
             patch('backend.conversation.agent.reserve_agent_call', side_effect=reserve):
            try:
                result = embeddings.retrieve(None, 'query')
            finally:
                release.set()
            self.assertTrue(finished.wait(1))
            self.assertFalse(result.available)
            # Let the worker leave the guard before checking its provider boundary.
            time.sleep(.03)
            fake.embed_documents.assert_not_called()

    def test_cold_client_initialization_is_inside_retrieval_deadline(self):
        release, finished = threading.Event(), threading.Event()
        fake = Mock()

        def cold_client(*args, **kwargs):
            release.wait(2)
            finished.set()
            return fake

        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL='fake'), \
             patch.object(embeddings, 'RETRIEVAL_TIMEOUT_S', .08, create=True), \
             patch.object(embeddings, 'client', side_effect=cold_client), \
             patch('backend.conversation.agent.reserve_agent_call') as reserve:
            try:
                started = time.monotonic()
                result = embeddings.retrieve(None, 'cold query')
                elapsed = time.monotonic() - started
            finally:
                release.set()
            self.assertTrue(finished.wait(1))
            self.assertLess(elapsed, .4)
            self.assertFalse(result.available)
            fake.embed_documents.assert_not_called()
            reserve.assert_not_called()

    def test_concurrent_cold_requests_initialize_one_cached_client(self):
        embeddings._client.cache_clear()
        fake = Mock()
        def construct(**kwargs):
            time.sleep(.03)
            return fake
        with patch.dict(os.environ, OPENROUTER_EMBEDDING_MODEL='concurrent-test', OPENROUTER_API_KEY='test-only',
                        EMBEDDING_API_KEY='', EMBEDDING_BASE_URL=''), \
             patch('langchain_openai.OpenAIEmbeddings', side_effect=construct) as constructor:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
                results = list(workers.map(lambda _: embeddings.client(), range(4)))
        self.assertEqual(constructor.call_count, 1)
        self.assertTrue(all(r is fake for r in results))
        embeddings._client.cache_clear()

    def test_fastapi_startup_warms_without_inference(self):
        from fastapi.testclient import TestClient
        from backend.app.main import app
        fake = Mock()
        with patch.dict(os.environ, EMBEDDINGS_ENABLED='true', OPENROUTER_EMBEDDING_MODEL='fake'), \
             patch.object(embeddings, 'client', return_value=fake) as get_client:
            with TestClient(app) as api:
                self.assertEqual(api.get('/health').status_code, 200)
        get_client.assert_called_once()
        fake.embed_documents.assert_not_called()


if __name__ == '__main__':
    unittest.main()
