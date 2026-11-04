from test_agent_scenarios import Base
from backend.conversation.agent import InvalidInteraction, run_agent


class ActionTests(Base):
    def ranked(self):
        self.turn("I need an on/off actuator with at least 70 Nm",
                  ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))

    def test_compare_top_is_code_only(self):
        self.ranked()
        result = run_agent(self.connection, "Compare top 2", self.history, self.context,
                           action={"type": "compare_top", "args": {"n": 2}})
        self.assertEqual(result.comparison["models"], self.context["last_ranked_list"][:2])
        self.assertEqual(result.tool_calls[0]["model"]["decision_calls"], 0)

    def test_rank_by_fastest_and_show_all(self):
        self.ranked()
        ranked = run_agent(self.connection, "Rank by fastest", self.history, self.context,
                           action={"type": "rank_by", "args": {"by": "fastest"}})
        self.assertIn("Fastest operating time", ranked.answer)
        shown = run_agent(self.connection, "Show all", self.history, ranked.context,
                          action={"type": "show_all", "args": {}})
        self.assertEqual(len(shown.context["last_ranked_list"]), len(self.context["last_ranked_list"]))
        self.assertEqual(shown.tool_calls[0]["model"]["decision_calls"], 0)

    def test_no_list_is_422(self):
        with self.assertRaises(InvalidInteraction) as raised:
            run_agent(self.connection, "Compare top 2", [], {}, action={"type": "compare_top", "args": {"n": 2}})
        self.assertEqual(raised.exception.code, "no_results_to_act_on")
