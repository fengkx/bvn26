"""A smooth-affine hypothesis must retain independently captured axis controls."""
import unittest
from tools.probes.analyze_smooth_affine_axis_reduction import analyze, axis


class SmoothAffineAxisReductionTests(unittest.TestCase):
    def test_fixed_geometry_reduction_retains_all_native_controls(self):
        report=analyze()
        for name,count in (('scalar',16377),('old',71824),('spans',9360)):
            self.assertEqual(report[name]['samples'],count)
            self.assertEqual(report[name]['exact'],count)
            self.assertEqual(report[name]['failures'],[])
        self.assertEqual(report['jiraiya']['exact_images'],6)
        self.assertEqual(sum(row['exact'] for row in report['jiraiya']['cases']),589824)
        self.assertTrue(report['axis_reduction_exact'])
        self.assertFalse(report['repeat_initializer_changed'])
        self.assertFalse(report['affine_smoothing_admitted'])
        self.assertFalse(report['production_admitted'])

    def test_reduction_does_not_admit_other_scale_or_rounding_domains(self):
        for scale in (0,-1):
            with self.assertRaises(AssertionError):
                axis(scale,0,0,'even')
        with self.assertRaises(AssertionError):
            axis(3,0,0,'ceiling')
