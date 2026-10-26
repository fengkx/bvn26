from fractions import Fraction
import unittest
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_leaf_boundaries import decode
from tools.probes.jinye_jpeg_source import source as jpeg_source, decoded_planes
from tools.probes.analyze_jinye_smooth_leaf import source_geometry, compare_case

from tools.probes.analyze_jinye_smooth_leaf import compose, invert, pixel_class, sample, transform


class JinyeSmoothLeafTests(unittest.TestCase):
    def test_retained_native_counterexamples_keep_gate_closed(self):
        evidence = ROOT/'evidence/importer-loud-fail/r221'
        fixture, captures, _ = decode(evidence/'native')
        _, _, _, alpha = jpeg_source()
        pixels, _ = decoded_planes(ROOT/'evidence/importer-loud-fail/r220/jpeg/analysis', alpha)
        report = json.loads((evidence/'candidate.json').read_text())
        for observed, stored in zip(captures, report['cases']):
            spec = fixture['cases'][observed['source_case']]
            shape = next(s for s in fixture['shapes'] if s['id'] == spec['shape'])
            matrix, polygon = source_geometry(spec, shape)
            result = compare_case(pixels, matrix, polygon, observed['pixels'])
            for key, value in result.items():
                self.assertEqual(json.loads(json.dumps(value)), stored[key])
            self.assertLess(result['interior_exact'], result['geometry_classes']['interior'])
            self.assertFalse(result['baseline_admitted'])
        self.assertEqual(len(captures), len(report['cases']))
        self.assertFalse(report['production_admitted'])

    def test_inverse_preserves_signed_affine_matrix(self):
        matrix = list(map(Fraction, [2, 1, -1, 3, 4, -7]))
        point = [Fraction(13, 7), Fraction(-9, 11)]
        self.assertEqual(transform(invert(matrix), transform(matrix, point)), tuple(point))
        self.assertEqual(compose(matrix, invert(matrix)), [1, 0, 0, 1, 0, 0])

    def test_geometry_partition_does_not_consult_source_or_native(self):
        polygon = [(0, 0), (4, 0), (4, 4), (0, 4)]
        self.assertEqual(pixel_class(1, 1, polygon), "interior")
        self.assertEqual(pixel_class(0, 0, polygon), "coverage_unproved")
        self.assertEqual(pixel_class(8, 8, polygon), "outside")
        self.assertEqual(pixel_class(1, 1, list(reversed(polygon))), "interior")

    def test_four_channel_byte_weights_keep_premultiplied_alpha(self):
        source = [[0, 0, 0, 0] for _ in range(92*40)]
        source[0] = [255, 127, 63, 255]
        self.assertEqual(sample(source, (Fraction(1, 2), Fraction(1, 2))), source[0])
        self.assertEqual(sample(source, (Fraction(1), Fraction(1))), [63, 31, 15, 63])


if __name__ == "__main__":
    unittest.main()
