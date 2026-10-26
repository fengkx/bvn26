from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_factorization import compare_black_boundaries, compare_boundaries, effective_geometry, require_equivalent


class JinyeFactorizationAnalysisTests(unittest.TestCase):
    def test_exact_shear_factorization_preserves_matrix_and_stage_mask(self):
        identity = [1, 0, 0, 1, 0, 0]
        mask = [[0, 0], [4, 0], [4, 2], [0, 2]]
        baseline = effective_geometry(identity, [1, 0, .5, 1, 0, 0], identity, mask)
        changed = effective_geometry([1, 0, 2, 1, 0, 0], [1, 0, -1.5, 1, 0, 0], identity,
                                     [[0, 0], [4, 0], [8, 2], [4, 2]])
        require_equivalent(baseline, changed)
        self.assertEqual(baseline[0][2], Fraction(1, 2))

    def test_property_or_mask_difference_rejects_before_pixel_comparison(self):
        baseline = ([1]*6, [(0, 0)])
        for changed in (([2]*6, [(0, 0)]), ([1]*6, [(1, 0)])):
            with self.assertRaises(ValueError):
                require_equivalent(baseline, changed)

    def test_full_failures_survive_deep_interior_isolation(self):
        a = [[0, 0, 73, 255] for _ in range(100)]
        b = [list(p) for p in a]
        b[0] = [1, 0, 73, 255]
        b[55] = [1, 0, 73, 254]
        report = compare_boundaries(a, b, ((0, 0), (10, 0), (10, 10), (0, 10)), (10, 10))
        self.assertEqual(report['full']['exact'], 98)
        self.assertEqual(len(report['deep']['failures']), 1)
        self.assertEqual(len(report['outside_deep']['failures']), 1)
        self.assertEqual(len(report['deep_code_incompatible']), 1)
        self.assertEqual(report['deep']['samples']+report['outside_deep']['samples'], 100)

    def test_black_plane_is_compared_independently(self):
        left = [[0, 0, 0, 255] for _ in range(100)]
        right = [list(p) for p in left]
        right[55] = [1, 0, 0, 255]
        result = compare_black_boundaries(left, right, ((0, 0), (10, 0), (10, 10), (0, 10)), (10, 10))
        self.assertEqual(result['full']['exact'], 99)
        self.assertEqual(len(result['deep']['failures']), 1)
        self.assertNotIn('deep_code_compatible', result)


if __name__ == '__main__':
    unittest.main()
