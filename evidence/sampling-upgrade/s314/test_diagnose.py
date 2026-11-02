"""Protect archived observation boundaries, not hypothesized runtime behavior."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s314', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.callback = json.loads((HERE.parent / 's304/diagnosis.json').read_text())['source_callback']['source']
        with tarfile.open(HERE.parent / 's293/held/native-build.tar.gz') as archive:
            cls.logger = archive.extractfile(audit.LOGGER).read().decode()

    def test_locked_result_and_missing_witnesses(self):
        self.assertTrue(self.report['locked_s304_reproduced'])
        self.assertTrue(self.report['independent_pair_proved_and_closed'])
        for requirement in self.report['qualification_requirements'].values():
            self.assertIsNone(requirement['qualified_witness'])
        for key in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                    'callback_completion_proved', 'terminal_completeness_proved',
                    'terminal_inventory_executed', 'full_as_proven', 'other_ranks_executed'):
            self.assertFalse(self.report[key])

    def test_channel_is_not_independent(self):
        channel = self.report['channel_audit']
        self.assertEqual(len(channel['serialized_fields']), 8)
        self.assertFalse(channel['aiEvent_independent_of_callback_mutation'])
        self.assertFalse(channel['host_copy_independent_of_event_producer'])
        self.assertFalse(channel['source_identity_is_loaded_body_identity'])
        self.assertEqual([r['line'] for r in channel['guard_after_marker']], [31, 32, 33, 34])

    def test_logger_serialization_mutations_rejected(self):
        for old, new in [('(++aiSeq)', 'aiSeq'), ('getTimer()', '0'),
                         ('trace(', 'otherTrace('), ('function(kind, value)', 'function(kind)')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                audit.audit_channel(self.logger.replace(old, new), self.callback)

    def test_callback_observer_order_mutations_rejected(self):
        for old, new in [('_root.aiEvent = function() {};', ''),
                         ('return;', ''), ('fscommand("quit");', 'stop();')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                audit.audit_channel(self.logger, self.callback.replace(old, new))

    def test_same_clock_is_not_activation_identity(self):
        held = self.report['runs']['held']
        self.assertEqual((held['done']['display'], held['done']['tick']),
                         (held['suffix'][-1]['display'], held['suffix'][-1]['tick']))
        self.assertIsNone(held['completion_witness'])
        self.assertIsNone(self.report['fixed_read_threshold'])

    def test_full_suffix_retained(self):
        prior = json.loads((HERE.parent / 's304/diagnosis.json').read_text())
        self.assertEqual(self.report['runs'], prior['runs'])

    def test_pinned_prior_mutation_rejected(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b'changed' if path == HERE.parent / 's304/README.md' else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'locked input changed'):
            audit.diagnose()

    def test_saved_result_reproduces(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))

    def test_cli_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in (None, *audit.GATES):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output',
                           str(Path(directory) / 'report.json')]
                if name:
                    command.append('--require-' + name)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1 if name else 0, result.stderr)
                if name:
                    self.assertIn(audit.GATES[name], result.stderr)


if __name__ == '__main__':
    unittest.main()
