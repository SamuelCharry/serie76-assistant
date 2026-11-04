"""Deterministic recommendation evidence from PostgreSQL rows."""
from test_agent_scenarios import Base


class RecommendationTests(Base):
    def test_provisional_and_refined_ranking(self):
        first = self.turn("I need an on/off actuator with at least 70 Nm",
                          ("search_actuators", {"service": "on_off", "min_torque_nm": 70}))
        self.assertEqual(first.recommendation["shown"], 3)
        self.assertIn("Ranked by closest torque", first.answer)
        self.assertEqual(len(first.context["last_ranked_list"]), first.recommendation["total"])
        from backend.conversation.agent import run_agent
        second = run_agent(self.connection, "Submit", self.history, self.context,
                           answers={"supply_voltage_v": "110", "enclosure": "explosionproof"})
        self.assertEqual(second.recommendation["total"], 10)
        self.assertEqual(second.recommendation["shown"], 3)
        self.assertEqual(second.recommendation["items"][0]["part_number"],
                         second.context["last_ranked_list"][0])
        self.assertIn("Ranked by closest torque", second.lead)

    def test_no_match_has_nearest_with_failed_requirement(self):
        result = self.turn("On/off, 110 V, at least 100000 Nm",
                           ("search_actuators", {"service": "on_off", "supply_voltage_v": 110,
                                                   "min_torque_nm": 100000}))
        self.assertEqual(result.recommendation["total"], 0)
        self.assertLessEqual(len(result.recommendation["items"]), 2)
        self.assertTrue(all("fails" in item["reason"].lower() for item in result.recommendation["items"]))

    def test_inch_pound_request_ranks_published_inch_pounds(self):
        result = self.turn('On/off over 1000 in-lb',
                           ('search_actuators', {'service': 'on_off', 'min_torque_in_lb': {'value': 1000, 'op': 'gt'}}))
        self.assertIn('1000 in-lb', result.recommendation['ranked_by'])
        self.assertIn('in-lb', result.recommendation['items'][0]['reason'])

    def test_unscoped_minimum_shows_only_qualifying_service_torque(self):
        result = self.turn('At least 100 Nm', ('search_actuators', {'min_torque_nm': 100}))
        for entry in result.recommendation['items']:
            torque = [v for v in entry['key_values'] if 'torque' in v['label'].lower()]
            self.assertTrue(torque)
            self.assertTrue(all(float(v['value'].split()[0]) >= 100 for v in torque))
            self.assertTrue(all(v['label'] != 'Torque' for v in torque))
            self.assertNotIn('70 Nm torque', entry['reason'])

    def test_fastest_reason_names_time_and_frequency(self):
        result = self.turn('Fastest 60 Hz on/off at 110 V',
                           ('search_actuators', {'service': 'on_off', 'frequency_hz': 60,
                                                 'supply_voltage_v': 110, 'sort_by': ['fastest']}))
        for entry in result.recommendation['items']:
            self.assertIn('Operating time at 60 Hz', entry['reason'])
            self.assertTrue(any(v['label'] == 'Operating time at 60 Hz' for v in entry['key_values']))

    def test_comparison_rows_are_visible_differences(self):
        result = self.turn('Compare 761X30-11370000/A vs 761X30-11380000/A',
                           ('get_actuator', {'part_numbers': ['761X30-11370000/A', '761X30-11380000/A'],
                                             'focus': ['overview']}))
        self.assertTrue(all(len(set(row['values'])) > 1 for row in result.comparison['rows']))

    def test_colloquial_service_and_knm_are_applied_without_model_guess(self):
        result = self.turn('Open and close at least 1.5 kNm',
                           ('search_actuators', {'min_torque_nm': 1500}))
        self.assertEqual(result.context['filters']['service'], 'on_off')
        self.assertEqual(float(result.context['filters']['min_torque_nm']), 1500)
        self.assertIn('1.5 kNm = 1500 Nm', result.answer)

    def test_hazardous_options_have_short_labels_and_descriptions(self):
        result = self.turn('Refinery with flammable gas',
                           ('search_actuators', {}))
        question = result.interaction['questions'][0]
        self.assertEqual(question['id'], 'enclosure')
        self.assertEqual({o['label'] for o in question['options']}, {'Explosionproof', 'Weatherproof'})
        self.assertTrue(all(o.get('description') for o in question['options']))
        self.assertEqual(result.recommendation['items'][0]['part_number'][:4], '761X')

    def test_pick_after_list_is_one_model_without_question(self):
        self.turn('On/off at least 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, 'Just pick one', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertTrue(result.answer.startswith('My pick: '))
        self.assertEqual(len(result.recommendation['items']), 1)
        self.assertIsNone(result.interaction)
        self.assertFalse(result.debug['llm_called'])

    def test_why_explains_current_ranking_without_table(self):
        self.turn('On/off at least 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, 'Why?', self.history, self.context,
                           model=Raising(AssertionError('LLM must not run')))
        self.assertIn('closest torque', result.answer)
        self.assertNotIn(' vs ', result.answer)
        self.assertFalse(result.debug['llm_called'])

    def test_next_paginates_and_that_one_uses_last_shown_first(self):
        self.turn('On/off at least 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        next_result = run_agent(self.connection, 'next', self.history, self.context,
                                model=Raising(AssertionError('LLM must not run')))
        self.assertEqual(len(next_result.products), 3)
        self.assertEqual(next_result.products[0]['base_part_number'], self.context['last_ranked_list'][3])
        that = run_agent(self.connection, 'that one', self.history, next_result.context,
                         model=Raising(AssertionError('LLM must not run')))
        self.assertIn(next_result.products[0]['base_part_number'], that.answer)

    def test_unresolved_question_lists_current_candidates_without_spec_dump(self):
        self.turn('On/off at least 70 Nm', ('search_actuators', {'service': 'on_off', 'min_torque_nm': 70}))
        result = self.turn('no', ('ask_clarification', {'field': 'decline'}))
        self.assertNotIn('unresolved scopes are not assumed', result.answer)
        self.assertNotIn('Source:', result.answer)

    def test_document_limitations_do_not_dump_specs(self):
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        for query in ('how much does 761A00-11300000/A cost?',
                      'what is the IP rating of the weatherproof models?',
                      'Do you have Rotork actuators?'):
            with self.subTest(query=query):
                result = run_agent(self.connection, query, [], {},
                                   model=Raising(AssertionError('LLM must not run')))
                self.assertIn('catalogue', result.answer.lower())
                self.assertNotIn('Source:', result.answer)
                self.assertFalse(result.debug['llm_called'])

    def test_asterisk_uses_stored_footnote(self):
        from backend.conversation.agent import run_agent
        from test_agent_scenarios import Raising
        result = run_agent(self.connection, 'what does the asterisk on 766A00-11320000/A mean?',
                           [], {}, model=Raising(AssertionError('LLM must not run')))
        self.assertIn('Sizes 6 and 7 are not CSA Certified', result.answer)
        self.assertNotIn('On/Off torque', result.answer)
