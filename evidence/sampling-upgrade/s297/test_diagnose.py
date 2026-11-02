"""Prevent static facilities and request proxies from becoming consumed-byte proof."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s297', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LoaderAssociationTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE / 'facility.json').read_text())
        self.binary_sha = self.record['binary_sha256']

    def check(self, record=None, reader=None):
        return audit.audit_facility(record or self.record, self.binary_sha,
                                    reader or (lambda path: (HERE / path).read_text()))

    def test_locked_replay_keeps_missing_observations_and_inline_boundary(self):
        report = audit.diagnose()
        self.assertEqual(report['historical_normal']['events'], 5503)
        self.assertEqual(len(report['static_read_stubs']), 4)
        self.assertTrue(report['source_loader_order']['completion_calls_next_step_inline'])
        self.assertIsNone(report['source_loader_order']['actual_callback_order'])
        self.assertTrue(all(value is None for value in report['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'loader_attestation_proved',
                    'normal_association_qualified', 'pre_advance_target_proved',
                    'wrong_resource_control_qualified', 'wrong_resource_control_executed'):
            self.assertIs(report[key], False)

    def test_new_execution_requires_independent_analysis(self):
        for key in ('player_launches', 'process_attaches', 'new_captures', 'live_read_events'):
            record = copy.deepcopy(self.record)
            record[key] = 1
            with self.assertRaisesRegex(ValueError, 'independent analysis'):
                self.check(record)

    def test_other_binary_rejected(self):
        self.record['binary_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'different player'):
            self.check()

    def test_duplicate_query_rejected(self):
        self.record['checks'][1] = self.record['checks'][0]
        with self.assertRaisesRegex(ValueError, 'missing or duplicated'):
            self.check()

    def test_success_or_changed_command_requires_analysis(self):
        for field, value in (('exit', 0), ('command', ['lldb', '-o', 'run'])):
            record = copy.deepcopy(self.record)
            record['checks'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'independent analysis'):
                self.check(record)

    def test_transcript_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, 'changed facility transcript'):
            self.check(reader=lambda path: (HERE / path).read_text() + 'match\n')

    def test_target_failure_is_not_empty_lookup(self):
        text = 'error: target creation failed\n'
        self.record['checks'][0]['sha256'] = audit.sha(text.encode())
        with self.assertRaisesRegex(ValueError, 'expected empty result'):
            self.check(reader=lambda path: text)

    def test_cost_must_be_finite_positive(self):
        for value in (-1, True, float('nan'), float('inf')):
            self.record['checks'][0]['elapsed_seconds'] = value
            with self.assertRaisesRegex(ValueError, 'invalid measured cost'):
                self.check()

    def test_all_requirement_commands_fail_closed(self):
        flags = {'--require-loader-attestation': 'S297_LOADER_ASSOCIATION_UNPROVED',
                 '--require-pre-advance-target': 'S297_PRE_ADVANCE_TARGET_UNPROVED',
                 '--require-wrong-resource-control': 'S297_WRONG_RESOURCE_BLOCKED'}
        with tempfile.TemporaryDirectory() as directory:
            for flag, code in flags.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'report.json'), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)


if __name__ == '__main__':
    unittest.main()
