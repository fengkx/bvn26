import gzip
import json
import unittest

from tools.probes.analyze_cxform_amplified import (
    ALPHAS, ROOT, intersect, previous_report, read_samples,
)
from tools.probes.analyze_cxform_intervals import (
    channel, coefficient_measurements, f32, lower_bound,
)

EVIDENCE = ROOT/'evidence/importer-loud-fail/r43'


class CxformAmplifiedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_samples(EVIDENCE/'native')
        cls.report = json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes()))

    def test_fixed_grid_retains_input_readbacks_without_clamping(self):
        self.assertEqual(len(self.rows),10368)
        self.assertEqual({p[3] for _,_,p,_,_,_,_ in self.rows},set(ALPHAS))
        grids = {a:{(m,d,op) for _,_,p,_,m,d,op in self.rows if p[3]==a} for a in ALPHAS}
        self.assertTrue(all(grid==grids[146] for grid in grids.values()))
        self.assertEqual(len(grids[146]),81)

    def test_local_exactness_cannot_admit_globally_rejected_construction(self):
        measured = coefficient_measurements(ROOT/'evidence/importer-loud-fail/r41')
        for space in ('unit','normalized','byte'):
            for order in ('alpha_first','opacity_first','joint'):
                for _,_,p,n,m,d,op in self.rows:
                    reciprocal = measured[p[3]]['estimate_quotient']
                    if space!='unit':
                        reciprocal = f32(reciprocal*255)
                    self.assertEqual(channel((p[1],p[3],m,d,op),reciprocal,space,order),n[1])
            group = self.report['models'][space+'/alpha_first']
            self.assertTrue(all(v['inside']<v['alphas'] for v in group['membership'].values()))
        for key in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(self.report[key])

    def test_bounds_retain_all_old_constraints_and_native_witnesses(self):
        previous = previous_report()
        native = {}
        for i,x,p,n,m,d,op in self.rows:
            for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
                native[('amplified',i,x,ch)] = ([p[ch],p[3],mul,offset,op],n[ch])
        for key,group in self.report['models'].items():
            space,order = key.split('/')
            pairs = [(group['green_intervals'],previous['green_intersections'][key]['intervals'])]
            if order=='alpha_first':
                pairs.append((group['combined_intervals'],previous['combined_intersections'][space]['intervals']))
                self.assertEqual(group['total_constraints'],661248)
                self.assertEqual(set(map(int,group['tightened_alphas'])),set(ALPHAS))
            for intervals,old in pairs:
                for a,interval in intervals.items():
                    if a in old:
                        self.assertGreaterEqual(interval['low_bits'],old[a]['low_bits'])
                        self.assertLessEqual(interval['high_bits'],old[a]['high_bits'])
                    self.assertLessEqual(interval['low_bits'],interval['high_bits'])
                    for field,bound,step in (('lower_witness','low_bits',0),('upper_witness','high_bits',1)):
                        witness = interval[field]
                        if witness is None:
                            continue
                        if witness['key'][0]=='r42':
                            self.assertEqual(witness['key'][1:],old[a][field]['key'])
                            self.assertEqual(interval[bound],old[a][bound])
                        else:
                            args,target = native[tuple(witness['key'])]
                            self.assertEqual((witness['args'],witness['native_channel']),(args,target))
                            self.assertEqual(lower_bound(tuple(args),space,order,target+step)-step,interval[bound])

    def test_empty_intersection_is_retained_not_replaced_with_local_fit(self):
        old = {'146':{'low_bits':100,'high_bits':120,'lower_witness':None,'upper_witness':None}}
        added = {146:{'low_bits':130,'high_bits':150,'lower_witness':None,'upper_witness':None}}
        result = intersect(old,added)
        self.assertEqual((result['146']['low_bits'],result['146']['high_bits']),(130,120))
        self.assertEqual(old['146']['low_bits'],100)
