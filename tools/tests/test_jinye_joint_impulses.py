import unittest

from tools.probes.analyze_jinye_joint_impulses import CELLS, CORNERS, joint_groups, response, staged


class JinyeJointImpulseTests(unittest.TestCase):
    def test_cells_cover_exactly_all_touching_contiguous_footprints(self):
        expected = {(x-dx, y-dy) for x, y in CORNERS for dx in (0, 1) for dy in (0, 1)}
        self.assertEqual(set(CELLS), expected)
        self.assertEqual(len(CELLS), 9)

    def test_staged_floor_can_explain_rejected_single_weight_triplet(self):
        self.assertEqual([staged(a, 57, 90, "vertical_horizontal") for a in (64, 128, 255)], [4, 10, 19])
        self.assertEqual([staged(a, 57, 90, "horizontal_vertical") for a in (64, 128, 255)], [4, 9, 19])

    def test_common_cell_and_fractions_constrain_all_corners(self):
        self.assertEqual(response((45, 19), 0, 0, "vertical_horizontal"), (64, 128, 255)+(0,)*9)
        self.assertEqual(response((44, 18), 0, 0, "horizontal_vertical"), (0,)*12)
        self.assertEqual(response((45, 19), 128, 128, "vertical_horizontal"), (16, 32, 63)*4)
        with self.assertRaises(ValueError):
            response((43, 19), 0, 0, "vertical_horizontal")
        with self.assertRaises(ValueError):
            response((45, 19), 256, 0, "vertical_horizontal")

    def test_grouping_rejects_missing_or_different_coordinate_sets(self):
        cases = [dict(shape=56, scale=1, cached=False, corner=c, base_case=c,
                      constraints=[[7, 8, c, c, c]]) for c in range(4)]
        group = joint_groups({"cases": cases})[0]
        self.assertEqual(group["rows"], [(7, 8, (0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3))])
        with self.assertRaises(AssertionError):
            joint_groups({"cases": cases[:3]})
        cases[3]["constraints"][0][0] = 6
        with self.assertRaises(AssertionError):
            joint_groups({"cases": cases})


if __name__ == "__main__":
    unittest.main()
