from test_agent_scenarios import Base
from backend.conversation.agent import run_agent
from backend.conversation import store
from uuid import uuid4


class FastPathTests(Base):
    def test_exact_compare_needs_no_model(self):
        result = run_agent(self.connection,
                           "Compare 761A00-11300000/A vs 761B00-11300000/A", [], {})
        self.assertEqual(result.comparison['models'],
                         ['761A00-11300000/A', '761B00-11300000/A'])
        self.assertFalse(result.debug['llm_called'])
        self.assertEqual(result.debug['attempts'], 0)
        self.assertGreaterEqual(result.debug['latency_ms'], 0)
        message_id = store.append_turn(self.connection, uuid4(), "Compare 761A00-11300000/A vs 761B00-11300000/A",
                                       result, new=True)
        self.assertEqual(store.debug_for_message(self.connection, message_id)['debug']['llm_called'], False)

    def test_partial_or_extra_request_does_not_route(self):
        from backend.conversation.agent import fast_path_codes
        self.assertIsNone(fast_path_codes('Compare 761A00-11300000'))
        self.assertIsNone(fast_path_codes('Compare 761A00-11300000/A and explain FLA'))
