from fractions import Fraction
import unittest
import gzip
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_smooth_controls import analyze

from tools.probes.analyze_jinye_smooth_controls import score, separable_sample


class JinyeSmoothControlsTests(unittest.TestCase):
    def test_native_controls_keep_both_fixed_models_rejected(self):
        evidence = ROOT/'evidence/importer-loud-fail/r222'
        actual = analyze(evidence/'native')
        stored = json.loads(gzip.decompress((evidence/'analysis.json.gz').read_bytes()))
        self.assertEqual(json.loads(json.dumps(actual)), stored)
        self.assertEqual(actual['source_readback_pixels_exact'], 22080)
        self.assertEqual(len(actual['cases']), 72)
        for result in actual['totals'].values():
            self.assertEqual(result['samples'], 329280)
            self.assertLess(result['exact'], result['samples'])
        self.assertFalse(actual['source_tag_equivalence_proved'])
        self.assertFalse(actual['sampler_admitted'])
        self.assertFalse(actual['production_admitted'])

    def test_separable_order_is_globally_fixed(self):
        source = [[0, 0, 0, 255] for _ in range(92*40)]
        source[0] = [255, 128, 64, 255]
        self.assertEqual(separable_sample(source, (Fraction(1), Fraction(1))), [63, 32, 16, 255])

    def test_geometry_and_centroid_constraints_retain_all_control_pixels(self):
        source = [[2*x, 0, 73, 255] for y in range(40) for x in range(92)]
        matrix = tuple(map(Fraction, [1, 0, 0, 1, 0, 0]))
        polygon = tuple((Fraction(x), Fraction(y)) for x, y in [(-1, -1), (3, -1), (3, 3), (-1, 3)])
        native = [source[0], source[1], source[92], source[93]]
        result = score(source, matrix, polygon, native, ramp_axis=0, ramp_step=2, size=(2, 2))
        self.assertEqual(result["geometry_classes"], {"interior": 4})
        self.assertEqual(result["centroid_contains_ideal"], 4)
        for rule in result["fixed_constructions"].values():
            self.assertEqual((rule["exact"], rule["samples"]), (4, 4))
        self.assertFalse(result["sampler_admitted"])


if __name__ == "__main__":
    unittest.main()
