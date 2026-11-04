"""Retry/fallback attempts are local fakes; no provider or model keys."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import httpx
import openai
from backend.conversation import agent


class Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, *args, **kwargs):
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value


class ResilienceTests(unittest.TestCase):
    def status(self, code):
        return openai.APIStatusError('fixture', response=httpx.Response(code, request=httpx.Request('POST', 'https://invalid.test')), body=None)

    def test_retry_503_counts_every_attempt(self):
        with patch.object(agent, 'reserve_agent_call') as reserve:
            response, attempts = agent.invoke_decision(Client([self.status(503), 'ok']), [], [], fallback=False)
        self.assertEqual(response, 'ok')
        self.assertEqual(reserve.call_count, 2)
        self.assertEqual([a['status'] for a in attempts], ['provider_error', 'ok'])

    def test_never_retry_or_fallback_4xx(self):
        for status in (400, 401, 402, 403, 429):
            with self.subTest(status=status), patch.object(agent, 'reserve_agent_call') as reserve, \
                 patch.object(agent, 'create_model_client', side_effect=AssertionError('fallback on 4xx')):
                with self.assertRaises(agent.AgentUnavailable):
                    agent.invoke_decision(Client([self.status(status)]), [], [], fallback=True)
                self.assertEqual(reserve.call_count, 1)

    def test_timeout_connection_and_fallback_are_bounded(self):
        request = httpx.Request('POST', 'https://invalid.test')
        with patch.dict(os.environ, {'OPENROUTER_FALLBACK_MODEL': 'fixture-fallback'}), \
             patch.object(agent, 'create_model_client', return_value=Client(['ok'])) as factory, \
             patch.object(agent, 'reserve_agent_call') as reserve:
            response, attempts = agent.invoke_decision(Client([openai.APITimeoutError(request=request),
                                                               openai.APIConnectionError(request=request)]), [], [])
        self.assertEqual(response, 'ok')
        self.assertEqual(reserve.call_count, 3)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[-1]['model'], 'fixture-fallback')

    def test_local_budget_failure_is_not_retried(self):
        with patch.object(agent, 'reserve_agent_call', side_effect=agent.AgentUnavailable('rate_limited_local')) as reserve:
            with self.assertRaises(agent.AgentUnavailable):
                agent.invoke_decision(Client(['unused']), [], [])
        self.assertEqual(reserve.call_count, 1)
