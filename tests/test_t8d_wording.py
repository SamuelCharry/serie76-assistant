"""Search prose lists ranked models once and names open choices naturally."""
from test_agent_scenarios import Base


class WordingTests(Base):
    def test_sorted_search_does_not_repeat_top_three(self):
        result = self.turn('Explosionproof, 110 V, modulating, at least 300 Nm, rank by current',
                           ('search_actuators', {'enclosure': 'explosionproof', 'supply_voltage_v': 110,
                                                 'service': 'modulating', 'min_torque_nm': 300,
                                                 'sort_by': ['lowest_current']}))
        for item in result.recommendation['items']:
            self.assertEqual(result.answer.count(item['part_number']), 1)

    def test_unresolved_uses_open_choice_sentence(self):
        self.turn('I need at least 70 Nm', ('search_actuators', {'min_torque_nm': 70}))
        result = self.turn('no', ('ask_clarification', {'field': 'decline'}))
        self.assertIn('Without service', result.answer)
        self.assertNotIn('I can narrow these further', result.answer)
