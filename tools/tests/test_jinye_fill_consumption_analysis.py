from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_fill_consumption import collapsed_fill_pairs, combined_translation_model, common_geometry, draw_consumption_pairs, native_delta


class JinyeFillConsumptionAnalysisTests(unittest.TestCase):
    def test_common_geometry_intersects_every_declared_control(self):
        self.assertEqual(common_geometry([[(0, 0), (1, 0)], [(1, 0), (2, 0)], [(1, 0)]]), [(1, 0)])
        with self.assertRaises(ValueError):
            common_geometry([])

    def test_consumption_separates_combined_translation_and_signed_draw_offset(self):
        direct = [1, 0, 0, 1, Fraction(3, 8), Fraction(-3, 8)]
        draw = [1, 0, 0, 1, Fraction(1, 8), Fraction(-1, 8)]
        rows = combined_translation_model(direct, draw)
        self.assertEqual(rows[0], (65536, 0, -16384, 32768))
        self.assertEqual(rows[1], (0, 65536, 16384, 32768))
        self.assertEqual(direct[4:], [Fraction(3, 8), Fraction(-3, 8)])

    def test_combined_quarter_ties_are_even(self):
        direct = [1, 0, 0, 1, Fraction(1, 8), Fraction(3, 8)]
        rows = combined_translation_model(direct, [1, 0, 0, 1, 0, 0])
        self.assertEqual([rows[0][2], rows[1][2]], [0, -32768])

    def test_draw_pair_groups_use_input_readbacks_and_preserve_counterexamples(self):
        cases = []
        for cid, value, red in ((0, 1.0, 2), (1, 1.015625, 4), (2, 1.25, 2)):
            matrix = [0]*23
            matrix[17] = value
            cases.append({'case': cid, 'baseline_id': 0, 'cached': False, 'draw_control': {'axis': 0},
                          'native_matrix_readback': matrix, 'codes': [[0, 0, [red, 0, 73, 255], [red//2, 0]]]})
        report = draw_consumption_pairs(cases)
        self.assertEqual(report['pair_count'], 1)
        self.assertEqual(report['changed_pairs'], 1)
        self.assertEqual(report['pairs'][0]['failures'], [[0, 0, [2, 0, 73, 255], [4, 0, 73, 255]]])

    def test_identical_candidate_rows_cannot_hide_native_fill_changes(self):
        common = {'baseline_id': 0, 'cached': False, 'draw_variant': 0,
                  'fixed_coordinate_rows': {'combined_fill_child_then_draw_quarters/minimum': ((1, 0, 0, 0), (0, 1, 0, 0))}}
        a = dict(common, case=0, codes=[[0, 0, [2, 0, 73, 255], [1, 0]]])
        b = dict(common, case=1, codes=[[0, 0, [4, 0, 73, 255], [2, 0]]])
        result = collapsed_fill_pairs([a, b])
        self.assertEqual(result['pair_count'], 1)
        self.assertEqual(result['changed_pairs'], 1)
        self.assertEqual(result['exact'], 0)

    def test_native_delta_retains_noncode_pixels_without_selection(self):
        report = native_delta([[1, 0, 73, 254]], [[0, 0, 73, 255]], [(0, 0)], (1, 1))
        self.assertEqual(report['samples'], 1)
        self.assertEqual(report['exact'], 0)
        self.assertEqual(report['max_channel_delta'], [1, 0, 0, 1])


if __name__ == '__main__':
    unittest.main()
