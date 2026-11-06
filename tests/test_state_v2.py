"""State contract validators and isolated executor, no provider calls."""
from copy import deepcopy
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.conversation import state_v2 as v2


def proposal(**updates):
    raw = dict(intent='search', filters=[], priority=[], references=[], unsupported_requests=[],
               pending_question='', site_context={'hazard': 'unknown'}, view={})
    raw.update(updates)
    return raw


def constraint(field='min_torque_nm', value='45', op='gte', unit='Nm', evidence='at least 45 Nm', **extra):
    return dict(field=field, value=value, op=op, unit=unit, evidence=evidence, **extra)


class StateValidators(unittest.TestCase):
    def validate(self, raw, query='at least 45 Nm', messages=(), context=None):
        return v2.validate(None, raw, query, messages, context or {}, [])

    def rejected(self, raw, query='at least 45 Nm', messages=(), context=None):
        with self.assertRaises(v2.Rejected):
            self.validate(raw, query, messages, context)

    def test_full_state_required(self):
        for missing in ('filters', 'priority', 'references', 'unsupported_requests', 'pending_question', 'site_context'):
            raw = proposal()
            del raw[missing]
            self.rejected(raw)

    def test_unknown_fields_and_intents(self):
        self.rejected(proposal(intent='make_up_answer'))
        self.rejected(proposal(answer='45 Nm'))
        self.rejected(proposal(filters=[constraint(field='price')]))

    def test_validation_errors_do_not_echo_model_authored_prose(self):
        raw = proposal()
        raw['This model has 999 W motor power'] = True
        with self.assertRaises(v2.Rejected) as caught:
            self.validate(raw)
        self.assertNotIn('999', str(caught.exception))

    def test_unknown_operator(self):
        self.rejected(proposal(filters=[constraint(op='approximately')]))

    def test_quoted_number_and_dimension(self):
        got = self.validate(proposal(filters=[constraint()]))
        self.assertEqual(got[2]['min_torque_nm'], {'value': 45, 'op': 'gte'})

    def test_invented_number_rejected(self):
        self.rejected(proposal(filters=[constraint(value='46')]))

    def test_same_number_wrong_dimension_rejected(self):
        self.rejected(proposal(filters=[constraint(evidence='45 V')]), '45 V')

    def test_part_number_digits_cannot_be_current_evidence(self):
        text = '761A00-11300000/A'
        self.rejected(proposal(filters=[constraint('max_fla_a', '761', 'lte', 'A', text)]), text)

    def test_unquoted_value_in_assistant_is_rejected(self):
        self.rejected(proposal(filters=[constraint(evidence='at least 45 Nm')]), 'Choose it',
                      [{'role': 'assistant', 'content': 'at least 45 Nm'}])

    def test_earlier_user_values_are_allowed(self):
        self.validate(proposal(filters=[constraint()]), 'Retain the torque',
                      [{'role': 'user', 'content': 'at least 45 Nm'}])

    def test_server_validated_evidence_survives_history_window(self):
        self.validate(proposal(filters=[constraint()]), 'Retain the torque',
                      context={'_v2_user_evidence': ['at least 45 Nm']})

    def test_decimal_comma_and_no_rounding(self):
        self.validate(proposal(filters=[constraint(value='1.5', evidence='1,5 Nm')]), '1,5 Nm')
        self.rejected(proposal(filters=[constraint(value='15', evidence='1,5 Nm')]), '1,5 Nm')
        self.rejected(proposal(filters=[constraint(value='1.00000000000000001', evidence='1.00000000000000001 Nm')]), '1.00000000000000001 Nm')

    def test_nonfinite_negative_large_and_boolean_rejected(self):
        for value in ('NaN', 'Infinity', '-1', '1000000000001', 'true'):
            self.rejected(proposal(filters=[constraint(value=value)]))

    def test_illegal_units_rejected(self):
        self.rejected(proposal(filters=[constraint(unit='kN')]))

    def test_range_and_equality_preserve_both_ends(self):
        got = self.validate(proposal(filters=[constraint(value='45', upper='75', op='range', evidence='45 to 75 Nm')]), '45 to 75 Nm')
        self.assertEqual(got[2]['min_torque_nm'], [{'value': 45, 'op': 'gte'}, {'value': 75, 'op': 'lte'}])
        got = self.validate(proposal(filters=[constraint(op='eq')]))
        self.assertEqual(len(got[2]['min_torque_nm']), 2)

    def test_bad_range_and_duplicate_direction_rejected(self):
        self.rejected(proposal(filters=[constraint(upper='75')]))
        self.rejected(proposal(filters=[constraint(op='range', upper='20', evidence='45 to 20 Nm')]), '45 to 20 Nm')
        self.rejected(proposal(filters=[constraint(), constraint()]))

    def test_categorical_evidence_and_values(self):
        self.validate(proposal(filters=[constraint('service', 'modulating', 'eq', '', 'hold midway')]), 'hold midway')
        self.rejected(proposal(filters=[constraint('service', 'imaginary', 'eq', '', 'hold midway')]), 'hold midway')
        self.rejected(proposal(filters=[constraint('service', 'modulating', 'eq', '', 'not said')]))
        self.rejected(proposal(filters=[constraint('service', 'modulating', 'gt', '', 'hold midway')]), 'hold midway')

    def test_categorical_duplicates_rejected(self):
        c = constraint('service', 'modulating', 'eq', '', 'hold midway')
        self.rejected(proposal(filters=[c, c]), 'hold midway')

    def test_boolean_requires_exact_value(self):
        self.validate(proposal(filters=[constraint('dc_only', 'true', 'eq', '', 'DC only')]), 'DC only')
        self.rejected(proposal(filters=[constraint('dc_only', 'yes', 'eq', '', 'DC only')]), 'DC only')

    def test_dimension_aliases(self):
        for field, unit, text, value in [('supply_voltage_v', 'V', '110-volt power', '110'),
                                        ('phase_count', 'phase', 'three-phase', '3'),
                                        ('min_starts_per_hour', 'starts/h', 'starts >= 1200 per hour', '1200'),
                                        ('min_torque_in_lb', 'in-lb', '75 in-lb', '75')]:
            with self.subTest(field=field):
                self.validate(proposal(filters=[constraint(field, value, 'eq' if field in ('supply_voltage_v', 'phase_count') else 'gte', unit, text)]), text)

    def test_dc_frequency_conflict(self):
        text = 'DC only at 60 Hz'
        self.rejected(proposal(filters=[constraint('dc_only', 'true', 'eq', '', text),
                                        constraint('frequency_hz', '60', 'eq', 'Hz', text)]), text)

    def test_priority_replaces_without_lexicon_gate(self):
        text = 'Put shorter travel ahead of every other criterion'
        p = dict(metric='operating_time', direction='lowest', evidence=text)
        got = self.validate(proposal(priority=[p]), text)
        self.assertEqual(got[4], ['fastest'])
        for field, value in (('metric', 'price'), ('direction', 'sideways'), ('frequency_hz', True)):
            bad = dict(p, **{field: value})
            self.rejected(proposal(priority=[bad]), text)

    def test_priority_frequency_requires_evidence_and_state_scope(self):
        p = dict(metric='operating_time', direction='lowest', frequency_hz=60, evidence='quickest at 60 Hz')
        self.rejected(proposal(priority=[p]), 'quickest at 60 Hz')
        self.validate(proposal(priority=[p], filters=[constraint('frequency_hz', '60', 'eq', 'Hz', 'quickest at 60 Hz')]), 'quickest at 60 Hz')

    def test_full_state_omission_removes_instead_of_merging(self):
        got = self.validate(proposal(), context={'filters': {'min_torque_nm': 45}})
        self.assertEqual(got[2], {})

    def test_unknown_hazard_state_and_missing_evidence_rejected(self):
        self.rejected(proposal(site_context={'hazard': 'maybe'}))
        self.rejected(proposal(site_context={'hazard': 'no'}))

    def test_optional_evidence_cannot_poison_later_grounding(self):
        self.rejected(proposal(site_context={'hazard': 'unknown', 'evidence': '999 Nm'}))
        self.rejected(proposal(view={'evidence': '999 Nm'}))

    def test_positive_hazard_cannot_be_hidden(self):
        self.rejected(proposal(), 'For solvent storage')
        self.rejected(proposal(site_context={'hazard': 'no', 'evidence': 'For solvent storage'}), 'For solvent storage')

    def test_hazard_cannot_be_cleared_by_removing_filter(self):
        old = {'state_v2': {'site_context': {'hazard': 'yes'}}}
        self.rejected(proposal(), 'Remove enclosure', context=old)
        self.rejected(proposal(site_context={'hazard': 'no', 'evidence': 'ordinary room'}), 'Remove enclosure',
                      [{'role': 'user', 'content': 'ordinary room'}], old)
        self.validate(proposal(site_context={'hazard': 'no', 'evidence': 'ordinary room now'}), 'ordinary room now', context=old)

    def test_pending_question_must_be_legal_and_unsupplied(self):
        self.rejected(proposal(pending_question='unknown'))
        self.rejected(proposal(filters=[constraint()], pending_question='min_torque_nm'))
        self.rejected(proposal(filters=[constraint('frequency_hz', '60', 'eq', 'Hz', '60 Hz')], pending_question='frequency'), '60 Hz')

    def test_focus_topic_glossary_and_frequency_are_validated(self):
        for view in ({'focus': ['invented']}, {'focus': ['torque', 'torque']}, {'topic': 'invented'},
                     {'terms': ['IP67']}, {'frequency_hz': 60, 'evidence': '45 Nm'},
                     {'service': 'imaginary', 'evidence': '45 Nm'}, {'offset': -1}, {'limit': 101}):
            self.rejected(proposal(view=view))

    def test_unsupported_labels_cannot_emit_model_prose(self):
        self.rejected(proposal(unsupported_requests=['power is 999 W']))
        self.rejected(proposal(unsupported_requests=['price', 'price']))
        self.validate(proposal(unsupported_requests=['warranty']))

    def test_duplicate_priority_rejected(self):
        p = dict(metric='torque', direction='highest', evidence='strongest')
        self.rejected(proposal(priority=[p, p]), 'strongest')

    def test_structured_controls_validate_options_and_keep_units(self):
        ctx = dict(filters={'enclosure': 'weatherproof'},
                   pending_questions=[dict(id='supply_voltage_v', options=[dict(value='110')])],
                   last_ranked_list=['761A00-11300000/A', '762A00-11300000/A'])
        text = v2.validated_controls(ctx, {'supply_voltage_v': '110'}, ['enclosure'], None)
        self.assertIn('110 V', text)
        self.assertEqual(ctx['filters'], {'enclosure': 'weatherproof'})
        for answers, removed, action in [({'supply_voltage_v': '999'}, [], None),
                                         ({}, ['service'], None),
                                         ({}, ['enclosure', 'enclosure'], None),
                                         ({}, [], {'type': 'compare_top', 'args': {'n': True}}),
                                         ({}, [], {'type': 'show_all', 'args': {'extra': 1}}),
                                         ({'supply_voltage_v': '110'}, [], {'type': 'show_all', 'args': {}})]:
            with self.assertRaises(v2.Rejected):
                v2.validated_controls(ctx, answers, removed, action)

    def test_reference_operation_cannot_smuggle_numbers(self):
        self.rejected(proposal(filters=[constraint(reference='761A00-11300000/A')]))

    def test_missing_references_and_unseen_pick_rejected(self):
        self.rejected(proposal(intent='lookup'))
        self.rejected(proposal(intent='compare'))
        self.rejected(proposal(intent='recommend_from_shown'))

    def test_schema_budget(self):
        from scripts.check_tool_schemas import metrics
        from langchain_core.utils.function_calling import convert_to_openai_tool
        result = metrics([convert_to_openai_tool(t) for t in v2.declarations()])
        self.assertLessEqual(result['enum_values'], 108)
        self.assertLess(result['bytes'], 5520)
        self.assertEqual(result['forbidden_nodes'], 0)
        self.assertLessEqual(result['depth'], 7)


