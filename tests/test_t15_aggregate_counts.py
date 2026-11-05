"""CSV oracles and real SQL, with scripted decisions only: no provider inference."""
import csv
import re
import unittest
from pathlib import Path

from backend.catalog.models import SearchFilters
from backend.catalog.repository import search_actuators, source_na_count
from backend.conversation import agent, catalogue_answers, policy
from test_agent_scenarios import Base, Raising


class CurrentScopeTests(unittest.TestCase):
    def test_dc_compatibility_does_not_require_dual_rating(self):
        for query in (
            'List the explosionproof units that accept a 24 V DC supply, including dual AC/DC units.',
            '24 V DC compatible units; include AC/DC models too.',
            'Explosionproof 24 V DC-only or AC/DC models.',
            'Modelos de 24 V DC, incluyendo AC/DC.',
        ):
            with self.subTest(query=query):
                self.assertEqual(policy.current_requirement(query), {'supply_current': 'DC', 'dc_only': False})
        for query in ('24 V DC only; exclude every AC/DC entry.', 'Only DC units, excluding AC/DC.'):
            self.assertEqual(policy.current_requirement(query), {'supply_current': 'DC', 'dc_only': True})
        self.assertEqual(policy.current_requirement('24 V AC/DC units'), {'supply_current': 'AC/DC', 'dc_only': False})
        self.assertEqual(policy.current_requirement('Only AC/DC units at 24 V; include DC compatibility information.'),
                         {'supply_current': 'AC/DC', 'dc_only': False})
        self.assertEqual(policy.current_requirement('DC units at 24 V, including weatherproof models.'),
                         {'supply_current': 'DC'})

    def test_exact_product_questions_never_become_aggregates(self):
        for query in (
            'Show the on/off torque and enclosure for 761Y30-11380000/A.',
            'Which enclosure does 761Y30-11380000/A have?',
            'For 761Y30-11380000/A, list the enclosure and on/off torque.',
        ):
            self.assertIsNone(catalogue_answers.answer(None, query))


