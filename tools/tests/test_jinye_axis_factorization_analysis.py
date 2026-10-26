import unittest
from tools.probes.analyze_jinye_axis_factorization import factor_groups
from tools.probes.analyze_jinye_source_factorization import baseline_gate, pair_result


class AxisFactorizationTests(unittest.TestCase):
    def cases(self):
        return [{'source_shape': 56, 'draw': [.25], 'factor_id': i} for i in (-1, 0, 1, 2, 3)]

    def test_raw_baseline_is_mandatory(self):
        self.assertEqual(len(factor_groups(self.cases())), 1)
        with self.assertRaises(ValueError):
            factor_groups(self.cases()[1:])

    def test_duplicate_factors_reject(self):
        with self.assertRaises(ValueError):
            factor_groups(self.cases()+self.cases()[:1])

    def test_raw_or_black_baseline_difference_rejects(self):
        a = {'bounds': [0, 0, 1, 1], 'pixels': [[2, 6, 73, 255]], 'black': [[2, 6, 73, 255]]}
        for plane in ('pixels', 'black'):
            b = dict(a, **{plane: [[4, 6, 73, 255]]})
            pair = pair_result(a, b, [(0, 0), (1, 0), (1, 1), (0, 1)], (1, 1))
            self.assertFalse(baseline_gate([pair]))


if __name__ == '__main__':
    unittest.main()