@unittest.skipUnless(os.environ.get('SERIES76_TEST_DB') == '1', 'requires isolated test DB')
class StateDatabaseTests(unittest.TestCase):
    def setUp(self):
        from backend.catalog.db import connect
        self.connection = connect()
        self.addCleanup(self.connection.close)

    def validate(self, raw, query, context=None):
        return v2.validate(self.connection, raw, query, [], context or {}, [])

    def test_existing_and_missing_codes(self):
        good = '761A00-11300000/A'
        self.validate(proposal(intent='lookup', references=[good]), good)
        for code in ('769Z99-11300000/A', '761A00-11300001/A', '761'):
            with self.assertRaises(v2.Rejected):
                self.validate(proposal(intent='lookup', references=[code]), code)

    def test_unique_user_prefix_and_model_only_prefix(self):
        got = self.validate(proposal(intent='lookup', references=['761A00-11300000']), '761A00-11300000')
        self.assertEqual(got[1]['references'], ['761A00-11300000/A'])
        self.assertTrue(got[5])
        with self.assertRaises(v2.Rejected):
            self.validate(proposal(intent='lookup', references=['761A00-11300000']), 'show the actuator')

    def test_ambiguous_and_near_codes_offer_only_real_candidates(self):
        from backend.catalog.repository import get_actuator
        for code in ('761A00', '761A00-11300001/A'):
            result = self.run_decision(proposal(intent='lookup', references=[code]), code)
            candidates = result.clarification['options']
            self.assertTrue(0 < len(candidates) <= 3)
            self.assertTrue(all(get_actuator(self.connection, c) for c in candidates))
            self.assertFalse(result.products)
            self.assertIsNone(result.recommendation)

    def test_assistant_only_code_cannot_ground_reference(self):
        with self.assertRaises(v2.Rejected):
            v2.validate(self.connection, proposal(intent='lookup', references=['761A00-11300000/A']),
                        'show it', [{'role': 'assistant', 'content': '761A00-11300000/A'}], {}, [])

    def test_shown_reference_and_subset(self):
        code = '761A00-11300000/A'
        self.validate(proposal(intent='recommend_from_shown', references=[code]), 'pick', {'on_screen': [code]})
        with self.assertRaises(v2.Rejected):
            self.validate(proposal(intent='recommend_from_shown', references=[code]), code, {'on_screen': []})

    def test_symbolic_sql_reference_provenance(self):
        code = '761A00-11300000/A'
        query = 'A stronger On/Off model on the same voltage'
        raw = proposal(filters=[constraint('service', 'on_off', 'eq', '', query),
                                constraint('min_torque_nm', '', 'gt', '', query, reference=code),
                                constraint('supply_voltage_v', '', 'eq', '', query, reference=code)])
        got = self.validate(raw, query, {'on_screen': [code]})
        self.assertEqual(got[6]['min_torque_nm'], 'from reference ' + code)
        self.assertEqual(got[2]['supply_voltage_v'], 110)

    def run_decision(self, raw, query, context=None):
        from scripts.agent_acceptance import IdealModel
        from backend.conversation.agent import run_agent
        with patch.dict(os.environ, {'AGENT_STATE_MODE': 'v2'}):
            return run_agent(self.connection, query, [], context or {}, model=IdealModel((v2.TOOL, raw)))

    def test_v1_interpretation_functions_are_never_called(self):
        from contextlib import ExitStack
        paths = ['backend.conversation.agent._turn', 'backend.conversation.agent.finish',
                 'backend.conversation.policy.colloquial_requirements', 'backend.conversation.policy.merge_filters',
                 'backend.conversation.policy.sort_grounded', 'backend.conversation.requirement_coverage.apply',
                 'backend.conversation.requirement_coverage.unsupported']
        with ExitStack() as stack:
            for path in paths:
                stack.enter_context(patch(path, side_effect=AssertionError('v1 path used')))
            result = self.run_decision(proposal(filters=[constraint()]), 'at least 45 Nm')
        self.assertTrue(result.recommendation)
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)

    def test_invalid_proposal_keeps_previous_state_without_products(self):
        previous = {'filters': {'service': 'on_off'}, 'state_v2': {'filters': []}}
        original = deepcopy(previous)
        result = self.run_decision(proposal(filters=[constraint(value='999')]), 'at least 45 Nm', previous)
        self.assertEqual(previous, original)
        self.assertEqual(result.context['state_v2'], original['state_v2'])
        self.assertEqual(result.products, [])
        self.assertIsNone(result.recommendation)
        self.assertIsNotNone(result.clarification)

    def test_integrity_failure_rejects_whole_result(self):
        with patch.object(v2.integrity, 'satisfies', return_value=False):
            result = self.run_decision(proposal(filters=[constraint()]), 'at least 45 Nm')
        self.assertFalse(result.products)
        self.assertIsNone(result.recommendation)
        self.assertIn('independent', result.answer)

    def test_hazard_never_recommends_weatherproof(self):
        query = 'Weatherproof for solvent storage'
        raw = proposal(filters=[constraint('enclosure', 'weatherproof', 'eq', '', query)],
                       site_context={'hazard': 'yes', 'evidence': query})
        result = self.run_decision(raw, query)
        self.assertIsNone(result.recommendation)
        self.assertEqual(result.clarification['field'], 'enclosure')

    def test_multiple_calls_rejected_without_second_decision(self):
        class Model:
            def bind_tools(self, *args, **kwargs):
                return self
            def invoke(self, *args, **kwargs):
                return SimpleNamespace(tool_calls=[dict(name=v2.TOOL, args=proposal())] * 2, response_metadata={})
        result = v2.run(self.connection, 'find models', [], {}, model=Model())
        self.assertFalse(result.products)
        self.assertEqual(result.tool_calls[0]['model']['decision_calls'], 1)


if __name__ == '__main__':
    unittest.main()
