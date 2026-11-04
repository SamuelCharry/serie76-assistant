from test_agent_scenarios import Base
from backend.conversation.agent import run_agent
from test_agent_scenarios import Scripted


class RankedReferences(Base):
    def ranked(self):
        self.turn("I need an on/off actuator with at least 70 Nm",
                  ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))

    def test_best_two_resolve_without_search(self):
        self.ranked()
        result = self.turn("Compare 2 of them the best ones",
                           ("get_actuator", {"from_results_top": 2, "focus": ["overview"]}))
        self.assertEqual(result.comparison["models"], self.context["last_ranked_list"][:2])
        self.assertEqual(result.tool_calls[0]["model"]["decision_calls"], 1)

    def test_which_ones_lists_ranked_codes(self):
        self.ranked()
        result = self.turn("wich ones ?", ("get_actuator", {"list_results": True}))
        self.assertIn(self.context["last_ranked_list"][0], result.answer)
        self.assertIn(str(len(self.context["last_ranked_list"])), result.answer)
