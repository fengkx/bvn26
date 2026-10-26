"""Source factorization preserves exact coefficients, masks, and dormant styles."""
import unittest
from tools.probes.build_jinye_axis_factorization import controls
from tools.probes.jinye_source_factorization_tags import parse
from tools.probes.decode_jinye_axis_factorization import append_row,recover_linear_property


class SourceFactorizationControls(unittest.TestCase):
    def test_exact_source_factorization(self):
        f=controls();self.assertEqual(len(f['cases']),10)
        for start in range(0,10,5):
            group=f['cases'][start:start+5]
            self.assertEqual([c['factor_id'] for c in group],[-1,0,1,2,3])
            self.assertTrue(all(c['expected_total_rational']==group[0]['expected_total_rational'] and c['expected_stage_mask_rational']==group[0]['expected_stage_mask_rational'] for c in group))

    def test_identity_preserves_source_semantics(self):
        f=controls()
        for cid in (56,57):
            shapes=[s for s in f['shapes'] if s['source_shape']==cid]
            baseline=shapes[0]['parsed'];identity=shapes[1]['parsed']
            self.assertEqual(baseline['mask_twips'],identity['mask_twips'])
            self.assertEqual(baseline['styles'][0],identity['styles'][0])
            for field in ('linear_fixed','translation_twips'):
                self.assertEqual(baseline['styles'][1][field],identity['styles'][1][field])
            for shape in shapes:self.assertEqual(parse(bytes.fromhex(shape['raw_tag_hex'])),shape['parsed'])

    def test_native_decimal_tie(self):
        self.assertEqual(recover_linear_property(1.69546508789063,1.695465087890625),1.695465087890625)
        with self.assertRaises(AssertionError):recover_linear_property(1.69546508789062,1.695465087890625)

    def test_rows_fail_closed(self):
        active={'pixels':[],'black':[]};row=['0']+['0','4278190080']*256
        for bad in (row[:-1],['1']+row[1:],['0',str(1<<32)]+row[2:]):
            with self.assertRaises(AssertionError):append_row(active,bad)
        append_row(active,row);self.assertEqual(len(active['pixels']),256)
        with self.assertRaises(AssertionError):append_row(active,row)


if __name__=='__main__':unittest.main()
