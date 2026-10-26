import unittest
from tools.probes.analyze_jinye_camera_translation import translated_comparison


class CameraTranslationTests(unittest.TestCase):
    def image(self, point):
        pixels = [[0, 0, 0, 0] for _ in range(64)]
        black = [[0, 0, 0, 255] for _ in range(64)]
        pixels[point[1]*8+point[0]] = [2, 6, 73, 255]
        black[point[1]*8+point[0]] = [2, 6, 73, 255]
        return {'pixels': pixels, 'black': black, 'bounds': [1, 1, 6, 6]}

    def test_integer_correspondence_preserves_pixels(self):
        pair = translated_comparison(self.image((3, 3)), self.image((4, 3)), [(2, 2), (5, 2), (5, 5), (2, 5)], (8, 8), (1, 0))
        self.assertEqual(pair['full']['samples'], 56)
        self.assertEqual(pair['full']['exact'], 56)
        self.assertTrue(pair['outside_overlap_clear'])

    def test_outside_overlap_nonzero_is_retained(self):
        b = self.image((4, 3))
        b['pixels'][0] = [0, 0, 0, 1]
        pair = translated_comparison(self.image((3, 3)), b, [(2, 2), (5, 2), (5, 5), (2, 5)], (8, 8), (1, 0))
        self.assertFalse(pair['outside_overlap_clear'])
        self.assertEqual(pair['outside_overlap']['pixels']['shifted']['failures'], [[0, 0, [0, 0, 0, 1]]])

    def test_fractional_offset_rejects(self):
        with self.assertRaises(ValueError):
            translated_comparison(self.image((3, 3)), self.image((4, 3)), [], (8, 8), (.5, 0))


if __name__ == '__main__':
    unittest.main()
