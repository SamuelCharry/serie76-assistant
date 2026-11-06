"""T8 multi-question submission with real SQL and scripted interpretation."""
from test_agent_scenarios import Base
from backend.conversation.agent import InvalidInteraction, run_agent


class MultiQuestionTests(Base):
    def test_plain_voltage_answer_applies_pending_option_without_model(self):
        self.turn('On/off at least 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, '110 volts', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertEqual(str(result.context['filters']['supply_voltage_v']), '110')
        self.assertFalse(result.debug['llm_called'])

    def test_all_distinguishing_questions_have_sql_counts(self):
        result = self.turn("I need an on/off actuator with at least 70 Nm",
                           ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        questions = result.interaction["questions"]
        self.assertGreaterEqual(len(questions), 2)
        self.assertTrue(all(all(isinstance(o["count"], int) and o["count"] > 0
                                for o in q["options"]) for q in questions))
        self.assertEqual(len({q["id"] for q in questions}), len(questions))
        self.assertEqual([q['id'] for q in questions], ['supply_voltage_v', 'enclosure'])

    def test_redundant_partition_is_removed_but_cross_cutting_field_remains(self):
        from backend.conversation.interactions import questions
        facets = {
            'supply_voltage_v': [{'value': 110, 'n': 2, 'codes': ['A', 'B']},
                                 {'value': 220, 'n': 2, 'codes': ['C', 'D']}],
            'supply_current': [{'value': 'AC', 'n': 2, 'codes': ['A', 'B']},
                               {'value': 'DC', 'n': 2, 'codes': ['C', 'D']}],
            'enclosure': [{'value': 'weatherproof', 'n': 2, 'codes': ['A', 'C']},
                          {'value': 'explosionproof', 'n': 2, 'codes': ['B', 'D']}],
            'phase_count': [{'value': 1, 'n': 4, 'codes': ['A', 'B', 'C', 'D']}],
        }
        self.assertEqual([q['id'] for q in questions(facets, list(facets))],
                         ['supply_voltage_v', 'enclosure'])

    def test_empty_combination_is_rejected_atomically(self):
        first = self.turn("I need an on/off actuator with at least 70 Nm",
                          ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        from backend.catalog.repository import question_facets
        from backend.catalog.models import SearchFilters
        from backend.conversation.interactions import questions
        facets = question_facets(self.connection, SearchFilters.model_validate(self.context['filters']), ['supply_current'])
        self.context['pending_questions'] += questions(facets, ['supply_current'])
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
