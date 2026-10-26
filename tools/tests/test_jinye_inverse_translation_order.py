import unittest
from fractions import Fraction
from tools.probes.analyze_jinye_inverse_translation_order import quantized_translation


class InverseTranslationOrderTests(unittest.TestCase):
    def test_rounding_order_is_input_defined(self):
        tx = ty = Fraction(-1, 2)
        self.assertEqual(quantized_translation(1, 1, tx, ty, 'quantize_coefficients_then_dot_then_round'), 1)
        self.assertEqual(quantized_translation(1, 1, tx, ty, 'quantize_coefficients_then_round_products_then_sum'), 2)

    def test_integer_products_agree(self):
        for order in ('quantize_coefficients_then_dot_then_round', 'quantize_coefficients_then_round_products_then_sum'):
            self.assertEqual(quantized_translation(3, -4, Fraction(2), Fraction(-1), order), -10)

    def test_unknown_order_fails_loud(self):
        with self.assertRaises(ValueError):
            quantized_translation(1, 1, Fraction(0), Fraction(0), 'matching_pixel')


if __name__ == '__main__':
    unittest.main()
