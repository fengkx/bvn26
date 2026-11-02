"""Keep native resolver and generation prerequisites fail-closed."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s298', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AllocationPrerequisiteTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE / 'facility.json').read_text())
        self.binary_sha = self.record['binary_sha256']

    def check(self, record=None, reader=None):
        return audit.audit_facility(record or self.record, self.binary_sha,
                                    reader or (lambda path: (HERE / path).read_text()))

    def test_locked_window_and_property_delete_remain_unproved(self):
        report = audit.diagnose()
        self.assertEqual(report['retained_capture']['events'], 8290)
        self.assertEqual([row['sequence'] for row in report['reference_window']['events']],
                         list(range(36, 49)))
        self.assertEqual(report['source_bindings']['control_property_delete']['statement'],
                         'delete replacement.identity;')
        self.assertTrue(all(value is None for value in report['native_observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'slot_reference_proved',
                    'allocation_identity_proved', 'actual_native_controls_executed',
                    'absence_of_possible_resolver_proved'):
            self.assertIs(report[key], False)
        for control in report['control_obligations'].values():
            self.assertIs(control['qualified'], False)
            self.assertIsNone(control['observed_native_generations'])
        self.assertEqual(report['control_obligations']['retained_content_clear']
                         ['historical_signal']['status'], 'missing_native_control')

    def test_exclusions_are_explicit(self):
        self.assertTrue(set(('pointer-only identity', '0->1 alias', 'token-loss identity',
                             'unloaded exemption', 'import inventory as runtime proof',
                             'property deletion as content clearing', 'ranks 1-7 and 9'))
                        <= set(audit.diagnose()['exclusions_enforced']))

    def test_new_execution_requires_independent_analysis(self):
        for key in ('player_launches', 'process_attaches', 'new_captures', 'live_lifetime_events'):
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
        flags = {'--require-' + name: code for name, code in audit.REQUIREMENTS.items()}
        with tempfile.TemporaryDirectory() as directory:
            for flag, code in flags.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'report.json'), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)


if __name__ == '__main__':
    unittest.main()
