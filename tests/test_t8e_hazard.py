"""Hazard confirmation and categorical alternatives keep the stated scope."""
from test_agent_scenarios import Base


class HazardTests(Base):
    def test_combustible_dust_confirmation_never_previews_weatherproof(self):
        first = self.turn('damper in a grain silo with combustible dust, 220 V',
                          ('search_actuators', {'supply_voltage_v': 220}))
        self.assertEqual(first.interaction['questions'][0]['id'], 'enclosure')
        self.assertTrue(all(item['part_number'][3] in 'XY' for item in first.recommendation['items']))
        second = self.turn('yes', ('search_actuators', {}))
        self.assertEqual(second.context['filters']['enclosure'], 'explosionproof')
        self.assertTrue(all(p['enclosure'] == 'explosionproof' for p in second.products))

    def test_not_classified_answers_weatherproof(self):
        self.turn('valve on an offshore platform deck, 110 V, on/off',
                  ('search_actuators', {'supply_voltage_v': 110, 'service': 'on_off'}))
        second = self.turn('no, the deck is not a classified area', ('search_actuators', {}))
        self.assertEqual(second.context['filters']['enclosure'], 'weatherproof')

    def test_three_phase_explosionproof_zero_alternatives_are_labeled(self):
        first = self.turn('explosionproof 3-phase modulating', ('search_actuators', {
            'enclosure': 'explosionproof', 'phase_count': 3, 'service': 'modulating'}))
        self.assertEqual(first.recommendation['total'], 0)
        self.assertIn('3-phase', first.answer)
        self.assertIn('Weatherproof', first.answer)
        self.assertIn('drop Explosionproof', first.answer)
        self.assertIn('drop 3-phase', first.answer)
        reasons = [item['reason'] for item in first.recommendation['items']]
        self.assertTrue(any('If you can drop Explosionproof' in reason for reason in reasons))
        self.assertTrue(any('If you can drop 3-phase' in reason for reason in reasons))
        follow = self.turn('so what can I do?', ('search_actuators', {}))
        self.assertEqual(follow.context['filters']['phase_count'], 3)
