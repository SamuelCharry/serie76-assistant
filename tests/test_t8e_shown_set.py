"""References resolve to the exact ordered models shown to the user."""
from test_agent_scenarios import Base


class ShownSetTests(Base):
    def test_compare_top_three_uses_ranks_one_through_three(self):
        first = self.turn('weatherproof modulating 220 V', ('search_actuators', {
            'enclosure': 'weatherproof', 'service': 'modulating', 'supply_voltage_v': 220}))
        shown = [item['part_number'] for item in first.recommendation['items']]
        self.assertEqual(first.context['on_screen'], shown)
        second = self.turn('compare the top 3', ('get_actuator', {'from_results_top': 3}))
        self.assertEqual(second.comparison['models'], shown)
        self.assertEqual(second.context['on_screen'], shown)

    def test_hazardous_room_picks_matching_compared_enclosure(self):
        self.turn('compare 761A00-11300000/A and 761X30-11300000/A',
                  ('get_actuator', {'part_numbers': ['761A00-11300000/A', '761X30-11300000/A']}))
        result = self.turn('which is better for a hazardous room?',
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('761X30-11300000/A', result.answer)
        self.assertIn('Explosionproof', result.answer)
        self.assertNotIn('Comparing ', result.answer)

    def test_metric_winner_becomes_that_one(self):
        self.turn('compare 761Y30-11300000/A and 762Y30-11300000/A',
                  ('get_actuator', {'part_numbers': ['761Y30-11300000/A', '762Y30-11300000/A']}))
        winner = self.turn('which one cycles more per hour on/off?',
                           ('get_actuator', {'part_numbers': ['761Y30-11300000/A', '762Y30-11300000/A']}))
        self.assertEqual(winner.context['focused_model'], '761Y30-11300000/A')
        answer = self.turn('show me that one', ('ask_clarification', {'field': 'part_number'}))
        self.assertEqual(answer.products[0]['base_part_number'], '761Y30-11300000/A')

    def test_metric_question_without_explicit_reference_uses_screen(self):
        self.turn('On/off explosionproof 220 V with at least 40% duty',
                  ('search_actuators', {'service': 'on_off', 'enclosure': 'explosionproof',
                                        'supply_voltage_v': 220, 'min_duty_s4_percent': 40}))
        result = self.turn('which has the most cycles per hour?',
                           ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('190 cycles/h', result.answer)
        self.assertNotIn('Comparing ', result.answer)

    def test_better_duty_tie_and_reverse_comparison(self):
        first = self.turn('compare 762X30-11300000/A and 762Y30-11300000/A',
                          ('get_actuator', {'part_numbers': ['762X30-11300000/A', '762Y30-11300000/A']}))
        duty = self.turn('which has better duty?', ('ask_clarification', {'field': 'requirements'}))
        self.assertIn('Both', duty.answer)
        reverse = self.turn('the other way round', ('ask_clarification', {'field': 'requirements'}))
        self.assertEqual(reverse.comparison['models'], list(reversed(first.comparison['models'])))
