"""Static read facilities must not become loader-consumption evidence."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s287', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LoaderBoundaryTests(unittest.TestCase):
    def test_historical_stream_and_static_stubs_do_not_admit_live_proof(self):
        report = audit.diagnose()
        self.assertEqual(report['historical_normal']['events'], 5503)
        self.assertEqual(len(report['static_read_stubs']), 4)
        self.assertTrue(report['source_loader_order']['completion_calls_next_step_inline'])
        self.assertIsNone(report['source_loader_order']['actual_callback_order'])
        self.assertTrue(all(value is None for value in report['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'loader_attestation_proved',
                    'wrong_resource_control_qualified'):
            self.assertIs(report[key], False)

    def test_wrong_pointer_slot_is_rejected(self):
        raw = (HERE / 'read-addresses.txt').read_text().replace('ff 25 f8 ce 4f 00', 'ff 25 f9 ce 4f 00')
        with self.assertRaisesRegex(ValueError, 'symbol mismatch'):
            audit.audit_read_stubs((HERE / 'indirect-symbols.txt').read_text(), raw)

    def test_missing_read_is_rejected(self):
        raw = (HERE / 'read-addresses.txt').read_text().replace('Debugger[0x100fb6882]', 'Missing[0x100fb6882]')
        with self.assertRaisesRegex(ValueError, 'missing or duplicated'):
            audit.audit_read_stubs((HERE / 'indirect-symbols.txt').read_text(), raw)

    def test_both_requirements_remain_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag in ('--require-loader-attestation', '--require-wrong-resource-control'):
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                                         '--output', str(Path(directory) / 'report.json'), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('S287_LOADER_UNPROVED', result.stderr)


if __name__ == '__main__':
    unittest.main()
