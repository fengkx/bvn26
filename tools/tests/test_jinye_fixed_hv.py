import unittest

from tools.probes.analyze_jinye_fixed_hv import interpolate_hv, sample_hv
from tools.probes.analyze_jinye_joint_impulses import staged


class JinyeFixedHvTests(unittest.TestCase):
    def test_hv_uses_horizontal_floor_before_vertical(self):
        for amplitude in (64, 128, 255):
            pixels = [[amplitude]*4, [0]*4, [0]*4, [0]*4]
            self.assertEqual(interpolate_hv(pixels, 199, 166), [staged(amplitude, 57, 90, "horizontal_vertical")]*4)
        self.assertEqual(interpolate_hv([[128]*4, [0]*4, [0]*4, [0]*4], 199, 166), [9]*4)

    def test_constant_channels_and_alpha_survive(self):
        pixels = [[20, 0, 73, 255], [111, 0, 73, 255], [241, 0, 73, 255], [37, 0, 73, 255]]
        for fx, fy in ((0, 0), (255, 255), (127, 86)):
            self.assertEqual(interpolate_hv(pixels, fx, fy)[1:], [0, 73, 255])

    def test_sampler_preserves_fixed_coordinates_and_clamp(self):
        source = [[x, y, 73, 255] for y in range(40) for x in range(92)]
        rows = ((65536, 0, 0, 32768), (0, 65536, 0, 32768))
        self.assertEqual(sample_hv(source, rows, 45, 19), [45, 19, 73, 255])
        self.assertEqual(sample_hv(source, rows, -2, 90), [0, 39, 73, 255])


if __name__ == "__main__":
    unittest.main()
