"""Locked-state and adversarial checks for the s272 evidence-only diagnosis."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('s272', ROOT / 'evidence/sampling-upgrade/s272/diagnose.py')
s272 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s272)


class StrictRasterAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((s272.LOCKED / 'diagnosis.json').read_text())
        cls.scene = json.loads((s272.LOCKED / 'paired-scene.json').read_text())

    def test_locked_capture_replay_and_rejection(self):
        result = s272.diagnose()
        self.assertEqual(result['events_revalidated'], 32227)
        self.assertEqual(result['native_bitmap_frames'], 61)
        audit = result['pair_audit']
        self.assertEqual(audit['differing_snapshot_counts']['camera_x'], 12)
        self.assertEqual(audit['differing_snapshot_counts']['camera_scale'], 61)
        self.assertFalse(audit['state_admitted'])
        self.assertFalse(audit['residual_family_classified'])
        self.assertFalse(audit['thin_raster_cut_proved'])
        self.assertEqual(audit['same_capture_godot_images_written'], 0)

    def test_tick13_has_state_confounders_not_a_raster_diagnosis(self):
        row = s272.audit_pair(self.contract, self.scene)['rows'][13]
        self.assertEqual((row['display'], row['firing']), (463, 25))
        differences = {d['field']: d for d in row['differences']}
        self.assertEqual(differences['camera_x']['native'], -0.05)
        self.assertEqual(differences['ones']['native'], 10)
        self.assertEqual(differences['ones']['godot'], 1)

    def test_cross_capture_display_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['rows'][13]['native_display'] += 1
        with self.assertRaisesRegex(ValueError, 'boundary'):
            s272.audit_pair(self.contract, scene)

    def test_missing_row_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            s272.audit_pair(self.contract, scene)

    def test_native_digit_substitution_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['rows'][13]['native']['ones'] = 1
        with self.assertRaisesRegex(ValueError, 'native state'):
            s272.audit_pair(self.contract, scene)

    def test_hidden_difference_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['rows'][13]['differences'].pop()
        with self.assertRaisesRegex(ValueError, 'differences'):
            s272.audit_pair(self.contract, scene)

    def test_false_green_summary_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['state_comparisons_passed'] = True
        with self.assertRaisesRegex(ValueError, 'summary'):
            s272.audit_pair(self.contract, scene)

    def test_equal_selected_fields_do_not_prove_phase(self):
        scene = copy.deepcopy(self.scene)
        for row in scene['rows']:
            row['godot'] = copy.deepcopy(row['native'])
            row['differences'] = []
        scene['state_comparisons_passed'] = True
        audit = s272.audit_pair(self.contract, scene)
        self.assertTrue(audit['selected_state_comparisons_passed'])
        self.assertFalse(audit['state_admitted'])
        self.assertFalse(audit['residual_family_classified'])


if __name__ == '__main__':
    unittest.main()
