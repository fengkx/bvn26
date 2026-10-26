import unittest
from tools.probes.audit_jinye_source_units import row_displacement, f32, changed_sample_addresses


class SourceUnitAuditTests(unittest.TestCase):
    def test_fixed_units_remain_subpixel(self):
        self.assertEqual(row_displacement([(65536, 0, 0, 0)], [(65536, 0, 1, 0)], [(0, 0, None), (10, 3, None)]), [1])

    def test_phase_and_gradient_are_both_counted(self):
        self.assertEqual(row_displacement([(65536, 0, 0, 0)], [(65537, 0, 0, 1)], [(0, 0, None), (10, 3, None)]), [11])

    def test_subbyte_changes_do_not_invent_changed_addresses(self):
        points = [(0, 0, None)]
        self.assertEqual(changed_sample_addresses([(0, 0, 32769, 0)], [(0, 0, 32770, 0)], points), 0)
        self.assertEqual(changed_sample_addresses([(0, 0, 32767, 0)], [(0, 0, 32768, 0)], points), 1)

    def test_float32_conversion_is_fixed_not_output_selected(self):
        self.assertEqual(f32(0.25), .25)
        self.assertEqual(f32(0.1), 0.10000000149011612)


if __name__ == '__main__':
    unittest.main()
