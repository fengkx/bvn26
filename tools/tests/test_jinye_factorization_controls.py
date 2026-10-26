"""Reject altered factorization geometry and incomplete native rows."""
import unittest
from tools.probes.build_jinye_factorization_controls import controls
from tools.probes.jinye_factorization_tags import encode_shape,parse_shape
from tools.probes.decode_jinye_factorization_controls import append_row


class FactorizationControls(unittest.TestCase):
    def test_exact_factorization_and_negative_masks(self):
        fixture=controls()
        self.assertEqual(len(fixture['cases']),20)
        self.assertTrue(any(x<0 or y<0 for s in fixture['shapes'] for x,y in s['parsed']['mask']))
        for start in range(0,20,5):
            group=fixture['cases'][start:start+5]
            self.assertTrue(all(c['expected_total']==group[0]['expected_total'] and c['expected_stage_mask']==group[0]['expected_stage_mask'] for c in group))

    def test_raw_shape_roundtrip(self):
        fill=[1,0,-2,1,0,0];mask=[[0,0],[92,0],[12,40],[-80,40]]
        parsed=parse_shape(encode_shape(56,fill,mask))
        self.assertEqual(parsed['fill'],fill);self.assertEqual(parsed['mask'],mask)
        self.assertEqual(parsed['fill_type'],67)

    def test_rows_fail_closed(self):
        active={'pixels':[],'black':[]}
        row=['0']+['0','4278190080']*192
        for bad in (row[:-1],['1']+row[1:],['0',str(1<<32)]+row[2:]):
            with self.assertRaises(AssertionError):append_row(active,bad)
        append_row(active,row)
        self.assertEqual(len(active['pixels']),192)
        with self.assertRaises(AssertionError):append_row(active,row)


if __name__=='__main__':unittest.main()
