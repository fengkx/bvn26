"""Reject static-to-live promotion and altered native operand evidence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s306', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LoaderWrapperTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE / 'native-bytes.json').read_text())
        self.transcript = (HERE / 'read-wrapper.txt').read_text()
        prior = json.loads((HERE.parent / 's297/diagnosis.json').read_text())
        self.stub = next(s for s in prior['static_read_stubs'] if s['symbol'] == 'CFReadStreamRead')

    def check(self):
        return audit.audit_wrapper(self.record, self.transcript, self.stub)

    def test_locked_replay_does_not_promote_static_evidence(self):
        report = audit.diagnose()
        self.assertTrue(report['locked_s297_reproduced'])
        self.assertEqual(report['historical_normal']['events'], 5503)
        self.assertEqual(report['M0-02'], 'pending')
        self.assertTrue(report['source_loader_order']['completion_calls_next_step_inline'])
        self.assertIsNone(report['source_loader_order']['actual_callback_order'])
        self.assertTrue(all(value is None for value in report['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'loader_attestation_proved',
                    'normal_association_qualified', 'pre_advance_target_proved',
                    'wrong_resource_control_executed', 'wrong_resource_control_qualified'):
            self.assertIs(report[key], False)

    def test_return_site_and_distinct_zero_negative_positive_paths(self):
        result = self.check()
        self.assertEqual(result['bytes_checked'], 432)
        self.assertEqual(result['api_return_site_candidate'], '0x1004b3552')
        self.assertEqual([b['target'] for b in result['branches']],
                         ['0x100fb5baa', '0x1004b3592', '0x1004b35e6', '0x1004b3592'])
        for key in ('live_p1_membership', 'native_consumer_type', 'immutable_request_field', 'callback_target_resolver'):
            self.assertIsNone(result[key])

    def test_static_kind_cannot_become_execution(self):
        self.record['kind'] = 'executed_p1'
        with self.assertRaisesRegex(ValueError, 'static evidence'):
            self.check()

    def test_incomplete_wrapper_rejected(self):
        self.record['wrapper']['size'] -= 1
        with self.assertRaisesRegex(ValueError, 'incomplete wrapper'):
            self.check()

    def test_wrong_file_mapping_rejected(self):
        self.record['wrapper']['file_offset'] += 1
        with self.assertRaisesRegex(ValueError, 'mapping'):
            self.check()

    def test_changed_bytes_rejected(self):
        self.record['wrapper']['hex'] = '00' + self.record['wrapper']['hex'][2:]
        with self.assertRaisesRegex(ValueError, 'changed native bytes'):
            self.check()

    def test_missing_or_repeated_disassembly_rejected(self):
        original = self.transcript
        line = next(line for line in original.splitlines(True) if '[0x1004b354d]' in line)
        for replacement in ('', line + line):
            self.transcript = original.replace(line, replacement)
            with self.assertRaisesRegex(ValueError, 'coverage mismatch'):
                self.check()

    def test_changed_stream_offset_even_with_recomputed_hash_rejected(self):
        raw = bytearray.fromhex(self.record['wrapper']['hex'])
        raw[0x1004b3541 - audit.START + 3] = 0x20
        self.record['wrapper']['hex'] = raw.hex()
        self.record['wrapper']['sha256'] = audit.sha(raw)
        line = next(line for line in self.transcript.splitlines() if '[0x1004b3541]' in line)
        self.transcript = self.transcript.replace(line, line.replace('48 8b 7b 18', '48 8b 7b 20'))
        # The byte coverage still agrees; the source-bound operand must not change.
        with self.assertRaisesRegex(ValueError, 'changed operand'):
            self.check()

    def test_changed_call_target_even_with_recomputed_hash_rejected(self):
        raw = bytearray.fromhex(self.record['wrapper']['hex'])
        raw[0x1004b354d - audit.START + 1] += 1
        self.record['wrapper']['hex'] = raw.hex()
        self.record['wrapper']['sha256'] = audit.sha(raw)
        self.transcript = self.transcript.replace('e8 58 26 b0 00', 'e8 59 26 b0 00')
        with self.assertRaisesRegex(ValueError, 'destination'):
            self.check()

    def test_extractor_rejects_different_executable(self):
        extractor = audit.load_module('s306_extract', HERE / 'extract.py')
        with self.assertRaisesRegex(ValueError, 'different player'):
            extractor.extract(b'not the player')

    def test_gates_fail_closed_individually_and_together(self):
        flags = {'--require-loader-attestation': 'S306_LOADER_ASSOCIATION_UNPROVED',
                 '--require-pre-advance-target': 'S306_PRE_ADVANCE_TARGET_UNPROVED',
                 '--require-wrong-resource-control': 'S306_WRONG_RESOURCE_BLOCKED'}
        with tempfile.TemporaryDirectory() as directory:
            for selected in [[flag] for flag in flags] + [list(flags)]:
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'report.json'), *selected],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                for flag in selected:
                    self.assertIn(flags[flag], result.stderr)


if __name__ == '__main__':
    unittest.main()
