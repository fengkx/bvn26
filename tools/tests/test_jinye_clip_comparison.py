import unittest

from tools.probes.analyze_jinye_clip_controls import analyze_clips, clip_points, compare_at


class JinyeClipComparisonTests(unittest.TestCase):
    def test_clip_membership_uses_only_declared_integer_geometry(self):
        self.assertEqual(clip_points((-1, 0, 3, 2), (3, 3)), {(0, 0), (1, 0), (0, 1), (1, 1)})
        for rect in ((0.5, 0, 1, 1), (0, 0, -1, 1)):
            with self.assertRaises(ValueError):
                clip_points(rect, (3, 3))

    def test_same_coordinate_overlap_retains_differences_and_outside_leaks(self):
        baseline = [[10, 0, 73, 255]]*4
        a = [[0, 0, 0, 0], [10, 0, 73, 255], [11, 0, 73, 255], [0, 0, 0, 0]]
        b = [[1, 0, 0, 0], [0, 0, 0, 0], [10, 0, 73, 255], [10, 0, 73, 255]]
        result = analyze_clips({0: a, 1: b}, {0: (1, 0, 2, 1), 1: (2, 0, 2, 1)}, baseline, (4, 1))
        self.assertEqual(result['overlap_pairs'][0]['samples'], 1)
        self.assertEqual(result['overlap_pairs'][0]['exact'], 0)
        self.assertEqual(result['overlap_pairs'][0]['failures'][0][:2], [2, 0])
        self.assertEqual(len(result['clips'][1]['outside_vs_clear']['failures']), 1)
        self.assertEqual(result['clips'][0]['inside_vs_baseline']['exact'], 1)

    def test_missing_capture_and_image_size_mismatch_reject(self):
        with self.assertRaises(ValueError):
            analyze_clips({}, {0: (0, 0, 1, 1)}, [[0]*4], (1, 1))
        with self.assertRaises(ValueError):
            compare_at([], [[0]*4], {(0, 0)}, (1, 1))


if __name__ == '__main__':
    unittest.main()
