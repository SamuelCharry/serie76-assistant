"""T8 multi-question submission with real SQL and scripted interpretation."""
from test_agent_scenarios import Base
from backend.conversation.agent import InvalidInteraction, run_agent


class MultiQuestionTests(Base):
    def test_all_distinguishing_questions_have_sql_counts(self):
        result = self.turn("I need an on/off actuator with at least 70 Nm",
                           ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        questions = result.interaction["questions"]
        self.assertGreaterEqual(len(questions), 2)
        self.assertTrue(all(all(isinstance(o["count"], int) and o["count"] > 0
                                for o in q["options"]) for q in questions))
        self.assertEqual(len({q["id"] for q in questions}), len(questions))

    def test_empty_combination_is_rejected_atomically(self):
        first = self.turn("I need an on/off actuator with at least 70 Nm",
                          ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        options = {q["id"]: [o["value"] for o in q["options"]] for q in first.interaction["questions"]}
        if not {"supply_voltage_v", "supply_current"} <= options.keys():
            self.skipTest("No cross-facet empty combination in current catalogue")
        before = dict(self.context)
        with self.assertRaises(InvalidInteraction) as raised:
            run_agent(self.connection, "Submit", self.history, self.context,
                      answers={"supply_voltage_v": "110", "supply_current": "AC/DC"})
        self.assertEqual(raised.exception.code, "empty_combination")
        self.assertEqual(self.context, before)

    def test_two_answers_apply_in_one_sql_turn(self):
        first = self.turn("I need an on/off actuator with at least 70 Nm",
                          ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        self.assertIn("enclosure", [q["id"] for q in first.interaction["questions"]])
        result = run_agent(self.connection, "Submit", self.history, self.context,
                           answers={"supply_voltage_v": "110", "enclosure": "explosionproof"})
        self.assertEqual(result.context["filters"]["supply_voltage_v"], "110")
        self.assertEqual(result.context["filters"]["enclosure"], "explosionproof")
        self.assertEqual(result.tool_calls[0]["model"]["decision_calls"], 0)
