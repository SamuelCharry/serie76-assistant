"""Pure policy tests: canonical codes, grounding, follow-up merge and contradictions. No DB, no network."""
import unittest

from backend.conversation import policy


class CodeTests(unittest.TestCase):
    def test_canonicalises_case_spaces_and_missing_hyphen_but_never_completes(self):
        self.assertEqual(policy.canonical_code("761A00-11300000/A"), ("761A00-11300000/A", None))
        code, note = policy.canonical_code(" 761a00-11300000/a ")
        self.assertEqual(code, "761A00-11300000/A")
        self.assertIn("Interpreted", note)
        self.assertEqual(policy.canonical_code("761A0011300000/A")[0], "761A00-11300000/A")
        # Missing /A or truncated: not completed, returned as a prefix for suggestions.
        self.assertEqual(policy.canonical_code("761A00-11300000"), (None, "761A00-11300000"))
        self.assertEqual(policy.canonical_code("761A00"), (None, "761A00"))
        self.assertEqual(policy.canonical_code("hello world!")[0], None)

    def test_codes_in_text(self):
        text = "compare 761A00-11300000/A with 761a0011330c00/a please"
        self.assertEqual(policy.codes_in_text(text), ["761A00-11300000/A", "761A00-11330C00/A"])


class GroundingTests(unittest.TestCase):
    def test_numbers_must_appear_in_conversation(self):
        texts = ["I need at least 70 Nm on 24VAC, 1,200 starts"]
        self.assertEqual(policy.grounding_errors({"min_torque_nm": "70", "supply_voltage_v": "24"}, [], texts), [])
        self.assertEqual(policy.grounding_errors({"min_starts_per_hour": 1200}, [], texts), [])
        self.assertEqual(policy.grounding_errors({"min_torque_nm": "80"}, [], texts), ["min_torque_nm"])

    def test_categorical_values_need_user_wording_or_quoted_assumption(self):
        texts = ["I need an actuator that can stop at any point of its travel"]
        self.assertEqual(policy.grounding_errors({"service": "modulating"}, [], texts), ["service"])
        assumption = [{"field": "service", "user_phrase": "stop at any point"}]
        self.assertEqual(policy.grounding_errors({"service": "modulating"}, assumption, texts), [])
        self.assertEqual(policy.grounding_errors({"supply_current": "DC"}, [], ["24 V DC please"]), [])
        self.assertEqual(policy.grounding_errors({"supply_current": "AC"}, [], ["24VAC"]), [])
        self.assertEqual(policy.grounding_errors({"supply_current": "DC"}, [], ["a decent actuator"]), ["supply_current"])
        self.assertEqual(policy.grounding_errors({"enclosure": "explosionproof"}, [], ["hazardous area with gas"]), [])

    def test_invented_assumption_phrase_is_detected(self):
        bad = [{"field": "service", "user_phrase": "precise flow control"}]
        self.assertEqual(policy.invalid_assumptions(bad, ["just an actuator"]), bad)

    def test_assumption_can_ground_a_number_from_glossary_wording(self):
        texts = ["standard North American voltage"]
        assumption = [{"field": "supply_voltage_v", "user_phrase": "north american voltage"}]
        self.assertEqual(policy.grounding_errors({"supply_voltage_v": "110"}, assumption, texts), [])


class MergeTests(unittest.TestCase):
    PREVIOUS = {"service": "on_off", "supply_voltage_v": "24", "min_torque_nm": "70",
                "min_cycles_per_hour": 30, "limit": 5, "offset": 0}

    def test_refine_keeps_previous_constraints(self):
        merged, notes = policy.merge_filters(self.PREVIOUS, {"supply_voltage_v": "110"}, refine=True, remove=[], more=False)
        self.assertEqual(merged["supply_voltage_v"], "110")
        self.assertEqual(merged["min_torque_nm"], "70")
        self.assertEqual(merged["service"], "on_off")
        self.assertEqual(merged["offset"], 0)
        self.assertEqual(notes, [])

    def test_new_request_does_not_inherit(self):
        merged, _ = policy.merge_filters(self.PREVIOUS, {"service": "modulating"}, refine=False, remove=[], more=False)
        self.assertNotIn("min_torque_nm", merged)

    def test_remove_implies_refining_the_previous_search(self):
        merged, _ = policy.merge_filters(self.PREVIOUS, {}, refine=False, remove=["min_torque_nm"], more=False)
        self.assertEqual((merged["service"], merged["supply_voltage_v"]), ("on_off", "24"))
        self.assertNotIn("min_torque_nm", merged)

    def test_remove_and_more(self):
        merged, _ = policy.merge_filters(self.PREVIOUS, {}, refine=True, remove=["min_torque_nm"], more=False)
        self.assertNotIn("min_torque_nm", merged)
        more, _ = policy.merge_filters(self.PREVIOUS, {}, refine=False, remove=[], more=True)
        self.assertEqual((more["offset"], more["min_torque_nm"]), (5, "70"))

    def test_service_change_drops_incompatible_carried_rate_and_says_so(self):
        merged, notes = policy.merge_filters(self.PREVIOUS, {"service": "modulating"}, refine=True, remove=[], more=False)
        self.assertNotIn("min_cycles_per_hour", merged)
        self.assertEqual(merged["min_torque_nm"], "70")
        self.assertIn("cycles/hour", notes[0])


class ConflictTests(unittest.TestCase):
    def test_contradictions_are_named(self):
        self.assertEqual(policy.conflicts({"supply_current": "DC", "frequency_hz": 60})[0][0], "dc_frequency")
        self.assertEqual(policy.conflicts({"supply_current": "DC", "phase_count": 3})[0][0], "dc_phase")
        self.assertEqual(policy.conflicts({"service": "modulating", "min_cycles_per_hour": 10})[0][0], "cycles_modulating")
        self.assertEqual(policy.conflicts({"service": "on_off", "min_starts_per_hour": 10})[0][0], "starts_on_off")
        self.assertEqual(policy.conflicts({"min_cycles_per_hour": 1, "min_starts_per_hour": 1})[0][0], "both_rates")
        self.assertEqual(policy.conflicts({"supply_current": "AC", "frequency_hz": 60}), [])

    def test_describe_is_readable(self):
        self.assertEqual(policy.describe({"service": "on_off", "min_torque_nm": "70", "frequency_hz": 60}),
                         "On/Off service, 60 Hz, torque ≥ 70 Nm")


if __name__ == "__main__":
    unittest.main()
