import unittest

from tools.probes.analyze_jinye_nearest_origin import compatible_texel, compare_nearest, compare_smooth_channels, predict_nearest


class JinyeNearestOriginAnalysisTests(unittest.TestCase):
    def test_codes_require_full_alpha_constant_channel_and_source_range(self):
        self.assertEqual(compatible_texel([90, 114, 73, 255]), [45, 19])
        for pixel in ([91, 114, 73, 255], [90, 115, 73, 255], [90, 114, 73, 254], [90, 114, 72, 255], [184, 114, 73, 255]):
            self.assertIsNone(compatible_texel(pixel))

    def test_nearest_has_no_smooth_half_texel_subtraction(self):
        rows = ((65536, 0, 0, 32768), (0, 65536, 0, 32768))
        self.assertEqual(predict_nearest(rows, 45, 19), [90, 114, 73, 255])
        self.assertEqual(predict_nearest(rows, -2, 90), [0, 234, 73, 255])

    def test_incompatible_codes_are_retained_in_model_denominator(self):
        rows = ((0, 0, 0, 0), (0, 0, 0, 0))
        report = compare_nearest([[1, 0, 73, 255]], [(0, 0)], {'fixed': rows}, (1, 1))
        self.assertEqual(report['texel_compatible'], 0)
        self.assertEqual(report['models']['fixed']['samples'], 1)
        self.assertEqual(report['models']['fixed']['exact'], 0)

    def test_smooth_crosscheck_keeps_channel_and_alpha_failures(self):
        good = compare_smooth_channels([[90, 114, 73, 255]], [[90, 0, 73, 255]], [[0, 114, 73, 255]], (1, 1))
        self.assertEqual(good['exact'], 1)
        bad = compare_smooth_channels([[90, 114, 73, 255]], [[90, 0, 73, 254]], [[0, 114, 73, 255]], (1, 1))
        self.assertEqual(bad['exact'], 0)


if __name__ == '__main__':
    unittest.main()
