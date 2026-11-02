"""Adversarial checks of retained rank-9 evidence boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s281', HERE / 'diagnose.py')
s281 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s281)


class RasterPrerequisiteTests(unittest.TestCase):
    def setUp(self):
        self.raster = json.loads((HERE.parent / 's272/diagnosis.json').read_text())
        self.lifetime = json.loads((HERE.parent / 's274/diagnosis.json').read_text())
        self.identities = {s: s281.capture_identity(s) for s in ('s262', 's274')}

    def audit(self):
        return s281.audit_prerequisites(self.raster, self.lifetime, self.identities)

    def test_local_lifetime_success_does_not_admit_raster(self):
        result = self.audit()
        self.assertTrue(result['s274_read_only_replay']['bounded_encoded_lifetime_observed'])
        self.assertFalse(result['same_capture_state_admitted'])
        self.assertFalse(result['thin_raster_cut_proved'])
        self.assertIsNone(result['exact_rgba_edge_residual'])
        self.assertIsNone(result['exact_rgba_interior_residual'])
        self.assertEqual(result['matched_image_pairs'], 0)

    def test_capture_identity_substitution_rejected(self):
        self.identities['s274'] = copy.deepcopy(self.identities['s262'])
        with self.assertRaisesRegex(ValueError, 'distinct captures'):
            self.audit()

    def test_local_admission_promoted_to_scene_rejected(self):
        self.lifetime['scene_state_admitted'] = True
        with self.assertRaisesRegex(ValueError, 'scene claim'):
            self.audit()

    def test_historical_image_substitution_rejected(self):
        self.raster['pair_audit']['same_capture_godot_images_written'] = 61
        with self.assertRaisesRegex(ValueError, 'historical scene'):
            self.audit()

    def test_lifetime_image_claim_rejected(self):
        self.lifetime['images_written'] = 61
        with self.assertRaisesRegex(ValueError, 'lifetime images'):
            self.audit()

    def test_production_claim_rejected(self):
        for flag in ('production_admitted', 'native_parity_proven'):
            with self.subTest(flag=flag):
                self.lifetime[flag] = True
                with self.assertRaisesRegex(ValueError, 'unexpected admission'):
                    self.audit()
                self.lifetime[flag] = False

    def test_raw_replays_match_locked_diagnoses(self):
        result = s281.diagnose()['prerequisites']
        self.assertEqual(result['s262_via_s272']['events_revalidated'], 32227)
        self.assertEqual(result['s274_read_only_replay']['events_revalidated'], 26828)
        self.assertEqual(result['s262_via_s272']['callback_count'], 68)
        self.assertEqual(result['s274_read_only_replay']['callback_count'], 63)


if __name__ == '__main__':
    unittest.main()
