"""Keep AS2 reference observations separate from native allocation proof."""
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s289', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AllocationBoundaryTests(unittest.TestCase):
    def test_retained_window_and_controls_do_not_prove_native_identity(self):
        report = audit.diagnose()
        self.assertEqual(report['retained_capture']['events'], 8290)
        self.assertEqual([r['sequence'] for r in report['reference_window']['events']], list(range(36, 49)))
        self.assertEqual([r['payload'] for r in report['reference_window']['controls']],
                         ['retained,true,true', 'replaced,true,false', 'retained_content_deleted,true,false'])
        self.assertTrue(all(v is None for v in report['native_observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'allocation_identity_proved'):
            self.assertIs(report[key], False)
        self.assertEqual(report['source_bindings']['control_property_delete']['statement'],
                         'delete replacement.identity;')
        self.assertEqual(report['controls']['retained_content_clear']['status'], 'missing_native_control')

    def test_missing_duplicate_and_mixed_events_reject(self):
        lines = gzip.decompress((HERE.parent / 's261/native-capture.log.gz').read_bytes()).decode().splitlines()
        for changed in (lines[:41] + lines[42:], lines[:41] + [lines[40]] + lines[41:],
                        lines[:41] + [lines[41].replace('s261-yijiao-r01', 'different-run')] + lines[42:]):
            with self.assertRaises(ValueError):
                audit.reference_window('\n'.join(changed))

    def test_changed_control_is_not_reclassified_as_retention(self):
        raw = gzip.decompress((HERE.parent / 's261/native-capture.log.gz').read_bytes()).decode()
        with self.assertRaisesRegex(ValueError, 'control observations'):
            audit.reference_window(raw.replace('retained_content_deleted,true,false', 'retained_content_deleted,true,true'))

    def test_source_binding_requires_unique_statement(self):
        for source in ('other();', 'delete replacement.identity;\ndelete replacement.identity;'):
            with self.assertRaisesRegex(ValueError, 'Missing or ambiguous'):
                audit.source_binding(source, 'delete replacement.identity;')

    def test_tampered_pin_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'input').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Changed evidence'):
                audit.verify_pins(root, {'input': '0' * 64})

    def test_both_requirements_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag in ('--require-slot-reference', '--require-allocation-identity'):
                output = Path(directory) / 'report.json'
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(output), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(audit.ERROR, result.stderr)
                self.assertFalse(json.loads(output.read_text())['allocation_identity_proved'])


if __name__ == '__main__':
    unittest.main()
