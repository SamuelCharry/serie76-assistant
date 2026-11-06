"""Metric winners shared by several models need a plural verdict."""
from backend.conversation.metrics import verdict
import unittest


def product(code, duty):
    return {'base_part_number': code, 'measurements': {'on_off_duty_s4_percent': duty}}


class MetricTieTests(unittest.TestCase):
    def test_tied_winners_use_plural_verb(self):
        text, winner = verdict([product('A', 70), product('B', 70), product('C', 40)],
                               'highest duty', {'service': 'on_off'})
        self.assertIn('A, B tie for the highest duty S4: 70 %.', text)
        self.assertIsNone(winner)
