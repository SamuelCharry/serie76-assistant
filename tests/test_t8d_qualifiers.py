"""Unsupported selection qualifiers are stated instead of silently dropped."""
from test_agent_scenarios import Base


class QualifierTests(Base):
    def test_indoor_superlative_discloses_scope(self):
        result = self.turn('what is the biggest torque you have for indoors?',
                           ('search_actuators', {'sort_by': ['highest_torque']}))
        self.assertIn("doesn't classify models as indoor", result.answer)
        self.assertNotIn('enclosure', result.context['filters'])

    def test_quiet_and_compact_are_not_hidden(self):
        for query, word in [('quiet actuator, 110 V', 'quiet'),
                            ('compact actuator, 110 V', 'compact')]:
            with self.subTest(word=word):
                self.context = {}
                self.history = []
                result = self.turn(query, ('search_actuators', {'supply_voltage_v': 110}))
                self.assertIn("doesn't classify models as " + word, result.answer)
