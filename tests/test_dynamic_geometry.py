"""Data changes and layout changes must not be replaced with memorized answers."""

import unittest
import importlib.util
if importlib.util.find_spec("numpy") is None:
    raise unittest.SkipTest("Optional geometry tests require requirements-ingest.lock.txt")

from catalog_ingest.geometry import (
    infer_columns,
    Token,
    GeometryError,
    supply_from_title,
)
from catalog_ingest.schema import parse_number, validate_measurements


def word(text, x, y, score=0.999):
    return Token(text, (x - 12, y - 5, x + 12, y + 5), score)


class DynamicGeometryTests(unittest.TestCase):
    def test_supply_heading_does_not_drop_thousands_or_phase_information(self):
        supply = supply_from_title("1,100V - Three-Phase Power")
        self.assertEqual(supply["supply_voltage_v"], 1100)
        self.assertEqual(supply["phase_count"], 3)
        self.assertEqual(supply_from_title("48V AC Power")["supply_current"], "AC")

    def test_ambiguous_supply_precision_is_not_rounded(self):
        with self.assertRaises(GeometryError):
            supply_from_title("1.234567890123456789V DC Power")

    def test_units_determine_torque_assignment_even_if_columns_move(self):
        tokens = [
            word("On/Off Output", 300, 100),
            word("Operating", 600, 100),
            word("Full Load", 750, 100),
            word("Locked Rotor", 900, 100),
            word("Cycles per Hour", 490, 100),
            word("Motor", 1020, 100),
        ]
        units = [
            ("Nm", 340),
            ("In-Lbs.", 260),
            ("S4%", 420),
            ("Cycles", 490),
            ("60 Hz", 570),
            ("50 Hz", 630),
            ("60 Hz", 720),
            ("50 Hz", 780),
            ("60 Hz", 870),
            ("50 Hz", 930),
            ("Watts", 1020),
        ]
        columns = infer_columns(
            [*tokens, *[word(t, x, 150) for t, x in units]], 150, 12
        )
        mapping = {c.field: c.center for c in columns}
        self.assertEqual(mapping["on_off_torque_nm"], 340)
        self.assertEqual(mapping["on_off_torque_in_lb"], 260)

    def test_number_parser_does_not_fix_dangerous_decimals_or_letters(self):
        self.assertEqual(parse_number("3.2"), 3.2)
        self.assertEqual(parse_number("17,700"), 17700)
        for text in ("BOO", "8:40", "1,2", "NaN", "inf", "-1"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_number(text)

    def test_excess_precision_is_rejected_instead_of_silently_rounded(self):
        with self.assertRaisesRegex(ValueError, "precision"):
            parse_number("1.234567890123456789")

    def test_physical_inversion_is_flagged_never_converted(self):
        problems = validate_measurements(
            {"on_off_torque_in_lb": 1100, "on_off_torque_nm": 9700}
        )
        self.assertTrue(any(p["code"] == "torque_unit_inconsistency" for p in problems))

    def test_valid_source_rounding_is_preserved(self):
        self.assertFalse(
            validate_measurements(
                {"modulating_torque_in_lb": 5520, "modulating_torque_nm": 640}
            )
        )

    def test_missing_unit_cannot_be_guessed_from_numeric_values(self):
        with self.assertRaises(GeometryError):
            infer_columns([word("unrecognized", 200, 150)], 150, 12)


if __name__ == "__main__":
    unittest.main()
