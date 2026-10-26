from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_factored_phase import projected_phase


class JinyeFactoredPhaseAnalysisTests(unittest.TestCase):
    def test_identity_fill_preserves_display_phase_and_full_coefficients(self):
        rows = ((65536, 120, -300, 32000), (-200, 65536, 800, 31000))
        self.assertEqual(projected_phase(rows, rows, [1, 0, 0, 1, 0, 0]), rows)

    def test_projection_uses_linear_fill_only_and_rounds_once(self):
        full = ((3, 5, 7, 999), (11, 13, 17, 999))
        display = ((0, 0, 9999, 1), (0, 0, -9999, 3))
        inverse = [Fraction(1, 2), Fraction(-1, 2), 0, 1, 10000, -10000]
        self.assertEqual(projected_phase(full, display, inverse), ((3, 5, 7, 0), (11, 13, 17, 2)))
        self.assertEqual(full[0][3], 999)

    def test_projection_retains_signed_cross_terms_without_minimum_reselection(self):
        full = ((1, 2, 3, 0), (4, 5, 6, 0))
        display = ((0, 0, 0, 20), (0, 0, 0, -10))
        self.assertEqual(projected_phase(full, display, [0, 1, -1, 0, 0, 0]), ((1, 2, 3, 10), (4, 5, 6, 20)))


if __name__ == '__main__':
    unittest.main()
