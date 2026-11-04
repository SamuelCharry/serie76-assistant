from test_agent_scenarios import Base


class GlossaryScenarioTests(Base):
    def test_mining_context_asks_before_enclosure_filter(self):
        result = self.turn('actuator for a mining site, 220 V',
                           ('search_actuators', {'supply_voltage_v': 220, 'enclosure': 'explosionproof'}))
        self.assertEqual(result.interaction['kind'], 'question')
        question = result.interaction['questions'][0]
        self.assertEqual(question['id'], 'enclosure')
        self.assertNotIn('enclosure', result.context['filters'])
        self.assertEqual(str(result.context['filters']['supply_voltage_v']), '220')
        self.assertTrue(all(':' in option['label'] and option['count'] > 0 for option in question['options']))
        self.assertEqual(result.suggested_replies[0], 'Compare top 2')
