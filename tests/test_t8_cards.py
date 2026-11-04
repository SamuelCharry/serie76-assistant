from test_agent_scenarios import Base


class CardTests(Base):
    def test_filtered_fields_lead_then_highest_distinct(self):
        result = self.turn("Compare 761A00-11300000/A, 761B00-11300000/A and 762A00-11300000/A",
                           ("get_actuator", {"part_numbers": ["761A00-11300000/A", "761B00-11300000/A",
                                                               "762A00-11300000/A"], "focus": ["overview"]}))
        self.assertEqual(result.comparison['layout'], 'cards')
        self.assertEqual(result.comparison['key_fields_reason'],
                         'Fields you filtered on, then the ones that differ most')
        self.assertLessEqual(len(result.comparison['key_fields']), 4)
        self.assertTrue(all(field in [row['field'] for row in result.comparison['rows']]
                            for field in result.comparison['key_fields']))
