import unittest
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.compare_jinye_tag_controls import analyze
from tools.probes.decode_jinye_tag_controls import decode

from tools.probes.compare_jinye_tag_controls import compare_pixels


class JinyeTagControlsTests(unittest.TestCase):
    def test_native_equivalence_is_bounded_and_bad_source_is_rejected(self):
        evidence = ROOT/'evidence/importer-loud-fail/r223'
        report = analyze(evidence/'native')
        self.assertEqual(json.loads(json.dumps(report)), json.loads((evidence/'comparison.json').read_text()))
        self.assertEqual((report['images_exact'], report['pixels_exact']), (72, 663552))
        self.assertTrue(report['bounded_source_tag_equivalence_proved'])
        self.assertFalse(report['general_source_tag_equivalence_proved'])
        self.assertFalse(report['production_admitted'])
        with self.assertRaises(AssertionError):
            decode(evidence/'rejected-short-header')

    def test_single_byte_difference_is_retained_without_tolerance(self):
        polygon = [(-1, -1), (4, -1), (4, 4), (-1, 4)]
        result = compare_pixels([[1, 2, 3, 255], [0, 0, 0, 0]],
                                [[1, 2, 4, 255], [0, 0, 0, 0]], polygon, width=2)
        self.assertEqual((result["exact"], result["samples"]), (1, 2))
        self.assertEqual(result["max_channel_delta"], [0, 0, 1, 0])
        self.assertEqual(result["differences_by_geometry"], {"interior": 1})
        self.assertEqual(result["failures"][0]["delta"], [0, 0, -1, 0])
        self.assertEqual(result["alpha_support_union_exact"], 0)

    def test_geometry_partition_does_not_hide_outside_differences(self):
        polygon = [(1, 1), (3, 1), (3, 3), (1, 3)]
        actual = [[0, 0, 0, 0] for _ in range(36)]
        native = [list(pixel) for pixel in actual]
        native[35] = [1, 1, 1, 1]
        result = compare_pixels(actual, native, polygon, width=6)
        self.assertEqual(result["differences_by_geometry"], {"outside": 1})
        self.assertEqual((result["failures"][0]["x"], result["failures"][0]["y"]), (5, 5))

    def test_mismatched_image_size_fails(self):
        with self.assertRaisesRegex(ValueError, "sizes differ"):
            compare_pixels([], [[0, 0, 0, 0]], [])


if __name__ == "__main__":
    unittest.main()
