import unittest
from tools.probes.analyze_jinye_phase_constraints import cell_bounds, intersect, finalize


class PhaseConstraintTests(unittest.TestCase):
    def test_interior_half_open_floor_interval(self):
        self.assertEqual(cell_bounds(100, 3, 92), (3*65536-100, 4*65536-101))

    def test_clamp_edges_are_unbounded(self):
        self.assertEqual(cell_bounds(100, 0, 92), (None, 65535-100))
        self.assertEqual(cell_bounds(100, 91, 92), (91*65536-100, None))

    def test_empty_intersection_keeps_both_witnesses(self):
        state = dict(constraints=0, lower=None, upper=None, lower_witness=None, upper_witness=None, predeclared_phases={3})
        intersect(state, (5, 10), {'case': 1})
        intersect(state, (0, 4), {'case': 2})
        result = finalize(state)
        self.assertFalse(result['constant_phase_feasible'])
        self.assertEqual(result['lower_witness'], {'case': 1})
        self.assertEqual(result['upper_witness'], {'case': 2})
        self.assertFalse(result['predeclared_phase_results'][0]['satisfies_all_constraints'])


if __name__ == '__main__':
    unittest.main()
