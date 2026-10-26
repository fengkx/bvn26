"""Clip controls preserve coordinates and distinguish API argument forms."""
import unittest
from tools.probes.build_jinye_affine_controls import controls as old_controls
from tools.probes.build_jinye_clip_controls import controls
from tools.probes.decode_jinye_clip_controls import append_row,require_clear_outside


class JinyeClipTests(unittest.TestCase):
    def test_grid_preserves_source_transform_and_camera(self):
        _,old=old_controls();_,cases,clips=controls()
        self.assertEqual(len(cases),24);self.assertEqual(len(clips),17)
        self.assertIsNone(clips[0]);self.assertEqual(clips[1],[0,0,96,96])
        self.assertEqual(clips[2:],[[x,0,w,96] for x in (46,47,48) for w in (1,3,4,5,16)])
        for c in cases:
            base=old[c['base_case']]
            self.assertEqual({k:v for k,v in c.items() if k not in ('id','base_case')},{k:v for k,v in base.items() if k!='id'})

    def test_readback_row_width_and_order(self):
        active={'pixels':[]};row=['0']+['-16777216']*192
        append_row(active,row);self.assertEqual(len(active['pixels']),96)
        for invalid in (row,row[:-1],row+['0']):
            with self.assertRaises(AssertionError):append_row(active,invalid)

    def test_outside_clip_nonzero_rejects(self):
        case={'source_case':0,'cached':False,'clip_id':2,'clip':[46,0,1,96],'pixels':[[0]*4 for _ in range(96*96)]}
        case['pixels'][46]=[1,2,3,255];require_clear_outside(case)
        case['pixels'][47]=[0,0,0,1]
        with self.assertRaisesRegex(ValueError,'1 pixels'):require_clear_outside(case)


if __name__=='__main__':unittest.main()
