"""Protect byte-bound candidate facts and reject unsupported live promotion."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s321', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CallerCandidateTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE / 'native-audit.json').read_text())
        self.text = (HERE / 'caller-window.txt').read_text()

    def test_candidate_reads_buffer_not_return_register(self):
        result = audit.audit_window(self.record, self.text)
        self.assertEqual(result['wrapper_target'], '0x1004b3440')
        self.assertEqual(result['argument_length'], 1)
        self.assertEqual(result['instructions'][6]['hex'], '0fb64dd7')
        self.assertIn('initialized zero', result['limitation'])

    def test_changed_buffer_operand_rejected(self):
        self.record['window']['hex'] = self.record['window']['hex'].replace('0fb64dd7', '0fb64dd8')
        with self.assertRaisesRegex(ValueError, 'caller window'):
            audit.audit_window(self.record, self.text)

    def test_missing_post_call_read_rejected(self):
        text = '\n'.join(line for line in self.text.splitlines() if not line.startswith('100108f6d:'))
        with self.assertRaisesRegex(ValueError, 'coverage'):
            audit.audit_window(self.record, text)

    def test_static_record_promotion_rejected(self):
        self.record['kind'] = 'executed_p1'
        with self.assertRaisesRegex(ValueError, 'cannot be promoted'):
            audit.audit_window(self.record, self.text)

    def test_pin_change_rejected(self):
        with patch.object(audit, 'sha', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'locked input changed'):
                audit.diagnose()

    def test_replay_keeps_all_live_observations_unknown(self):
        result = audit.diagnose()
        self.assertEqual(result, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(result['historical_normal']['events'], 5503)
        self.assertTrue(all(v is None for v in result['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'consumer_request_proved',
                    'loader_attestation_proved', 'normal_association_qualified',
                    'pre_advance_target_proved', 'wrong_resource_control_executed'):
            self.assertIs(result[key], False)

    def test_all_proof_requirements_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            for flags in [[flag] for flag in audit.GATES] + [list(audit.GATES)]:
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'out.json'),
                                         *['--require-' + flag for flag in flags]],
                                        capture_output=True, text=True, cwd=audit.ROOT)
                self.assertEqual(result.returncode, 1, result.stderr)
                for flag in flags:
                    self.assertIn(audit.GATES[flag], result.stderr)

    def test_pattern_search_is_not_instruction_decoding(self):
        spec = importlib.util.spec_from_file_location('extract', HERE / 'extract_native.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # An embedded immediate-like pattern deliberately remains a candidate.
        raw = b'\x90\xe8\x04\x00\x00\x00\x90'
        self.assertEqual(module.candidates(raw, 0, len(raw), 0x1000, 0x100a), [1])
        self.assertEqual(module.candidates(raw, 0, 5, 0x1000, 0x100a), [])


if __name__ == '__main__':
    unittest.main()
