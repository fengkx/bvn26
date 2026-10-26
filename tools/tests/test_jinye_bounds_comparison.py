import unittest
from tools.probes.analyze_jinye_bounds_controls import require_outward_patch, aggregate
from tools.probes.analyze_jinye_source_factorization import pair_result, baseline_gate


class BoundsComparisonTests(unittest.TestCase):
    def test_outward_sides_are_independent(self):
        for side in range(4):
            after = [10, 20, 30, 40]
            after[side] += -1 if side in (0, 2) else 1
            require_outward_patch({'before': [10, 20, 30, 40], 'after': after, 'side': side,
                                  'amount_twips': 1, 'changed_bits': [7], 'allowed_changed_bits': [7, 8]})

    def test_other_bits_and_inward_changes_reject(self):
        patch = {'before': [10, 20, 30, 40], 'after': [9, 20, 30, 40], 'side': 0,
                 'amount_twips': 1, 'changed_bits': [7], 'allowed_changed_bits': [8]}
        with self.assertRaises(ValueError):
            require_outward_patch(patch)
        patch.update(changed_bits=[], after=[11, 20, 30, 40])
        with self.assertRaises(ValueError):
            require_outward_patch(patch)

    def test_black_plane_can_fail_baseline_independently(self):
        a = {'bounds': [0, 0, 1, 1], 'pixels': [[0, 0, 0, 0]], 'black': [[0, 0, 0, 255]]}
        b = dict(a, black=[[1, 0, 0, 255]])
        pair = pair_result(a, b, [(0, 0), (1, 0), (1, 1), (0, 1)], (1, 1))
        self.assertFalse(baseline_gate([pair]))
        report = aggregate([pair])
        self.assertEqual(report['raw']['full']['exact'], 1)
        self.assertEqual(report['black']['full']['exact'], 0)


if __name__ == '__main__':
    unittest.main()
