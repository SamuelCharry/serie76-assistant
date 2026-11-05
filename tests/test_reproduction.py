"""Clean-checkout regressions: authenticated verification and keyless walkthrough."""
import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch

from backend.conversation.agent import run_agent, single_field_code
from scripts import load_example_bank, verify_catalog_db
from test_agent_scenarios import Base, Scripted


class VerifierTests(unittest.TestCase):
    def test_login_then_protected_http_without_leaking_token(self):
        requests = []

        def respond(request, timeout):
            requests.append(request)
            if request.full_url.endswith('/api/auth/login'):
                self.assertEqual(json.loads(request.data), {
                    'email': 'demo@series76.test', 'password': 'Series76-Demo-1'})
                self.assertIsNone(request.get_header('Authorization'))
                response = io.BytesIO(b'{"access_token":"test-token"}')
            else:
                self.assertEqual(request.get_header('Authorization'), 'Bearer test-token')
                response = io.BytesIO(b'{"total":5}')
            response.status = 200
            return response

        with patch.object(verify_catalog_db.urllib.request, 'urlopen', side_effect=respond):
            token = verify_catalog_db.demo_login('http://localhost:18000')
            self.assertEqual(verify_catalog_db.http('http://localhost:18000',
                             '/api/actuators/search', {'service': 'on_off'}, token=token),
                             (200, {'total': 5}))
        self.assertEqual(len(requests), 2)

    def test_http_error_preserves_status(self):
        error = urllib.error.HTTPError('http://localhost', 401, 'Unauthorized', {},
                                       io.BytesIO(b'{"error":"unauthorized"}'))
        with patch.object(verify_catalog_db.urllib.request, 'urlopen', side_effect=error):
            self.assertEqual(verify_catalog_db.http('http://localhost', '/api/actuators/x')[0], 401)
            error.fp.seek(0)
            with self.assertRaisesRegex(RuntimeError, 'Demo login failed.*401'):
                verify_catalog_db.demo_login('http://localhost')

    def test_api_port_default_and_override(self):
        for port, expected in [('', '8000'), ('18000', '18000')]:
            with patch.dict(os.environ, {'API_PORT': port}):
                self.assertEqual(verify_catalog_db.default_base_url(), f'http://127.0.0.1:{expected}')


class BankPreviewTests(unittest.TestCase):
    def test_model_free_dry_run_never_opens_db_or_provider(self):
        with patch.dict(os.environ, {'OPENROUTER_EMBEDDING_MODEL': ''}), \
                patch('sys.argv', ['load_example_bank.py', '--dry-run']), \
                patch.object(load_example_bank, 'connect', side_effect=AssertionError('DB used')), \
                patch.object(load_example_bank, 'local_environment', side_effect=AssertionError('env read')), \
                patch.object(load_example_bank.embeddings, 'embed_documents', side_effect=AssertionError('paid call')), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(load_example_bank.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report['examples'], 658)
        self.assertEqual(report['anchors'], 100)
        self.assertEqual(report['pending_texts'], 758)
        self.assertEqual(report['scope'], 'input_only')
        self.assertFalse(report['existing_vectors_checked'])


class SingleFieldRecognitionTests(unittest.TestCase):
    def test_only_closed_requests_qualify(self):
        code = '761A00-11300000/A'
        for query in [f'What is the motor power of {code}?', f'FLA of {code} at 60 Hz',
                      f'operating time of {code}', f'power of {code.lower()}',
                      f'on/off torque of {code}', f'LRA for {code}']:
            with self.subTest(query=query):
                self.assertEqual(single_field_code(query), code)
        for query in [f'power and torque of {code}', f'FLA of {code} at 50 Hz and 60 Hz',
                      'motor power of 761A00', 'power of 761A00-11300000',
                      f'power of {code} for a hazardous site', f'is power of {code} under 20 W?',
                      f'power of {code} or 761B00-11300000/A', f'lowest power of {code}',
                      f'not power of {code}', f'power of XX{code}', f'power of {code}X',
                      f'power of {code}, and explain IP67', f'FLA of {code} at 55 Hz',
                      f'on/off modulating torque of {code}', f'power of {code} instead']:
            with self.subTest(query=query):
                self.assertIsNone(single_field_code(query))


class SingleFieldScenarioTests(Base):
    def test_readme_and_scoped_queries_match_scripted_model_bytes(self):
        code = '761A00-11300000/A'
        for query in [f'What is the motor power of {code}?', f'FLA of {code} at 60 Hz',
                      f'operating time of {code}', f'on/off torque of {code}']:
            with self.subTest(query=query):
                model = Scripted(('get_actuator', {'part_numbers': [code]}))
                interpreted = run_agent(self.connection, query, [], {}, model=model)
                self.assertIsNotNone(model.seen)
                with patch.dict(os.environ, {'OPENROUTER_API_KEY': '', 'OPENROUTER_CHAT_MODEL': '',
                                              'EMBEDDINGS_ENABLED': 'false'}), \
                        patch('backend.conversation.agent.create_model_client', side_effect=AssertionError('LLM used')), \
                        patch('backend.conversation.embeddings.embed_documents', side_effect=AssertionError('embedding used')):
                    keyless = run_agent(self.connection, query, [], {})
                self.assertEqual(keyless.answer.encode(), interpreted.answer.encode())
                self.assertEqual(keyless.products, interpreted.products)
                self.assertFalse(keyless.tool_calls[0]['model']['llm_called'])
                if query.startswith('What is'):
                    self.assertIn('15 W', keyless.answer)

    def test_ambiguous_and_unknown_code_reach_model(self):
        for query in ['power and torque of 761A00-11300000/A',
                      'motor power of 999Z99-99999999/A']:
            model = Scripted(('get_actuator', {'part_numbers': ['761A00-11300000/A']}))
            with patch('backend.conversation.agent.create_model_client', return_value=model):
                run_agent(self.connection, query, [], {})
            self.assertIsNotNone(model.seen)
