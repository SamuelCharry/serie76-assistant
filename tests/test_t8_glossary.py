from test_agent_scenarios import Base


class GlossaryScenarioTests(Base):
    def test_mining_context_accepts_explicit_explosionproof_tool_choice(self):
        result = self.turn('actuator for a mining site, 220 V',
                           ('search_actuators', {'supply_voltage_v': 220, 'enclosure': 'explosionproof'}))
        self.assertIsNone(result.interaction)
        self.assertEqual(result.context['filters']['enclosure'], 'explosionproof')
        self.assertEqual(int(result.context['filters']['supply_voltage_v']), 220)
        self.assertTrue(all(item['part_number'][3] in 'XY' for item in result.recommendation['items']))
        self.assertEqual(result.suggested_replies[0], 'Compare top 2')
