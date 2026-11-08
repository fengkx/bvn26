"""Adversarial checks of negative-only raw/source joins, never pixel proof."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s362_route', HERE / 'derive_digit_witnesses.py')
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


class DigitWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((route.LOCKED / 'native-capture.log.gz').read_bytes())
        cls.run_id = json.loads((route.LOCKED / 'native-build.json').read_text())['run_id']
        cls.scene = json.loads((route.LOCKED / 'paired-scene.json').read_text())
        cls.source = json.loads((route.LOCKED / 'source-contract.json').read_text())

    def derive(self, raw=None, scene=None, source=None):
        return route.derive(self.raw if raw is None else raw, self.run_id,
                            self.scene if scene is None else scene,
                            self.source if source is None else source)

    def test_raw_source_witnesses_cover_all_boundaries(self):
        result = self.derive()
        self.assertEqual(result, json.loads((HERE / 'digit-witnesses.json').read_text()))
        self.assertEqual(result['boundaries_with_digit_conflict'], 61)
        self.assertEqual(result['rows'][0]['witness']['native_source_shape'], 1806)
        self.assertEqual(result['rows'][0]['witness']['scene_source_shape'], 1800)

    def test_cross_run_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cross-run'):
            self.derive(raw=self.raw.replace(self.run_id.encode(), b'other-run', 1))

    def test_wrong_display_or_callback_cannot_join_by_tick(self):
        for field in ('native_display', 'replayed_firings'):
            scene = copy.deepcopy(self.scene)
            scene['rows'][0][field] += 1
            with self.assertRaisesRegex(ValueError, 'boundary join'):
                self.derive(scene=scene)

    def test_missing_duplicate_and_truncated_rows_rejected(self):
        for rows in (self.scene['rows'][:-1], self.scene['rows'] + [self.scene['rows'][0]]):
            with self.assertRaises(ValueError):
                self.derive(scene={**self.scene, 'rows': rows})
        with self.assertRaises(ValueError):
            self.derive(raw=self.raw[:self.raw.rfind(b'|s262_end|')])

    def test_equal_digits_never_establish_admission(self):
        scene = copy.deepcopy(self.scene)
        for row in scene['rows']:
            for field in ('tens', 'ones'):
                row['godot'][field] = row['native'][field]
        result = self.derive(scene=scene)
        self.assertEqual(result['boundaries_with_digit_conflict'], 0)
        self.assertFalse(result['complete_admission_inferred'])
        self.assertIsNone(result['exact_rgba_edge_residual'])
        self.assertTrue(all(row['witness'] is None for row in result['rows']))

    def test_no_dependency_on_camera_or_recorded_difference_summary(self):
        scene = copy.deepcopy(self.scene)
        for row in scene['rows']:
            row['differences'] = []
            row['godot']['camera_scale'] = row['native']['camera_scale']
        self.assertEqual(self.derive(), self.derive(scene=scene))

    def test_unknown_source_frame_rejected(self):
        source = copy.deepcopy(self.source)
        source['symbols']['1810']['changes'].pop()
        with self.assertRaisesRegex(ValueError, 'source glyph mapping'):
            self.derive(source=source)


if __name__ == '__main__':
    unittest.main()
