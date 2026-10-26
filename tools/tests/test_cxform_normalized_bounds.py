"""Sequence-specific intervals are rejection constraints, never coefficients."""
import gzip
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cxform_normalized_bounds import channel, interval, MAX_FINITE, from_bits


class NormalizedBoundsTests(unittest.TestCase):
    def test_negative_endpoints_and_constant_channels(self):
        args = (25,49,-129,128,100)
        for mode in ('divide','multiply_rounded','multiply_estimated'):
            lo,hi = interval(args,mode,12)
            self.assertEqual(channel(args,from_bits(lo),mode),12)
            self.assertEqual(channel(args,from_bits(hi),mode),12)
            self.assertGreater(channel(args,from_bits(lo-1),mode),12)
            self.assertLess(channel(args,from_bits(hi+1),mode),12)
            constant = (0,49,-129,128,100)
            target = channel(constant,0,mode)
            self.assertEqual(interval(constant,mode,target),(0,MAX_FINITE))
            low,high = interval(constant,mode,target+1)
            self.assertGreater(low,high)

    def test_recorded_native_witness_bounds(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r55/analysis.json.gz'
        r = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(r['old_constraints']+r['signed_constraints'],1302912)
        for mode,model in r['models'].items():
            self.assertEqual(len(model['intervals']),255)
            self.assertEqual(model['empty_alphas'],[])
            for bound in model['intervals'].values():
                self.assertLessEqual(bound['low_bits'],bound['high_bits'])
                for field,index in (('lower_witness',0),('upper_witness',1)):
                    witness = bound[field]
                    if witness:
                        exact = interval(tuple(witness['args']),mode,witness['native'])
                        self.assertEqual(exact[index],bound['low_bits' if index==0 else 'high_bits'])
            self.assertTrue(all(v['inside']<255 for v in model['membership'].values()))
        for flag in ('coefficients_selected','candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(r[flag])


if __name__=='__main__':
    unittest.main()
