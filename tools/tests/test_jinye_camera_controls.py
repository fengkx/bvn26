"""Camera controls move only the final destination translation."""
import unittest
from fractions import Fraction as Q
from tools.probes.build_jinye_camera_controls import controls
from tools.probes.build_jinye_signed_factorization import controls as old_controls
from tools.probes.decode_jinye_camera_controls import append_row


class CameraControls(unittest.TestCase):
    def test_only_camera_moves(self):
        f=controls();old=old_controls();self.assertEqual(len(f['cases']),70)
        raw={s['parsed']['shape']:s['raw_tag_hex'] for s in old['shapes']}
        self.assertTrue(all(s['raw_tag_hex']==raw[s['parsed']['shape']] for s in f['shapes']))
        for c in f['cases']:
            base=old['cases'][c['baseline_case']];offset=c['camera_offset']
            self.assertEqual(c['matrix'],base['matrix']);self.assertEqual(c['outer'],base['outer'])
            self.assertEqual(c['draw'][:4],base['draw'][:4])
            self.assertEqual(c['draw'][4:],[base['draw'][4+k]+offset[k] for k in (0,1)])
            self.assertTrue(all(0<=Q(v)<256 for p in c['expected_stage_mask_rational'] for v in p))

    def test_baseline_and_integer_correspondence(self):
        f=controls();old=old_controls()
        self.assertEqual(sum(c['camera_offset']==[0,0] for c in f['cases']),10)
        for c in f['cases']:
            base=old['cases'][c['baseline_case']]
            for got,want in zip(c['expected_stage_mask_rational'],base['expected_stage_mask_rational']):
                self.assertEqual([Q(got[k])-Q(want[k]) for k in (0,1)],c['camera_offset'])

    def test_short_rows_reject(self):
        with self.assertRaises(AssertionError):append_row({'pixels':[],'black':[]},['0'])


if __name__=='__main__':unittest.main()
