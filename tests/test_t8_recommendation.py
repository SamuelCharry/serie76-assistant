"""Deterministic recommendation evidence from PostgreSQL rows."""
from test_agent_scenarios import Base


class RecommendationTests(Base):
    def test_provisional_and_refined_ranking(self):
        first = self.turn("I need an on/off actuator with at least 70 Nm",
                          ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        self.assertEqual(first.recommendation["shown"], 3)
        self.assertIn("Closest torque", first.answer)
        self.assertEqual(len(first.context["last_ranked_list"]), first.recommendation["total"])
        from backend.conversation.agent import run_agent
        second = run_agent(self.connection, "Submit", self.history, self.context,
                           answers={"supply_voltage_v": "110", "enclosure": "explosionproof"})
        self.assertEqual(second.recommendation["total"], 10)
        self.assertEqual(second.recommendation["shown"], 3)
        self.assertEqual(second.recommendation["items"][0]["part_number"],
                         second.context["last_ranked_list"][0])
        self.assertIn("Closest torque", second.lead)

    def test_no_match_has_nearest_with_failed_requirement(self):
        result = self.turn("On/off, 110 V, at least 100000 Nm",
                           ("search_actuators", {"service": "on_off", "supply_voltage_v": 110,
                                                   "min_torque_nm": 100000}))
        self.assertEqual(result.recommendation["total"], 0)
        self.assertLessEqual(len(result.recommendation["items"]), 2)
        self.assertTrue(all("fails" in item["reason"].lower() for item in result.recommendation["items"]))

    def test_inch_pound_request_ranks_published_inch_pounds(self):
        result = self.turn('On/off over 1000 in-lb',
                           ('search_actuators', {'service': 'on_off', 'min_torque_in_lb': {'value': 1000, 'op': 'gt'}}))
        self.assertIn('1000 in-lb', result.recommendation['ranked_by'])
        self.assertIn('in-lb', result.recommendation['items'][0]['reason'])
