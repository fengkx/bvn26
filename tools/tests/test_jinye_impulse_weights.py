from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_impulse_weights import real_weight_interval, verify_gray_reference, weight_interval


class JinyeImpulseWeightTests(unittest.TestCase):
    def test_common_weight_intersects_all_amplitudes(self):
        self.assertEqual(weight_interval([16, 32, 63], 256), (64, 64))
        lower, upper = weight_interval([16, 31, 63], 256)
        self.assertGreater(lower, upper)

    def test_precision_constraints_do_not_select_a_feasible_coefficient(self):
        lower, upper = weight_interval([0, 0, 1], 256)
        self.assertGreater(lower, upper)
        self.assertEqual(weight_interval([0, 0, 1], 65536), (258, 511))

    def test_invalid_or_missing_amplitude_is_rejected(self):
        for values in ([1, 2], [65, 0, 0], [-1, 0, 0]):
            with self.assertRaises(ValueError):
                weight_interval(values, 256)

    def test_half_open_real_bounds_reject_even_without_quantized_coefficients(self):
        lower, upper = real_weight_interval([4, 10, 19])
        self.assertEqual((lower, upper), (Fraction(5, 64), Fraction(5, 64)))
        self.assertGreaterEqual(lower, upper)

    def test_gray_reference_checks_every_red_alpha_byte(self):
        common = {key: [] for key in ("matrix", "outer", "draw", "fill", "mask")}
        old_spec = dict(common, id=0, shape=56)
        spec = dict(old_spec, amplitude=255, base_case=0)
        pixels = [[0, 0, 73, 255] for _ in range(96*96)]
        pixels[234] = [1, 0, 73, 255]
        old_pixels = [[0, 0, 0, 255] for _ in range(96*96)]
        result = verify_gray_reference({"cases": [spec]}, [{"source_case": 0, "cached": False, "pixels": pixels}], [[0]*23],
                                       {"cases": [old_spec]}, [{"source_case": 0, "cached": False, "pixels": old_pixels}], [[0]*19])
        self.assertEqual(result[0]["red_alpha_exact"], 96*96-1)
        self.assertEqual(result[0]["failures"], [[42, 2, 1, 0, 255, 255]])


if __name__ == "__main__":
    unittest.main()
