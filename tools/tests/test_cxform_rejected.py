import gzip
import json
import unittest

from tools.probes.analyze_cxform_amplified import read_samples
from tools.probes.analyze_cxform_intervals import lower_bound
from tools.probes.analyze_cxform_rejected import (
    EVIDENCE, measurements, prior, read_native, sequence,
)

ROOT = EVIDENCE/'r44'


class CxformRejectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.clipping = read_native(ROOT/'native')
        cls.report = json.loads(gzip.decompress((ROOT/'analysis.json.gz').read_bytes()))

    def test_fixed_grid_retains_old_alphas_and_records_all_clipping(self):
        self.assertEqual(len(self.rows),132192)
        self.assertEqual(len(self.clipping),864)
        self.assertEqual({v['alpha'] for v in self.clipping},{7})
        inputs = {(p[3],x,m,d,op):(p,n) for _,x,p,n,m,d,op in self.rows}
        previous = read_samples(EVIDENCE/'r43/native')
        self.assertEqual(len(previous),10368)
        for _,x,p,n,m,d,op in previous:
            self.assertEqual(inputs[p[3],x,m,d,op],(p,n))
        self.assertTrue({14,135,146,197,206,244}.issubset({p[3] for _,_,p,_,_,_,_ in self.rows}))

    def test_every_old_bound_is_retained_and_new_witnesses_are_native(self):
        old = prior()
        needed = {}
        for key,model in self.report['models'].items():
            space,order = key.split('/')
            for group in ('green_intervals','combined_intervals'):
                if group not in model:
                    continue
                for a,bounds in model[group].items():
                    previous = old['models'][key][group].get(a)
                    if previous:
                        self.assertGreaterEqual(bounds['low_bits'],previous['low_bits'])
                        self.assertLessEqual(bounds['high_bits'],previous['high_bits'])
                    for field,bound,step in (('lower_witness','low_bits',0),('upper_witness','high_bits',1)):
                        w = bounds[field]
                        if not w:
                            continue
                        if w['key'][0]=='r43':
                            self.assertEqual(w['key'][1:],previous[field]['key'])
                            self.assertEqual(bounds[bound],previous[bound])
                        else:
                            self.assertEqual(w['key'][0],'rejected')
                            self.assertEqual(lower_bound(tuple(w['args']),space,order,w['native_channel']+step)-step,bounds[bound])
                            needed[tuple(w['key'])] = (w['args'],w['native_channel'])
        actual = {}
        for i,x,p,n,m,d,op in self.rows:
            for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
                key = ('rejected',i,x,ch)
                if key in needed:
                    actual[key] = ([p[ch],p[3],mul,offset,op],n[ch])
        self.assertEqual(actual,needed)

    def test_direct_sequences_preserve_old_controls_and_reject_exactly(self):
        measured = measurements(ROOT)
        for key,model in self.report['direct_sequences'].items():
            mode,order = key.split('/')
            self.assertEqual(model['old']['channels'],661248)
            self.assertEqual(model['new']['channels'],396576)
            for dataset in model.values():
                self.assertEqual(dataset['channels']-dataset['exact'],sum(v['occurrences'] for v in dataset['failures']))
                for failure in dataset['failures']:
                    actual = sequence(failure['args'],measured[mode],order)
                    self.assertEqual(actual,failure['actual'])
                    self.assertNotEqual(actual,failure['native'])
            self.assertLess(model['old']['exact'],model['old']['channels'])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(self.report[flag])

    def test_no_factorized_common_construction_passes_all_intervals(self):
        for model in self.report['models'].values():
            if 'membership' in model:
                self.assertEqual(model['total_constraints'],1057824)
                self.assertTrue(all(v['inside']<v['alphas'] for v in model['membership'].values()))
