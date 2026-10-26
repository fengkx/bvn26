import unittest

from tools.probes.analyze_jinye_deep_gradients import compare, deep_points, level_and_gradient_score


class JinyeDeepGradientTests(unittest.TestCase):
    def test_constant_level_bias_is_not_claimed_as_level_parity(self):
        points = [(x, y) for y in range(3) for x in range(4)]
        native = {(x, y): 2*x+3*y for x, y in points}
        predicted = {point: value+1 for point, value in native.items()}
        result = level_and_gradient_score(predicted, native, points)
        self.assertEqual(result["levels_exact"], 0)
        self.assertEqual(result["level_residual_histogram"], {1: 12})
        for axis in result["gradients"].values():
            self.assertEqual(axis["exact"], axis["samples"])

    def test_slope_error_is_not_removed_by_comparing_only_levels(self):
        points = [(x, 0) for x in range(4)]
        result = level_and_gradient_score({point: 3*point[0] for point in points},
                                          {point: 2*point[0] for point in points}, points)
        self.assertEqual(result["gradients"]["horizontal"]["exact"], 0)
        self.assertEqual(result["gradients"]["horizontal"]["samples"], 3)

    def test_deep_geometry_and_failed_native_invariant_retain_the_sample(self):
        polygon = ((-1, -1), (9, -1), (9, 9), (-1, 9))
        self.assertEqual(len(deep_points(polygon, (8, 8), 2)), 16)
        shape = {"bitmap_matrix": {"scaleX": "20", "scaleY": "20"},
                 "mask_records": [{"type": "StyleChangeRecord", "fillStyle1": "2", "moveDeltaX": "0", "moveDeltaY": "0"}]
                 + [{"type": "StraightEdgeRecord", "generalLineFlag": "true", "deltaX": str(x), "deltaY": str(y)}
                    for x, y in [(640, 0), (0, 640), (-640, 0), (0, -640)]] + [{"type": "EndShapeRecord"}]}
        spec = {"source": 0, "matrix": [1, 0, 0, 1, 0, 0], "outer": [1, 0, 0, 1, 0, 0], "draw": [1, 0, 0, 1, 0, 0]}
        source = [[2*x, 0, 73, 255] for y in range(40) for x in range(92)]
        native = [[2*x, 0, 73, 255] for y in range(8) for x in range(8)]
        native[3*8+3] = [6, 0, 72, 254]
        result = compare(source, spec, shape, native, (8, 8))
        self.assertFalse(result["opaque_constant_channel_invariants_exact"])
        self.assertEqual(result["invariant_failures"], [[3, 3, [6, 0, 72, 254]]])
        self.assertEqual(result["deep_geometry_samples"], 25)
        self.assertTrue(all(row["samples"] == 25 for row in result["models"].values()))


if __name__ == "__main__":
    unittest.main()
