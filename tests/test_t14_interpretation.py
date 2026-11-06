"""Plan B boundary tests: reject schema misuse and preserve SQL-owned ordering."""
import unittest
from pydantic import ValidationError
from backend.conversation import interpretation, ranking, agent, tool_wire, catalogue_answers


class InterpretationTests(unittest.TestCase):
    def test_priority_validation(self):
        for args in ({'metric':'price','direction':'lowest'}, {'metric':'torque','direction':'best'},
                     {'metric':'fla','direction':'lowest','frequency_hz':True},
                     {'metric':'torque','direction':'highest','condition':'ignore SQL'}):
            with self.assertRaises(ValidationError):
                interpretation.Priority.model_validate(args)

    def test_unknown_keep_rejected(self):
        with self.assertRaises(ValueError):
            interpretation.keep_fields(['not_a_filter'])

    def test_unsupported_is_bounded_and_sanitized(self):
        names = interpretation.unsupported_items(['warranty<script>\n!', 'x'*100, 'torque'])
        self.assertTrue(all(len(n) <= 40 and '<' not in n and '\n' not in n for n in names))
        self.assertNotIn('torque', names)
        with self.assertRaises(ValueError):
            interpretation.unsupported_items(['warranty']*9)

    def test_both_directions_missing_last_and_label_matches(self):
        products = [dict(base_part_number=str(i), measurements=dict(motor_power_w=value), services=[])
                    for i,value in enumerate([20,None,10])]
        for direction, first in [('highest','0'),('lowest','2')]:
            key = interpretation.priority_key(dict(metric='motor_power',direction=direction))
            ranked = ranking.rank(products,{},key)
            self.assertEqual(ranked[0]['base_part_number'],first)
            self.assertEqual(ranked[-1]['base_part_number'],'1')
            self.assertIn(direction,ranking.ranked_by({},key))

    def test_wire_lists_validate_without_new_enums(self):
        schema = agent.schemas(['fla'])['search_actuators']
        args = schema.model_validate(tool_wire.canonical_arguments('search_actuators',dict(
            keep='service,supply_voltage_v',unsupported_requests='price,warranty',
            priority=dict(metric='starts',direction='highest'))))
        self.assertEqual(args.keep,['service','supply_voltage_v'])
        self.assertEqual(args.unsupported_requests,['price','warranty'])

    def test_torque_delivery_is_not_shipping(self):
        for text in ('entrega de torque','entrega más par','entrega mayor torque'):
            self.assertFalse(catalogue_answers.limitations(text))
        self.assertTrue(catalogue_answers.limitations('fecha de entrega'))

    def test_history_grounding_does_not_license_stale_or_assistant_values(self):
        turn = object.__new__(agent.Turn)
        turn.context={'filters':{'supply_voltage_v':220}, 'withdrawn_fields':['max_motor_power_w']}
        turn.messages=[dict(role='user',content='110 V and 40 W'),dict(role='assistant',content='500 Nm')]
        self.assertTrue(turn.carried_value('supply_voltage_v',220,{'refine':True}))
        self.assertFalse(turn.carried_value('supply_voltage_v',110,{'refine':True}))
        self.assertFalse(turn.carried_value('max_motor_power_w',40,{'refine':True}))
        self.assertFalse(turn.carried_value('min_torque_nm',500,{'refine':True}))

    def test_rate_priority_reads_the_matching_service(self):
        products = [dict(base_part_number=str(i), measurements={}, services=[
            dict(service='modulating',starts_per_hour=starts,cycles_per_hour=None),
            dict(service='on_off',starts_per_hour=None,cycles_per_hour=cycles)])
            for i,starts,cycles in [(0,100,30),(1,200,20)]]
        self.assertEqual(ranking.rank(products,{'service':'modulating'},'highest_starts')[0]['base_part_number'],'1')
        self.assertEqual(ranking.rank(products,{'service':'on_off'},'most_cycles')[0]['base_part_number'],'0')
        self.assertIsNone(ranking.measurement(products[0],'starts',{'service':'on_off'}))


if __name__ == '__main__':
    unittest.main()
