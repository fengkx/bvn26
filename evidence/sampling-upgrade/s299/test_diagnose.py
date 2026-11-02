"""Reject unsupported raster claims; no synthetic positive pixel proof."""
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
spec = importlib.util.spec_from_file_location('s299', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class RasterAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.locked = json.loads((HERE.parent / 's290/diagnosis.json').read_text())

    def test_replay_retains_all_boundaries_and_unknown_pixels(self):
        report = audit.diagnose()
        self.assertEqual(report['scope'], 'AFTER-s290 rank #9 only')
        self.assertEqual(len(report['boundary_audit']), 61)
        for row in report['boundary_audit']:
            for field in ('source_bound_edge_membership', 'source_bound_interior_membership',
                          'exact_rgba_edge_residual', 'exact_rgba_interior_residual', 'differing_channels'):
                self.assertIsNone(row[field])
            self.assertFalse(row['paired_capture_attempted'])
        for field in ('production_admitted', 'native_parity_proven', 'state_admission_proved',
                      'paired_scene_proved', 'thin_raster_cut_proved', 'residual_family_classified'):
            self.assertIs(report[field], False)

    def test_changed_boundary_identity_rejects_at_every_tick(self):
        for index in range(61):
            for field, value in (('display', -1), ('firing', -1), ('run_id', 'other'), ('raw_sha256', '0' * 64)):
                changed = copy.deepcopy(self.locked)
                changed['boundary_audit']['rows'][index][field] = value
                with self.assertRaisesRegex(ValueError, 'Locked s290'):
                    audit.audit_locked(changed, self.locked)

    def test_missing_duplicate_reordered_rows_reject(self):
        rows = self.locked['boundary_audit']['rows']
        for replacement in (rows[:-1], [rows[0]] * 61, list(reversed(rows))):
            changed = copy.deepcopy(self.locked)
            changed['boundary_audit']['rows'] = replacement
            with self.assertRaises(ValueError):
                audit.audit_locked(changed, self.locked)

    def test_hidden_scene_or_glyph_difference_rejects(self):
        for field in ('glyph_mismatch_fields', 'other_selected_state_mismatch_fields'):
            changed = copy.deepcopy(self.locked)
            changed['boundary_audit']['rows'][0][field] = []
            with self.assertRaises(ValueError):
                audit.audit_locked(changed, self.locked)

    def test_proof_promotion_rejects_even_if_retained_copy_changed(self):
        for field in ('production_admitted', 'native_parity_proven', 'state_admission_proved', 'thin_raster_cut_proved'):
            changed = copy.deepcopy(self.locked)
            changed[field] = True
            with self.assertRaisesRegex(ValueError, 'proof promotion'):
                audit.audit_locked(changed, changed)

    def test_images_and_zero_residuals_cannot_supply_missing_admission(self):
        for field, value in (('same_capture_state_admitted', True), ('matched_image_pairs', 1),
                             ('exact_rgba_edge_residual', 0), ('exact_rgba_interior_residual', 0)):
            changed = copy.deepcopy(self.locked)
            changed['locked_prerequisites'][field] = value
            with self.assertRaises(ValueError):
                audit.audit_locked(changed, changed)

    def test_changed_pin_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'input').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Changed locked evidence'):
                audit.verify_pins(path, {'input': '0' * 64})

    def test_diagnose_rejects_changed_replay(self):
        changed = copy.deepcopy(self.locked)
        changed['boundary_audit']['rows'][60]['display'] = -1
        with patch.object(audit, 'replay_locked', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'Locked s290'):
                audit.diagnose()

    def test_cli_audit_and_each_proof_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            for name in (None, *audit.REQUIREMENTS):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                if name:
                    command.append('--require-' + name)
                result = subprocess.run(command, cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, int(name is not None), result.stderr)
                self.assertIn(audit.REQUIREMENTS[name] if name else 'S299_DIAGNOSIS_OK', result.stderr + result.stdout)
                self.assertFalse(json.loads(output.read_text())['thin_raster_cut_proved'])


if __name__ == '__main__':
    unittest.main()
