"""Keep missing allocation observations distinct from AS2 identity shortcuts."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s267'


class AllocationIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('s267_diagnose', HERE / 'diagnose.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.prior = cls.module.read_pinned_inputs()
        cls.report = cls.module.diagnose()

    def test_recomputed_report_and_pending_flags(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for key in ('production_admitted', 'native_parity_proven', 'mapping_fix_proved',
                    'identity_discriminator_valid_for_cleared_content',
                    'allocation_generation_observations_established'):
            self.assertIs(self.report[key], False)
        self.assertEqual(self.report['product_obligations_closed'], 0)

    def test_exact_retained_sites_have_no_native_generations(self):
        sites = self.report['allocation_observability']['target_observer_sites']
        self.assertEqual([(r['event_sequence'], r['root'], r['frame'], r['total_frames'])
                          for r in sites], [(36, 8, '1', '2'), (44, 9, '0', '0')])
        for site in sites:
            for field in ('native_allocation_address', 'native_allocation_generation',
                          'saved_reference_native_referent'):
                self.assertIsNone(site[field])

    def test_property_deletion_is_not_retained_clear_calibration(self):
        result = self.report['allocation_observability']
        self.assertTrue(result['indistinguishable_as2_signals'])
        self.assertEqual(result['controls']['retained_content_clear']['status'], 'missing_native_control')
        self.assertIn('independently_verified_retained_content_clear_control', result['missing'])
        self.assertIn('same_depth_replacement_native_generation_control', result['missing'])

    def test_tokens_frames_and_paths_cannot_mint_native_generation(self):
        prior = copy.deepcopy(self.prior)
        for row in prior['observations']:
            row['objects']['depth_occupant'].update(token='new-token', display_id='123', frame='1')
        for site in self.module.allocation_requirements(prior)['target_observer_sites']:
            self.assertIsNone(site['native_allocation_generation'])

    def test_attach_feasibility_does_not_prove_target_identity(self):
        facility = self.report['facility']
        self.assertTrue(facility['historical_same_binary_attach_succeeded'])
        self.assertFalse(facility['historical_attach_is_target_identity_evidence'])
        self.assertFalse(facility['native_slot_resolver_established'])
        self.assertFalse(facility['absence_of_possible_facility_proved'])
        self.assertEqual(facility['allocation_events_captured'], 0)

    def test_required_identity_gate_fails_and_writes_missing_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'diagnosis.json'
            process = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                                      '--output', str(output), '--require-allocation-identity'],
                                     cwd=ROOT, capture_output=True, text=True,
                                     env=os.environ | {'PYTHONPATH': str(ROOT)})
            self.assertEqual(process.returncode, 1, process.stderr)
            self.assertIn('ALLOCATION_IDENTITY_UNPROVED', process.stdout)
            self.assertEqual(json.loads(output.read_text()), self.report)


if __name__ == '__main__':
    unittest.main()
