"""Manual T6 regressions: scripted interpretation, real SQL, no provider calls."""
from unittest.mock import patch

from test_agent_scenarios import Base
from backend.catalog.models import SearchFilters
from backend.catalog.repository import search_actuators
from backend.conversation import store
from uuid import uuid4

QUERIES = [
    "Necesito las especificaciones del modelo 761A00-11300000/A. ¿Cuál es su torque On/Off y su velocidad de operación a 60Hz?",
    "rRecomiéndame un actuador Explosionproof para 24V DC en servicio Modulating, que tenga un torque mayor a 1,000 In-Lbs.",
    "Busco un actuador para exteriores que sea muy rápido y no consuma mucha energía.",
    "¿Tienen algún modelo de la serie 76 que soporte 100,000 In-Lbs de torque en 110V?",
    "no", "cancelar",
    "Actually, cancel that. Can you tell me about hydraulic pumps?",
    "Actually, cancel that Do you have any series 76 actuator that supports over 100,000 In-Lbs of torque at 110V?",
]


class ManualQualityTests(Base):
    def assert_replies(self, result):
        self.assertEqual(len(result.suggested_replies), 3)
        self.assertEqual(len(set(result.suggested_replies)), 3)
        self.assertTrue(all(isinstance(s, str) and s.strip() for s in result.suggested_replies))

    def test_01_multi_focus_60hz(self):
        result = self.turn(QUERIES[0], ("get_actuator", {
            "part_numbers": ["761A00-11300000/A"],
            "focus": [{"field": "torque", "service": "on_off"}, {"field": "operating_time", "frequency_hz": 60}]}))
        self.assertIn("700 in-lb / 80 Nm", result.answer)
        self.assertIn("17 s", result.answer)
        for text in ["Modulating torque", "50 Hz", "FLA", "LRA", "Motor power", "Duty S4"]:
            self.assertNotIn(text, result.answer)
        self.assert_replies(result)

    def test_02_strict_torque(self):
        result = self.turn(QUERIES[1], ("search_actuators", {
            "enclosure": "explosionproof", "supply_voltage_v": 24, "supply_current": "DC",
            "service": "modulating", "min_torque_in_lb": {"value": 1000, "op": "gt"}}))
        self.assertEqual(len(result.products), 3)
        self.assertIn("> 1000 in-lb", result.answer)
        self.assertTrue(all(p["measurements"]["modulating_torque_in_lb"] > 1000 for p in result.products))
        self.assert_replies(result)

    def test_03_preference_ranking(self):
        result = self.turn(QUERIES[2], ("search_actuators", {
            "enclosure": "weatherproof", "sort_by": ["fastest", "lowest_power"]}))
        self.assertEqual(len(result.products), 3)
        self.assertIn("Operating time", result.answer)
        self.assertIn("Motor power", result.answer)
        self.assertNotIn("torque:", result.answer)
        self.assertEqual(result.answer.count("?"), 1)
        self.assert_replies(result)

    def impossible(self, query, cancel=False):
        result = self.turn(query, ("search_actuators", {
            "supply_voltage_v": 110, "min_torque_in_lb": {"value": 100000, "op": "gt" if cancel else "gte"},
            "cancel_previous": cancel}))
        self.assertIsNone(result.clarification)
        self.assertEqual(result.products, [])
        self.assertIn("No actuator", result.answer)
        self.assertIn("Closest published", result.answer)
        self.assertNotIn("?", result.answer)
        self.assert_replies(result)
        return result

    def test_04_impossible_before_clarification(self):
        self.impossible(QUERIES[3])

    def pending(self):
        return self.turn("I need at least 70 Nm", ("search_actuators", {"min_torque_nm": 70}))

    def test_05_decline_does_not_repeat(self):
        previous = self.pending()
        self.assertIsNotNone(previous.clarification)
        result = self.turn(QUERIES[4], ("ask_clarification", {"field": "decline"}))
        self.assertIsNone(result.clarification)
        self.assertNotEqual(result.answer, previous.answer)
        self.assertNotIn("?", result.answer)
        self.assert_replies(result)

    def test_06_cancel_clears_context_without_catalogue_tool(self):
        self.pending()
        with patch("backend.conversation.agent.search_actuators", side_effect=AssertionError("cancel queried catalogue")), \
             patch("backend.conversation.agent.get_actuator", side_effect=AssertionError("cancel queried catalogue")):
            result = self.turn(QUERIES[5], ("ask_clarification", {"field": "cancel"}))
        self.assertFalse(result.context.get("filters"))
        self.assertFalse(result.context.get("pending_clarification"))
        self.assertIn("Cancelled", result.answer)
        self.assert_replies(result)

    def test_07_cancel_and_out_of_scope(self):
        self.pending()
        result = self.turn(QUERIES[6], ("ask_clarification", {"field": "unsupported", "cancel_previous": True}))
        self.assertIn("Cancelled", result.answer)
        self.assertIn("Series 76", result.answer)
        self.assertFalse(result.context.get("filters"))
        self.assert_replies(result)

    def test_08_cancel_then_impossible(self):
        self.pending()
        result = self.impossible(QUERIES[7], cancel=True)
        self.assertIn("Cancelled", result.answer)
        self.assertNotIn("min_torque_nm", result.context.get("filters", {}))

    def test_strict_boundaries_and_legacy_scalars(self):
        def codes(op, value):
            result = search_actuators(self.connection, SearchFilters(service="on_off", supply_voltage_v=110,
                min_torque_nm={"value": value, "op": op}, limit=100))
            return {p["base_part_number"] for p in result["products"]}
        self.assertIn("761A00-11300000/A", codes("gte", 80))
        self.assertNotIn("761A00-11300000/A", codes("gt", 80))
        less = search_actuators(self.connection, SearchFilters(max_motor_power_w={"value": 15, "op": "lt"}, limit=100))
        inclusive = search_actuators(self.connection, SearchFilters(max_motor_power_w=15, limit=100))
        self.assertTrue(all(p["measurements"]["motor_power_w"] < 15 for p in less["products"]))
        self.assertGreater(inclusive["total"], less["total"])

    def test_comparison_diff_only_and_persisted_payload(self):
        result = self.turn("Compare 761A00-11300000/A vs 761B00-11300000/A", ("get_actuator", {
            "part_numbers": ["761A00-11300000/A", "761B00-11300000/A"]}))
        self.assertEqual(len(result.comparison["models"]), 2)
        self.assertGreater(result.comparison["identical_fields_hidden"], 0)
        self.assertTrue(all(row["a"] != row["b"] for row in result.comparison["rows"]))
        self.assertTrue(all(row["better"] in (None, "a", "b") for row in result.comparison["rows"]))
        self.assertNotIn("|", result.answer)
        sid = uuid4()
        store.append_turn(self.connection, sid, "Compare", result, new=True)
        saved = store.history(self.connection, sid)[-1]
        self.assertEqual(saved["comparison"], result.comparison)
        self.assertEqual(saved["suggested_replies"], result.suggested_replies)

    def test_three_candidates_offer_sql_verified_pairs(self):
        result = self.turn("Compare 761A00-11300000/A, 761B00-11300000/A and 762A00-11300000/A", ("get_actuator", {
            "part_numbers": ["761A00-11300000/A", "761B00-11300000/A", "762A00-11300000/A"]}))
        self.assertIsNone(result.comparison)
        self.assertEqual(result.products, [])
        self.assertTrue(all(reply.startswith("Compare ") for reply in result.suggested_replies))

    def test_ranked_sql_order_and_persisted_focus_followup(self):
        actual = search_actuators(self.connection, SearchFilters(enclosure="weatherproof", sort_by=["fastest", "lowest_power"], limit=3))
        expected = self.connection.execute("""SELECT e.base_part_number FROM series76.entries e
            JOIN series76.catalog_state c ON c.active_import_id=e.import_id
            WHERE e.enclosure='weatherproof' AND e.data_status='reported'
            ORDER BY (SELECT min(f.operating_time_s) FROM series76.frequency_specs f WHERE f.entry_id=e.id) ASC NULLS LAST,
                e.motor_power_w ASC NULLS LAST,e.base_part_number LIMIT 3""").fetchall()
        self.assertEqual([p["base_part_number"] for p in actual["products"]], [r["base_part_number"] for r in expected])
        self.turn(QUERIES[0], ("get_actuator", {"part_numbers": ["761A00-11300000/A"], "focus": [{"field": "operating_time", "frequency_hz": 60}]}))
        follow = self.turn("Show it again", ("get_actuator", {"part_numbers": ["761A00-11300000/A"]}))
        self.assertIn("at 60 Hz: 17 s", follow.answer)
        self.assertNotIn("at 50 Hz", follow.answer)

    def test_cancel_and_decline_override_stale_scripted_decisions(self):
        self.pending()
        declined = self.turn("no", ("ask_clarification", {"field": "service"}))
        self.assertIsNone(declined.clarification)
        self.pending()
        with patch("backend.conversation.agent.search_actuators", side_effect=AssertionError("catalogue ran")):
            cancelled = self.turn("cancelar", ("search_actuators", {}))
        self.assertIn("Cancelled", cancelled.answer)
        self.assertFalse(cancelled.context.get("filters"))

    def test_filtered_search_renders_only_the_requested_frequency(self):
        result = self.turn("On/off at 110 V and 60 Hz, operating time up to 18 seconds", ("search_actuators", {
            "service": "on_off", "supply_voltage_v": 110, "frequency_hz": 60,
            "max_operating_time_s": {"value": 18, "op": "lte"}}))
        self.assertTrue(result.products)
        self.assertIn("Operating time at 60 Hz: 17 s", result.answer)
        self.assertNotIn("at 50 Hz", result.answer)
