"""Protect evidence boundaries without inventing a positive raster fixture."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s290', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class RasterBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.pair = json.loads((HERE.parent / 's272/diagnosis.json').read_text())['pair_audit']
        self.prerequisites = json.loads((HERE.parent / 's281/diagnosis.json').read_text())['prerequisites']

    def test_all_boundaries_remain_unmeasured(self):
        report = audit.diagnose()
        rows = report['boundary_audit']['rows']
        self.assertEqual(len(rows), 61)
        self.assertEqual(rows[13]['glyph_mismatch_fields'], ['tens', 'ones'])
        self.assertEqual(report['boundary_audit']['other_selected_state_mismatch_ticks'], list(range(61)))
        self.assertTrue(all(r['pixel_classification'] == 'not_measured' for r in rows))
        for key in ('production_admitted', 'native_parity_proven', 'state_admission_proved', 'thin_raster_cut_proved'):
            self.assertIs(report[key], False)

    def test_missing_duplicate_reordered_rows_reject(self):
        for rows in (self.pair['rows'][:-1], [self.pair['rows'][0]] * 61, list(reversed(self.pair['rows']))):
            pair = copy.deepcopy(self.pair)
            pair['rows'] = rows
            with self.assertRaisesRegex(ValueError, 'state rows'):
                audit.audit_rows(pair, self.prerequisites)

    def test_hidden_difference_rejects(self):
        self.pair['rows'][13]['differences'].pop()
        with self.assertRaisesRegex(ValueError, 'summary'):
            audit.audit_rows(self.pair, self.prerequisites)

    def test_boundary_substitution_rejects(self):
        self.pair['rows'][13]['display'] += 1
        with self.assertRaisesRegex(ValueError, 'binding'):
            audit.audit_rows(self.pair, self.prerequisites)

    def test_image_and_admission_promotion_reject(self):
        for key, value in (('state_admitted', True), ('same_capture_godot_images_written', 61)):
            pair = copy.deepcopy(self.pair)
            pair[key] = value
            with self.assertRaisesRegex(ValueError, 'admission or image'):
                audit.audit_rows(pair, self.prerequisites)

    def test_zero_residual_and_proof_promotion_reject(self):
        for key, value in (('exact_rgba_edge_residual', 0), ('exact_rgba_interior_residual', 0),
                           ('matched_image_pairs', 61), ('same_capture_state_admitted', True),
                           ('thin_raster_cut_proved', True), ('residual_family_classified', True)):
            prerequisites = copy.deepcopy(self.prerequisites)
            prerequisites[key] = value
            with self.assertRaises(ValueError):
                audit.audit_rows(self.pair, prerequisites)

    def test_changed_pin_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'input').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Changed locked'):
                audit.verify_pins(root, {'input': '0' * 64})

    def test_both_requirements_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag in ('--require-state-admission', '--require-thin-raster'):
                output = Path(directory) / 'report.json'
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(output), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(audit.ERROR, result.stderr)
                self.assertFalse(json.loads(output.read_text())['thin_raster_cut_proved'])


if __name__ == '__main__':
    unittest.main()
