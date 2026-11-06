"""Regression tests for real public-text coverage and exit semantics."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import check_public_text as audit


class PublicTextAuditTests(unittest.TestCase):
    def test_each_leak_category(self):
        for leak in ('get_actuator', 'filters.min_torque_nm', '{"x": 1}',
                     "{'x': None}", 'SELECT * FROM entries',
                     'Traceback (most recent call last):', 'ValidationError',
                     'on_off', 'weatherproof', 'view.limit', 'DatabaseUnavailable', '[1, 2]', "['internal', 'data']"):
            with self.subTest(leak=leak):
                self.assertTrue(audit.response_text_issues({'answer': leak}))

    def test_every_surface(self):
        payload = {
            'answer': 'get_actuator', 'lead': 'get_actuator',
            'suggested_replies': ['get_actuator'],
            'suggestions': [{'label': 'get_actuator'}, 'get_actuator'],
            'active_filters': [{'label': 'get_actuator'}],
            'interaction': {'questions': [{'prompt': 'get_actuator', 'options': [
                {'label': 'get_actuator', 'description': 'get_actuator'}]}]},
            'clarification': {'message': 'get_actuator'},
            'comparison': {'summary': 'get_actuator', 'assumptions': 'get_actuator',
                           'rows': [{'label': 'get_actuator', 'values': ['get_actuator']}],
                           'hidden_rows': [{'label': 'get_actuator'}]},
            'product_cards': [{'fields': [{'label': 'get_actuator'}]}],
            'products': [{'label': 'get_actuator'}],
            'recommendation': {'ranked_by': 'get_actuator', 'items': [{'reason': 'get_actuator'}]},
        }
        texts = list(audit.visible_texts(payload))
        self.assertEqual(len(texts), 19)
        for path, text in texts:
            with self.subTest(path=path):
                self.assertTrue(audit.text_issues(text))

    def test_machine_fields_and_valid_copy(self):
        self.assertEqual(audit.response_text_issues({
            'answer': 'On/Off torque: 80 Nm. Weatherproof. Modulating torque: 65 Nm.',
            'assumptions': [{'field': 'enclosure', 'value': 'weatherproof'}],
            'debug': {'message': 'ValidationError'},
            'products': [{'enclosure': 'weatherproof', 'source_status': 'source_NA',
                          'notes': [{'text': 'Duty cycle for on/off and modulating service'}]}],
            'comparison': {'rows': [{'field': 'on_off_torque_nm', 'label': 'On/Off torque'}]},
            'interaction': {'questions': [{'id': 'filters.min_torque_nm',
                'prompt': 'Which torque?', 'options': [{'value': 'on_off', 'label': 'On/Off'}]}]},
        }), [])

    def test_stored_response_is_not_duplicated(self):
        data = {'results': [{'id': 'L1-01', 'turns': [{'answer': 'copy',
            'response': {'answer': 'get_actuator'}}]}]}
        rows = list(audit.stored_responses(data))
        self.assertEqual(len(rows), 1)
        self.assertIn('L1-01', rows[0][0])

    def test_cli_exit_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results.json'
            report = Path(directory) / 'report.json'
            for answer, expected in [('Published torque: 80 Nm.', 0), ('get_actuator', 1)]:
                path.write_text(json.dumps({'response': {'answer': answer}}))
                with patch.object(audit, 'audit_selfchecks'), patch.object(audit, 'ROOT', Path(directory)), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(audit.main(['--outputs', str(path), '--report', str(report)]), expected)
                self.assertEqual(json.loads(report.read_text())['sources'][str(path)]['responses'], 1)

    def test_incomplete_sources_fail(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audit, 'ROOT', Path(directory)), patch.object(audit, 'audit_selfchecks'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(['--outputs', directory + '/missing*.json']), 1)

    def test_markdown_scans_prose_not_evaluation_serialization(self):
        pack = "\n".join([
            "## L1-01 (persona: precise)", "### Variant A", "  > USER: get_actuator",
            "    ANSWER: Published torque.",
            "    PRODUCT CARD: weatherproof | on_off_torque_nm=80",
            "    COMPARISON: models=['a', 'b'] summary=Valid comparison.",
            "  > USER: next", "    QUESTION CARD: filters.min_torque_nm",
        ])
        rows = list(audit.markdown_responses(pack))
        self.assertEqual(len(rows), 2)
        self.assertEqual(audit.response_text_issues(rows[0][1]), [])
        self.assertTrue(audit.response_text_issues(rows[1][1]))
        self.assertEqual(rows[1][0], 'L1-01/A/turn-2')

    def test_invalid_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results.json'
            path.write_text('{broken')
            result = audit.Audit()
            result.stored(path)
            self.assertEqual(len(result.errors), 1)
            self.assertEqual(result.sources[str(path)]['responses'], 0)

    def test_live_requires_keyless_confirmation(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            audit.main(['--live', 'http://127.0.0.1:8000'])


if __name__ == '__main__':
    unittest.main()
