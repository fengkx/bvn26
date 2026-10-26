from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_source_factorization import baseline_gate, raw_geometry, recover_matrix


class JinyeSourceFactorizationAnalysisTests(unittest.TestCase):
    def test_exact_native_half_up_print_recovers_binary_coefficient(self):
        expected = [1.695465087890625, 0.0, 0.0, 1.0, -322.85, -118.85]
        actual = [1.69546508789063, 0.0, 0.0, 1.0, -322.85, -118.85]
        matrix = recover_matrix(actual, expected)
        self.assertEqual(matrix[0], Fraction(expected[0]))
        self.assertEqual(matrix[4], Fraction(-6457, 20))
        actual[0] = 1.69546508789062
        with self.assertRaises((ValueError, AssertionError)):
            recover_matrix(actual, expected)

    def test_raw_fill_and_mask_use_authoritative_integer_fields(self):
        parsed = {'styles': [{}, {'bitmap': 55, 'type': 67, 'linear_fixed': [1310720, 0, 655360, 1310720],
                                 'translation_twips': [1, -1]}], 'mask_twips': [[1, 3], [21, 3]]}
        fill, mask = raw_geometry(parsed)
        self.assertEqual(fill, [1, 0, Fraction(1, 2), 1, Fraction(1, 20), Fraction(-1, 20)])
        self.assertEqual(mask[0], (Fraction(1, 20), Fraction(3, 20)))

    def test_baseline_requires_both_planes_and_nonempty_inventory(self):
        pair = {'full': {'samples': 4, 'exact': 4}, 'black_composition': {'full': {'samples': 4, 'exact': 4}}}
        self.assertTrue(baseline_gate([pair]))
        pair['black_composition']['full']['exact'] = 3
        self.assertFalse(baseline_gate([pair]))
        self.assertFalse(baseline_gate([]))


if __name__ == '__main__':
    unittest.main()
