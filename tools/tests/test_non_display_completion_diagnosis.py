"""Retain the s232 rejection and distinguish callbacks from root re-entry."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    's254_diagnosis', ROOT / 'evidence/sampling-upgrade/s254/diagnose.py')
DIAGNOSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSIS)


class NonDisplayCompletionDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / 'evidence/sampling-upgrade/s232'
        cls.text = gzip.decompress((base / 'native-capture.log.gz').read_bytes()).decode()
        cls.run_id = json.loads((base / 'native-build.json').read_text())['run_id']

    def test_retained_rejection_and_exact_report(self):
        actual = DIAGNOSIS.diagnose()
        retained = json.loads((ROOT / 'evidence/sampling-upgrade/s254/diagnosis.json').read_text())
        self.assertEqual(actual, retained)
        self.assertEqual(actual['native_gate']['exit_code'], 1)
        self.assertEqual(actual['admitted_samples'], 0)
        self.assertFalse(actual['trace_trimmed'])
        self.assertFalse(actual['production_admitted'])
        self.assertFalse(actual['native_parity_proven'])

    def test_terminal_callbacks_are_not_later_root_events(self):
        report = DIAGNOSIS.analyze(self.text, self.run_id)
        self.assertEqual(report['event_count'], 5705)
        self.assertEqual(report['terminal_kind_counts'], {'key_read': 34})
        self.assertEqual(len(report['later_root_events']), 16)
        first = report['later_root_events'][0]
        self.assertEqual((first['sequence'], first['tick'], first['display'], first['kind']),
                         (5690, 61, 526, 'input_next_display'))
        self.assertEqual([r['sequence'] for r in report['done_events']], [5655, 5705])
        self.assertEqual(report['terminal_geometry_events'][-1]['sequence'], 5654)
        self.assertEqual(report['all_geometry_begin_count'], 62)
        self.assertEqual(report['all_geometry_end_count'], 62)

    def test_missing_callback_cannot_silently_shorten_sequence(self):
        lines = self.text.splitlines()
        del lines[5655]
        with self.assertRaisesRegex(ValueError, 'broken event sequence'):
            DIAGNOSIS.analyze('\n'.join(lines), self.run_id)

    def test_foreign_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'foreign'):
            DIAGNOSIS.analyze(self.text.replace(self.run_id, 'foreign', 1), self.run_id)

    def test_nonmonotonic_clock_is_rejected(self):
        lines = self.text.splitlines()
        fields = lines[-1].split('|')
        fields[3] = '0'
        lines[-1] = '|'.join(fields)
        with self.assertRaisesRegex(ValueError, 'nonmonotonic clock'):
            DIAGNOSIS.analyze('\n'.join(lines), self.run_id)

    def test_missing_done_is_not_completion(self):
        with self.assertRaisesRegex(ValueError, 'missing done'):
            DIAGNOSIS.analyze(self.text.replace('|done|', '|not_done|'), self.run_id)

    def test_later_period_cannot_be_relabelled_terminal(self):
        lines = self.text.splitlines()
        fields = lines[-1].split('|')
        fields[4:6] = ['525', '60']
        lines[-1] = '|'.join(fields)
        with self.assertRaisesRegex(ValueError, 'terminal period reappears'):
            DIAGNOSIS.analyze('\n'.join(lines), self.run_id)


if __name__ == '__main__':
    unittest.main()
