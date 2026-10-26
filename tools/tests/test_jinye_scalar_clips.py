import unittest

from tools.probes.analyze_jinye_scalar_clips import matched_points, score


class JinyeScalarClipTests(unittest.TestCase):
    def test_matched_membership_uses_same_geometry_and_declared_clip(self):
        points = [(1, 0, None), (1, 1, None), (2, 0, None)]
        self.assertEqual(matched_points(points, [1, 0, 1, 1]), [(1, 0)])
        with self.assertRaises(ValueError):
            matched_points(points, [1, 0, 2, 1])

    def test_score_distinguishes_scalar_fix_regression_and_persistent_failure(self):
        source = [[20, 0, 73, 255]]*3680
        rows = ((0, 0, 0, 32768), (0, 0, 0, 32768))
        exact = [20, 0, 73, 255]
        bad = [21, 0, 73, 255]
        result = score(source, rows, [(x, 0) for x in range(4)],
                       [exact, bad, bad, exact], [bad, exact, bad, exact], (4, 1))
        self.assertEqual(result['exact'], {'scalar': 2, 'full': 2, 'native_pair': 2})
        self.assertEqual(set(result['transitions'].values()), {1})
        self.assertEqual(len(result['failures']), 3)

    def test_extent_mismatch_rejects(self):
        with self.assertRaises(ValueError):
            score([], [], [], [], [[0]*4], (1, 1))


if __name__ == '__main__':
    unittest.main()
