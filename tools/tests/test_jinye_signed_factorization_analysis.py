import unittest
from fractions import Fraction
from tools.probes.analyze_jinye_axis_factorization import factor_groups
from tools.probes.analyze_jinye_factorization import require_equivalent
from tools.probes.analyze_jinye_signed_factorization import EXPECTED_FACTORS


class SignedFactorizationTests(unittest.TestCase):
    def cases(self):
        return [{'source_shape': 57, 'draw': [.25], 'factor_id': i} for i in EXPECTED_FACTORS]

    def test_all_predeclared_factors_required(self):
        self.assertEqual(len(factor_groups(self.cases(), EXPECTED_FACTORS)), 1)
        for missing in EXPECTED_FACTORS:
            with self.assertRaises(ValueError):
                factor_groups([c for c in self.cases() if c['factor_id'] != missing], EXPECTED_FACTORS)

    def test_unexpected_negative_factor_rejects(self):
        cases = self.cases()
        cases[0] = dict(cases[0], factor_id=-2)
        with self.assertRaises(ValueError):
            factor_groups(cases, EXPECTED_FACTORS)

    def test_reversing_stage_polygon_is_not_equivalence(self):
        matrix = list(map(Fraction, [1, 0, 0, 1, 0, 0]))
        polygon = [(0, 0), (2, 0), (2, 1), (0, 1)]
        with self.assertRaises(ValueError):
            require_equivalent((matrix, polygon), (matrix, list(reversed(polygon))))


if __name__ == '__main__':
    unittest.main()
