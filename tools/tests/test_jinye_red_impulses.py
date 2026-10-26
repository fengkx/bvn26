"""Independent red amplitudes keep geometry and non-red channels fixed."""
import unittest
from tools.probes.build_jinye_affine_controls import controls as original
from tools.probes.build_jinye_red_impulses import controls,source_pixel
from tools.probes.decode_jinye_red_impulses import append_row


class JinyeRedImpulseTests(unittest.TestCase):
    def test_geometry_is_unchanged_from_pinned_controls(self):
        _,old=original();_,cases=controls();self.assertEqual(len(cases),48)
        for c in cases:
            base=old[c['base_case']]
            for field in ('shape','source_frame','fill','mask','matrix','outer','draw'):
                self.assertEqual(c[field],base[field])
            self.assertEqual(base['source'],c['corner']+2)
            self.assertNotEqual(c['draw'][0],2)

    def test_only_authored_red_impulse_changes(self):
        for source in range(12):
            pixels=[source_pixel(source,x,y) for y in range(40) for x in range(92)]
            self.assertTrue(all(p[1:]==[0,73,255] for p in pixels))
            self.assertEqual(sum(p[0]>0 for p in pixels),1)
            self.assertEqual(max(p[0] for p in pixels),(64,128,255)[source//4])

    def test_row_width_and_order_reject(self):
        active={'pixels':[]};row=['0']+['-16777216']*192
        append_row(active,row);self.assertEqual(len(active['pixels']),96)
        for bad in (row,row[:-1],row+['0']):
            with self.assertRaises(AssertionError):append_row(active,bad)


if __name__=='__main__':unittest.main()
