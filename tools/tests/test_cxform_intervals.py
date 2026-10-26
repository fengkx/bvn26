import gzip
import json
from pathlib import Path
import tempfile
import unittest

from tools.probes.analyze_cxform_alpha import alpha_samples
from tools.probes.analyze_cxform_intervals import (
    ROOT, MAX_FINITE, channel, coefficient_measurements, float_bits, lower_bound,
    native_samples,
)

EVIDENCE = ROOT/'evidence/importer-loud-fail/r41'


class CxformIntervalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(gzip.decompress((EVIDENCE/'intervals.json.gz').read_bytes()))
        cls.native = native_samples(EVIDENCE/'native')

    def test_interval_witnesses_are_native_and_endpoints_are_exact(self):
        required = set()
        for group in self.report['combined'].values():
            for interval in group['intervals'].values():
                for field in ('lower_witness','upper_witness'):
                    witness = interval[field]
                    if witness:
                        required.add(tuple(witness['key']))
        actual = {}
        for i,x,p,n,m,d,op in self.native:
            for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
                key = ('native',i,x,ch)
                if key in required:
                    actual[key] = ([p[ch],p[3],mul,offset,op],n[ch])
        for name,ops in (('alpha',(25,50,100)),('opacity',(1,33,67,99))):
            for key,p,n,op in alpha_samples(ROOT/'evidence/importer-loud-fail/r40'/name,ops):
                for ch,m,d in ((0,128,8),(1,192,0),(2,256,-4)):
                    location = (name,*key,ch)
                    if location in required:
                        actual[location] = ([p[ch],p[3],m,d,op],n[ch])
        self.assertEqual(set(actual),required)
        for space,group in self.report['combined'].items():
            for interval in group['intervals'].values():
                self.assertLessEqual(interval['low_bits'],interval['high_bits'])
                for field,bound,step in (('lower_witness','low_bits',0),('upper_witness','high_bits',1)):
                    witness = interval[field]
                    if witness is None:
                        self.assertEqual(interval[bound],0 if step==0 else MAX_FINITE)
                        continue
                    args,target = actual[tuple(witness['key'])]
                    self.assertEqual((args,target),(witness['args'],witness['native_channel']))
                    endpoint = lower_bound(tuple(args),space,'alpha_first',target+step)-step
                    self.assertEqual(endpoint,interval[bound])

    def test_no_common_measured_construction_is_admitted(self):
        measured = coefficient_measurements(EVIDENCE)
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(self.report[flag])
        self.assertEqual(len(self.native),88320)
        self.assertEqual(self.report['green']['unit/alpha_first']['exact'],88087)
        for name in measured[1]:
            bounds = self.report['combined']['unit']['intervals']
            inside = sum(v['low_bits']<=float_bits(measured[int(a)][name])<=v['high_bits']
                         for a,v in bounds.items())
            self.assertEqual(inside,self.report['combined']['unit']['measurements'][name]['inside'])
            self.assertLess(inside,255)
        prior = self.report['old_regressions']['prior_regressions']
        for name,count in (('rows',25920),('scalar',3072),('spans',8652),('varied',8652)):
            self.assertEqual(prior[name]['exact'],count)

    def test_nonzero_offset_distinguishes_tested_orders_without_selecting_per_pixel(self):
        reciprocal = coefficient_measurements(EVIDENCE)[87]['estimate_inverse']
        args = (64,87,193,-1,67)
        self.assertEqual(channel(args,reciprocal,'unit','alpha_first'),31)
        self.assertEqual(channel(args,reciprocal,'unit','opacity_first'),32)
        sample = next(row for row in self.native if row[0:2]==(1525,15))
        self.assertEqual(sample[3][1],31)
        self.assertFalse(self.report['candidate_admitted'])

    def test_incomplete_measurements_cannot_supply_a_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'reciprocal.txt').write_text('1 3f800000\n')
            with self.assertRaisesRegex(ValueError,'Incomplete'):
                coefficient_measurements(path)