class AggregateOracleTests(Base):
    def setUp(self):
        super().setUp()
        with (Path(__file__).resolve().parents[1] / 'data/extracted/series76/catalog.csv').open(
                encoding='utf-8-sig', newline='') as stream:
            self.rows = list(csv.DictReader(stream))

    def fresh(self):
        self.history, self.context = [], {}

    def keyless(self, query):
        return agent.run_agent(self.connection, query, [], {}, model=Raising(AssertionError('No inference')))

    def test_l1_05_original_and_paraphrases_correct_a_narrow_dual_decision(self):
        expected = {r['base_part_number'] for r in self.rows if r['enclosure'] == 'explosionproof'
                    and r['supply_voltage_v'] == '24' and r['supply_current'] in ('DC', 'AC/DC')
                    and r['data_status'] == 'reported'}
        for query in (
            'List the explosionproof units that accept a 24 V DC supply, including dual AC/DC units.',
            'Show all explosionproof 24 V DC compatible models, including AC/DC.',
            'Explosionproof units for 24 V DC; also include dual AC/DC models.',
        ):
            with self.subTest(query=query):
                self.fresh()
                result = self.turn(query, ('search_actuators', dict(
                    enclosure='explosionproof', supply_voltage_v=24, supply_current='AC/DC')))
                self.assertEqual(result.recommendation['total'], len(expected))
                self.assertEqual(result.context['filters']['supply_current'], 'DC')
                self.assertIn('including AC/DC', result.answer)
                self.assertIn('Explosionproof', result.answer)
                self.assertIn('24 V', result.answer)
                self.assertIn('with published electrical data', result.answer)
                if 'all' in query:
                    self.assertEqual({r['part_number'] for r in result.recommendation['items']}, expected)

    def test_dc_only_and_dual_only_keep_distinct_sql_counts(self):
        for filters, current in ((dict(supply_current='DC', dc_only=True), 'DC'),
                                 (dict(supply_current='AC/DC'), 'AC/DC')):
            expected = {r['base_part_number'] for r in self.rows if r['supply_current'] == current}
            result = search_actuators(self.connection, SearchFilters(**filters), allow_ambiguous=True)
            self.assertEqual(result['total'], len(expected))
            self.assertEqual({r['base_part_number'] for r in result['products']}, expected)

    def test_l7_09_exact_lookup_and_paraphrases_use_product_data(self):
        code = '761Y30-11380000/A'
        row = next(r for r in self.rows if r['base_part_number'] == code)
        for query in (
            f'Show the on/off torque and enclosure for {code}.',
            f'For {code}, give the on/off torque and enclosure.',
            f'Give the enclosure and on/off torque for {code}.',
        ):
            with self.subTest(query=query):
                self.fresh()
                result = self.turn(query, ('get_actuator', dict(part_numbers=[code])))
                self.assertIn(code, result.answer)
                self.assertIn(row['on_off_torque_nm'] + ' Nm', result.answer)
                self.assertIn(row['enclosure'].capitalize(), result.answer)
                self.assertNotIn('Published enclosures', result.answer)

    def test_weatherproof_count_paraphrases_include_source_na(self):
        rows = [r for r in self.rows if r['enclosure'] == 'weatherproof']
        published = len({r['base_part_number'] for r in rows if r['data_status'] == 'reported'})
        missing = len({r['base_part_number'] for r in rows if r['data_status'] == 'source_NA'})
        for query in ('How many weatherproof models are there?', 'How many weatherproof actuators are listed?',
                      'Count weatherproof models.',
                      'What enclosures are available?', 'List the published enclosures.'):
            with self.subTest(query=query):
                answer = self.keyless(query).answer
                self.assertIn('Weatherproof', answer)
                self.assertRegex(answer, rf'\b{published} models\b')
                self.assertRegex(answer, rf'\b{missing} more')
                self.assertIn('N/A', answer)
                self.assertIn('excluded', answer)

    def test_count_retains_numeric_and_categorical_scope(self):
        expected = {r['base_part_number'] for r in self.rows if r['enclosure'] == 'weatherproof'
                    and r['supply_voltage_v'] == '110' and r['data_status'] == 'reported'
                    and r['on_off_torque_nm'] and float(r['on_off_torque_nm']) >= 100}
        for query in ('How many weatherproof on/off models at 110 V deliver at least 100 Nm?',
                      'Count 110 V weatherproof on/off actuators with at least 100 Nm.'):
            answer = self.keyless(query).answer
            self.assertIn(f'{len(expected)} models', answer)
            for scope in ('Weatherproof', 'On/Off', '110 V', '100 Nm', 'published'):
                self.assertIn(scope, answer)

    def test_excluded_na_scope_does_not_claim_unknown_performance(self):
        filters = dict(enclosure='weatherproof', min_torque_nm=100, service='on_off')
        missing = source_na_count(self.connection, SearchFilters(**filters))
        expected = {r['base_part_number'] for r in self.rows if r['enclosure'] == 'weatherproof'
                    and r['data_status'] == 'source_NA' and r['service_layout'] in ('mixed', 'on_off', 'shared')}
        self.assertEqual(missing['count'], len(expected))
        note = catalogue_answers.unavailable_note(self.connection, filters)
        self.assertIn('performance eligibility is unverified', note)
        self.assertNotIn('100', note)
        self.assertIn('Weatherproof', note)
        self.assertEqual(source_na_count(self.connection, SearchFilters(enclosure='explosionproof'))['count'], 0)

    def test_counts_follow_sql_changes_not_fixed_catalogue_figures(self):
        # Transaction is rolled back by Base; the real catalogue is preserved.
        before = source_na_count(self.connection, SearchFilters(enclosure='weatherproof'))['count']
        code = next(r['base_part_number'] for r in self.rows if r['enclosure'] == 'weatherproof'
                    and r['data_status'] == 'source_NA')
        self.connection.execute("UPDATE series76.entries SET enclosure='explosionproof' WHERE base_part_number=%s", (code,))
        after = source_na_count(self.connection, SearchFilters(enclosure='weatherproof'))['count']
        self.assertEqual(after, before - 1)
        self.assertIn(f'{after} more', self.keyless('How many weatherproof models are there?').answer)

    def test_every_aggregate_sentence_names_its_scope(self):
        answers = [self.keyless(q).answer for q in (
            'What enclosures are available?', 'What voltages are available?', 'What services are available?',
            'How many models are in the catalogue?', 'How many weatherproof models are there?',
            'How many explosionproof 3-phase models are there?')]
        for query, filters in (
            ('Show all weatherproof models.', dict(enclosure='weatherproof')),
            ('Show all actuators.', {}),
            ('Find the strongest actuator.', dict(sort_by=['highest_torque'])),
            ('Find on/off weatherproof 110 V units with at least 800 Nm.',
             dict(service='on_off', enclosure='weatherproof', supply_voltage_v=110, min_torque_nm=800)),
        ):
            self.fresh()
            answers.append(self.turn(query, ('search_actuators', filters)).answer)
        checked = 0
        for answer in answers:
            for sentence in re.split(r'(?<=[.!?])\s+', answer):
                if re.search(r'\b\d+\s+(?:actuators?|models|more|published supply voltages)\b', sentence):
                    checked += 1
                    with self.subTest(sentence=sentence):
                        self.assertRegex(sentence, r'whole catalogue|Weatherproof|Explosionproof|On/Off|Modulating')
                        self.assertRegex(sentence, r'published|N/A')
        self.assertGreaterEqual(checked, len(answers))
