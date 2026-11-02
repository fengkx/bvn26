"""Protect the distinction between import byte pins and native object identity."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s279'


class NativeResolverGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('s279_diagnose', HERE / 'diagnose.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.report = cls.module.diagnose()

    def test_recomputed_evidence_and_historical_boundaries(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        sites = self.report['allocation_observability']['target_observer_sites']
        self.assertEqual([(r['event_sequence'], r['root'], r['frame'], r['total_frames']) for r in sites],
                         [(36, 8, '1', '2'), (44, 9, '0', '0')])
        self.assertEqual(self.report['retained_capture']['events'], 8290)

    def test_import_bytes_do_not_resolve_objects_or_generations(self):
        facility = self.report['facility']
        self.assertEqual(facility['allocator_import_stubs_byte_pinned'], 4)
        for key in ('slot_resolver', 'saved_reference_resolver', 'native_object_layout', 'allocation_free_ledger'):
            self.assertIsNone(facility[key])
        self.assertFalse(facility['retained_content_clear_qualified'])
        self.assertFalse(facility['same_depth_replacement_qualified'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertFalse(self.report['mapping_fix_proved'])

    def test_identical_as2_controls_remain_ambiguous(self):
        observed = self.report['allocation_observability']
        self.assertTrue(observed['indistinguishable_as2_signals'])
        for control in observed['controls'].values():
            self.assertIsNone(control['native_allocation_generation_before'])
            self.assertIsNone(control['native_allocation_generation_after'])

    def test_tampered_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'input').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Changed evidence'):
                self.module.verify_pins(root, {'input': '0' * 64})

    def test_pending_breakpoint_is_not_a_resolver(self):
        transcript = (HERE / 'facility/resolver-breakpoints.txt').read_text()
        self.assertIn('locations = 0 (pending)', transcript)
        self.assertFalse(self.report['facility']['absence_of_possible_resolver_proved'])

    def test_required_gate_recomputes_and_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(output),
                                     '--require-allocation-identity'], cwd=ROOT,
                                    env=os.environ | {'PYTHONPATH': str(ROOT)},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('ALLOCATION_IDENTITY_UNPROVED', result.stdout)
            self.assertEqual(json.loads(output.read_text()), self.report)


if __name__ == '__main__':
    unittest.main()
