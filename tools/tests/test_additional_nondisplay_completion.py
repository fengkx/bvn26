"""Protect the independently selected s228 suffix and its admission boundary."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s280'
SPEC = importlib.util.spec_from_file_location('s280_diagnose', HERE / 'diagnose.py')
DIAGNOSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSIS)


class AdditionalNonDisplayCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = DIAGNOSIS.diagnose()
        cls.classifier = DIAGNOSIS.load_classifier()
        source = HERE.parent / 's228'
        cls.text = gzip.decompress((source / 'native-capture.log.gz').read_bytes()).decode()
        cls.run_id = json.loads((source / 'native-build.json').read_text())['run_id']

    def test_exact_retained_diagnosis(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for field in ('completion_fix_proved', 'terminal_callback_completeness_proved',
                      'production_admitted', 'native_parity_proven', 'trace_trimmed'):
            self.assertFalse(self.report[field])
        self.assertEqual(self.report['admitted_samples'], 0)
        self.assertEqual(self.report['native_gate']['exit_code'], 1)

    def test_entire_suffix_includes_two_later_roots(self):
        report = self.report
        self.assertEqual(report['event_count'], 5630)
        self.assertEqual([r['sequence'] for r in report['done_events']], [5540, 5585, 5630])
        self.assertEqual(report['terminal_kind_counts'], {'key_read': 34})
        self.assertEqual(len(report['later_root_events']), 56)
        self.assertEqual(report['all_action_sample_count'], 63)
        periods = report['suffix_periods']
        self.assertEqual([(p['tick'], p['display'], len(p['events'])) for p in periods],
                         [(60, 497, 34), (61, 498, 45), (62, 499, 11)])
        self.assertEqual([r['sequence'] for p in periods for r in p['events']], list(range(5541, 5631)))
        self.assertEqual(report['terminal_action_samples'][0]['sequence'], 5539)

    def test_normal_quit_is_not_terminal_completeness(self):
        controls = self.report['normal_quit_controls']
        normal = controls['normal']['post_done_periods']
        held = controls['held']['post_done_periods']
        self.assertEqual(sum(len(p['events']) for p in normal), 5)
        self.assertEqual(sum(len(p['events']) for p in held), 52)
        self.assertEqual(held[0]['kind_counts']['key_read'], 34)
        self.assertEqual(held[-1]['events'][-1]['kind'], 'capture_window_closed')
        self.assertEqual(controls['normal']['all_action_sample_count'], 61)
        self.assertEqual(controls['held']['all_action_sample_count'], 61)

    def test_missing_terminal_callback_rejected(self):
        lines = self.text.splitlines()
        del lines[5540]
        with self.assertRaisesRegex(ValueError, 'broken event sequence'):
            self.classifier.analyze('\n'.join(lines), self.run_id)

    def test_missing_second_later_root_rejected(self):
        lines = self.text.splitlines()
        del lines[5619]
        with self.assertRaisesRegex(ValueError, 'broken event sequence'):
            self.classifier.analyze('\n'.join(lines), self.run_id)

    def test_later_root_cannot_be_relabelled_terminal(self):
        lines = self.text.splitlines()
        parts = lines[-1].split('|')
        parts[4:6] = ['497', '60']
        lines[-1] = '|'.join(parts)
        with self.assertRaisesRegex(ValueError, 'terminal period reappears'):
            self.classifier.analyze('\n'.join(lines), self.run_id)

    def test_changed_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'input').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'changed retained input'):
                DIAGNOSIS.verify_pins(root, {'input': DIAGNOSIS.digest(b'original')})


if __name__ == '__main__':
    unittest.main()
