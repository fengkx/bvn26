from fractions import Fraction
import unittest

from tools.probes.analyze_jinye_translation_controls import actual_spec, models_for, native_pair_comparisons


class JinyeTranslationControlsTests(unittest.TestCase):
    def test_actual_twip_readback_replaces_request_without_mutating_it(self):
        requested = {"id": 0, "matrix": [1, 0, 0, 1, 0.125, -0.125]}
        readback = [0, 1, 0, 0, 1, 0.1, -0.1] + [0]*16
        result = actual_spec(requested, readback)
        self.assertEqual(result["matrix"][4:], [Fraction(1, 10), Fraction(-1, 10)])
        self.assertEqual(requested["matrix"][4:], [0.125, -0.125])

    def test_non_twip_property_is_rejected(self):
        requested = {"id": 0, "matrix": [1, 0, 0, 1, 0, 0]}
        readback = [0, 1, 0, 0, 1, 0.125, 0] + [0]*16
        with self.assertRaises(AssertionError):
            actual_spec(requested, readback)

    def test_scaled_translation_consumption_is_a_separate_global_model(self):
        spec = {"matrix": [1, 0, 0, 1, Fraction(3, 10), 0],
                "outer": [1, 0, 0, 1, 0, 0], "draw": [Fraction(1, 2), 0, 0, Fraction(1, 2), 0, 0]}
        shape = {"bitmap_matrix": {"scaleX": "20", "scaleY": "20"},
                 "mask_records": [{"type": "StyleChangeRecord", "fillStyle1": "2", "moveDeltaX": "0", "moveDeltaY": "0"}]
                 + [{"type": "StraightEdgeRecord", "generalLineFlag": "true", "deltaX": str(x), "deltaY": str(y)}
                    for x, y in [(40, 0), (0, 40), (-40, 0), (0, -40)]]
                 + [{"type": "EndShapeRecord"}]}
        models, _, _ = models_for(spec, shape)
        self.assertEqual(models["legacy_child_draw_quarters/center"][0][2], -16384)
        self.assertEqual(models["scaled_child_then_draw_quarters/center"][0][2], -32768)

    def test_native_pairs_use_parameter_adjacency_and_keep_every_pixel(self):
        offsets = [-1/64, 0, 1/64, 7/64, 8/64, 9/64, 15/64, 16/64, 17/64]
        specs = [{"id": index, "base_case": 0, "operand": "matrix", "axis": 0,
                  "source": 0, "shape": 56, "quarter_origin": 0, "offset": offset,
                  "draw": [1, 0, 0, 1, 0, 0]} for index, offset in enumerate(offsets)]
        captures = [{"source_case": index, "cached": cached,
                     "pixels": [[0, 0, 0, 0]]*3+[[int(index == 4), 0, 0, 0]]}
                    for index in range(9) for cached in (False, True)]
        readbacks = [[index]+[0]*22 for index in range(9)]
        pairs = native_pair_comparisons({"cases": specs, "size": [2, 2]}, captures, readbacks)
        self.assertEqual(len(pairs), 16)
        self.assertEqual(sum(row["changed_pixels"] for row in pairs), 4)
        self.assertTrue(all(row["child_translation_equal"] for row in pairs))
        self.assertEqual([row["cases"] for row in pairs if row["changed_pixels"]], [[3, 4], [4, 5]]*2)


if __name__ == "__main__":
    unittest.main()
