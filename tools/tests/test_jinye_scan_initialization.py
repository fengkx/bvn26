import unittest
from fractions import Fraction as F
from tools.probes.analyze_jinye_scan_initialization import initialized_base, ORDERS


class ScanInitializationTests(unittest.TestCase):
    def test_exact_integer_coefficients_agree(self):
        for order in ORDERS:
            self.assertEqual(initialized_base((F(2),F(-3),F(4)),(131072,-196608,262144,0),7,5,order),3*65536)

    def test_each_order_defers_only_its_own_start_axis(self):
        exact=(F(1,3),F(1,3),F(0));quantized=(21845,21845,0,0)
        self.assertEqual(initialized_base(exact,quantized,3,0,ORDERS[0]),65535)
        self.assertEqual(initialized_base(exact,quantized,3,0,ORDERS[1]),65535)
        self.assertEqual(initialized_base(exact,quantized,3,0,ORDERS[2]),65536)
        self.assertEqual(initialized_base(exact,quantized,0,3,ORDERS[1]),65536)

    def test_rgb_selected_order_rejects(self):
        with self.assertRaises(ValueError):
            initialized_base((F(1),F(1),F(0)),(65536,65536,0,0),0,0,'best_rgb')


if __name__ == '__main__':
    unittest.main()
