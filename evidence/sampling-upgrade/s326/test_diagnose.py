"""Guard the locked s317 handoff; these tests do not prove pixels or admission."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s326', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LockedRasterTests(unittest.TestCase):
    def setUp(self):
        self.prior = json.loads((HERE.parent / 's317/diagnosis.json').read_text())

    def test_full_handoff_retains_identity_and_unmeasured_pixels(self):
        report = audit.diagnose()
        self.assertEqual(report['scope'], 'AFTER-s317 rank #9 only')
        self.assertEqual(report['boundary_audit'], self.prior['boundary_audit'])
        self.assertEqual(report['locked_prerequisites'], self.prior['locked_prerequisites'])
        self.assertEqual(report['ordered_gates'], self.prior['ordered_gates'])
        self.assertEqual(report['new_independent_runtime_observations'], [])
        self.assertEqual(report['new_captures'], 0)
        self.assertEqual(report['m0_02_status'], 'pending')
        for key in ('production_admitted', 'native_parity_proven', 'state_admission_proved',
                    'paired_scene_proved', 'thin_raster_cut_proved', 'residual_family_classified'):
            self.assertIs(report[key], False)

    def test_each_boundary_identity_change_rejected(self):
        for tick in range(61):
            changed = copy.deepcopy(self.prior)
            changed['boundary_audit'][tick]['run_id'] = 'substituted-run'
            with self.assertRaisesRegex(ValueError, 'Locked s317'):
                audit.audit_locked(changed, self.prior)

    def test_non_boundary_change_rejected(self):
        changed = copy.deepcopy(self.prior)
        changed['blocker'] = 'no blocker'
        with self.assertRaisesRegex(ValueError, 'Locked s317'):
            audit.audit_locked(changed, self.prior)

    def test_retained_guards_reject_claims_even_with_matching_copy(self):
        for field, value in (('production_admitted', True), ('matched_image_pairs', 1),
                             ('exact_rgba_edge_residual', 0), ('classified_boundaries', 61)):
            changed = copy.deepcopy(self.prior)
            changed[field] = value
            with self.assertRaises(ValueError):
                audit.audit_locked(changed, changed)

    def test_changed_replay_rejected_by_diagnosis(self):
        module = audit.locked_module()
        changed = copy.deepcopy(self.prior)
        changed['boundary_audit'][60]['same_capture_image_pair_available'] = True
        with patch.object(module, 'diagnose', return_value=changed), patch.object(audit, 'locked_module', return_value=module):
            with self.assertRaisesRegex(ValueError, 'Locked s317'):
                audit.diagnose()

    def test_cli_base_and_all_unproved_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            for name in (None, *audit.REQUIREMENTS):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                if name:
                    command.append('--require-' + name)
                result = subprocess.run(command, cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, int(name is not None), result.stderr)
                self.assertIn(audit.REQUIREMENTS[name] if name else 'S326_DIAGNOSIS_OK', result.stdout + result.stderr)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])


if __name__ == '__main__':
    unittest.main()
