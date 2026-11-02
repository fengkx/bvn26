"""Source-bound boundary witnesses and fail-closed proof requirements."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s313', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ConsumerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE.parent / 's306/native-bytes.json').read_text())
        self.transcript = (HERE.parent / 's306/read-wrapper.txt').read_text()
        self.stub = json.loads((HERE.parent / 's297/diagnosis.json').read_text())['static_read_stubs'][0]

    def check(self):
        return audit.audit_boundary(self.record, self.transcript, self.stub)

    def test_complete_call_inventory_has_unresolved_indirect_targets(self):
        result = self.check()
        self.assertEqual(len(result['calls']), 16)
        self.assertEqual(result['indirect_call_sites'], ['0x1004b3480', '0x1004b34d0', '0x1004b3573'])
        self.assertEqual(result['calls'][-1]['static_target'], '0x100498d20')
        self.assertEqual(result['calls'][-1]['return_site'], '0x1004b35d4')
        self.assertTrue(all(c['executed_target'] is None for c in result['calls']))

    def test_api_return_is_not_wrapper_return_or_consumer(self):
        result = self.check()
        self.assertEqual(result['candidate_api_return'], '0x1004b3552')
        self.assertEqual(result['returns'], ['0x1004b35e5'])
        for key in ('caller_continuation', 'actual_p1_consumer', 'immutable_request_generation'):
            self.assertIsNone(result[key])

    def test_cleanup_and_return_copy_witnesses(self):
        facts = {w['address']: w['hex'] for w in self.check()['witnesses']}
        self.assertEqual(facts['0x1004b35c0'], '48c7431800000000')
        self.assertEqual(facts['0x1004b35d4'], '4489e8')

    def test_changed_boundary_operand_rejected_even_with_matching_transcript_hash(self):
        for address, old, new in [(0x1004b35c0, '48 c7 43 18 00 00 00 00', '48 c7 43 20 00 00 00 00'),
                                  (0x1004b35d4, '44 89 e8', '44 89 f0')]:
            with self.subTest(address=address):
                self.setUp()
                raw = bytearray.fromhex(self.record['wrapper']['hex'])
                offset = address - self.record['wrapper']['address']
                raw[offset:offset + len(bytes.fromhex(new))] = bytes.fromhex(new)
                self.record['wrapper']['hex'] = raw.hex()
                self.record['wrapper']['sha256'] = audit.sha(raw)
                self.transcript = self.transcript.replace(old, new)
                with self.assertRaisesRegex(ValueError, 'boundary operand'):
                    self.check()

    def test_missing_instruction_rejected(self):
        self.transcript = '\n'.join(line for line in self.transcript.splitlines() if '[0x1004b35cf]' not in line)
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.check()

    def test_static_kind_cannot_be_promoted(self):
        self.record['kind'] = 'executed_p1'
        with self.assertRaisesRegex(ValueError, 'static evidence'):
            self.check()

    def test_locked_replay_and_all_proofs_stay_unproved(self):
        report = audit.diagnose()
        self.assertEqual(report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(report['historical_normal']['events'], 5503)
        self.assertTrue(report['locked_s306_reproduced'])
        self.assertTrue(all(v is None for v in report['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'consumer_request_proved',
                    'loader_attestation_proved', 'normal_association_qualified',
                    'pre_advance_target_proved', 'wrong_resource_control_executed',
                    'wrong_resource_control_qualified'):
            self.assertIs(report[key], False)
        self.assertEqual(report['M0-02'], 'pending')

    def test_changed_pin_rejected(self):
        with patch.object(audit, 'sha', return_value='different'):
            with self.assertRaisesRegex(ValueError, 'locked input changed'):
                audit.diagnose()

    def test_all_gates_fail_individually_and_together(self):
        with tempfile.TemporaryDirectory() as directory:
            for flags in [[flag] for flag in audit.GATES] + [list(audit.GATES)]:
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                                         '--output', str(Path(directory) / 'report.json'),
                                         *['--require-' + f for f in flags]],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                for flag in flags:
                    self.assertIn(audit.GATES[flag], result.stderr)


if __name__ == '__main__':
    unittest.main()
