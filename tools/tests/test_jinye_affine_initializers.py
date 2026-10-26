from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_affine_initializers import fixed_rows, sample_fixed
from tools.probes.analyze_jinye_smooth_leaf import sample


class JinyeAffineInitializerTests(unittest.TestCase):
    def test_positive_axis_center_and_minimum_reduce_to_same_offset(self):
        for scale in (Fraction(3), Fraction(5), Fraction(13), Fraction(5, 2)):
            matrix = [scale, 0, 0, scale, Fraction(-3, 4), Fraction(5, 4)]
            self.assertEqual(fixed_rows(matrix, "center"), fixed_rows(matrix, "minimum"))

    def test_fixed_sampler_keeps_signed_fraction_and_rgba_weights(self):
        source = [[x, y, 73, 255] for y in range(40) for x in range(92)]
        rows = ((65536, 0, -16384, 32768), (0, 65536, 8192, 32768))
        for x, y in ((0, 0), (1, 1), (45, 19), (91, 39)):
            point = (Fraction(x)-Fraction(1, 4)+Fraction(1, 2),
                     Fraction(y)+Fraction(1, 8)+Fraction(1, 2))
            self.assertEqual(sample_fixed(source, rows, x, y, "byte_weights"), sample(source, point))

    def test_geometry_offset_is_not_center_for_mixed_signed_inverse(self):
        matrix = list(map(Fraction, [1, 0, 1, 1, 0, 0]))
        center = fixed_rows(matrix, "center")
        minimum = fixed_rows(matrix, "minimum")
        self.assertEqual(center[0][:3], minimum[0][:3])
        self.assertNotEqual(center[0][3], minimum[0][3])


if __name__ == "__main__":
    unittest.main()
