import unittest

from tools.test_move_cases import target_frame_ranges, target_seen


class MoveCasesTargetTests(unittest.TestCase):
    def test_multiple_target_intervals_are_supported(self):
        case = {'slot': 'p1', 'target_frames': [804, 865, 700, 803]}
        rows = [{'slot': 'p1', 'frame': 701}]
        self.assertEqual(target_frame_ranges(case), [(804, 865), (700, 803)])
        self.assertTrue(target_seen(case, rows))

    def test_null_target_is_valid(self):
        self.assertEqual(target_frame_ranges({'target_frames': [None, None]}), [])

    def test_odd_or_reversed_ranges_are_rejected(self):
        for values in ([1], [3, 2], [None, 2]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                target_frame_ranges({'target_frames': values})


if __name__ == '__main__':
    unittest.main()
