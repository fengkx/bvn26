"""Protect source ownership boundaries and reject completion-by-silence."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s304', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.source = cls.report['source_callback']['source']

    def test_locked_result_and_admission(self):
        self.assertTrue(self.report['locked_s293_diagnosis_equal'])
        self.assertTrue(self.report['independent_pair_proved_and_closed'])
        for key in ('production_admitted', 'native_parity_proven', 'full_as_proven', 'other_ranks_executed'):
            self.assertFalse(self.report[key])
        self.assertIsNone(self.report['fixed_suffix_threshold'])

    def test_closure_marker_precedes_exit(self):
        bound = self.report['source_callback']
        p = bound['lines']
        self.assertLess(p['closure_marker'], p['replace_callback'])
        self.assertLess(p['disable_logger'], bound['quit_lines'][0])
        self.assertLess(bound['quit_lines'][0], p['explicit_return'])
        self.assertLess(p['done_marker'], p['arm_guard'])
        self.assertLess(p['arm_guard'], bound['fallthrough_end_line'])
        self.assertIsNone(bound['observed_return'])
        self.assertIsNone(bound['live_activation_identity'])

    def test_source_mutations_rejected(self):
        for before, after in [('return;', ''), ('aiDisplay++;', 'aiDisplay += 2;'),
                              ('_root.aiEvent = function() {};', ''),
                              ('fscommand("quit");', 'stop();')]:
            with self.subTest(before=before), self.assertRaises(ValueError):
                audit.source_bounds(self.source.replace(before, after))

    def test_observed_suffix_is_retained_not_a_threshold(self):
        runs = self.report['runs']
        self.assertEqual(runs['normal']['suffix'], [])
        self.assertEqual(runs['held']['suffix_kind_counts'], {'capture_window_closed': 1, 'key_read': 34})
        self.assertEqual(runs['held']['suffix'][-1]['sequence'], 5549)
        self.assertEqual(runs['held']['done']['sequence'], 5514)
        self.assertTrue(all(r['completion_witness'] is None for r in runs.values()))

    def test_arbitrary_read_counts_never_create_witness(self):
        for count in (0, 1, 33, 34, 35, 100):
            lines = ['AIREF|synthetic|1|0|1|60|done|']
            lines += [f'AIREF|synthetic|{i+2}|0|1|60|key_read|owner,1,false' for i in range(count)]
            lines += [f'AIREF|synthetic|{count+2}|0|1|60|capture_window_closed|before-next-root-increment']
            self.assertIsNone(audit.suffix('\n'.join(lines).encode())['completion_witness'])

    def test_duplicate_done_and_missing_event_rejected(self):
        for trace in ('AIREF|test|1|0|1|60|done|\nAIREF|test|2|0|1|60|done|',
                      'AIREF|test|2|0|1|60|done|'):
            with self.assertRaises(ValueError):
                audit.suffix(trace.encode())

    def test_pinned_archive_tamper_rejected(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b'changed' if path == audit.LOCKED / 'held/native-build.tar.gz' else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'LOCKED_INPUT_CHANGED'):
            audit.diagnose()

    def test_saved_artifact_reproducible(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))

    def test_gates_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, code in audit.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                    str(Path(directory) / 'report.json'), '--require-' + name], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)


if __name__ == '__main__':
    unittest.main()
