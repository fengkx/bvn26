import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.probes.analyze_cxform_adjacent import EVIDENCE, SITES, previous_report, read_native
from tools.probes.analyze_cxform_intervals import lower_bound
from tools.probes.analyze_cxform_rejected import measurements, sequence

ROOT = EVIDENCE/'r45'


class CxformAdjacentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.targets = read_native(ROOT/'native')
        cls.report = json.loads(gzip.decompress((ROOT/'analysis.json.gz').read_bytes()))

    def test_independent_grid_retains_centered_rows_and_clipping(self):
        self.assertEqual((len(self.rows),len(self.targets)),(14688,459))
        self.assertEqual(self.report['centered_exact'],96)
        self.assertEqual(sum(v['clipped'] for v in self.targets),8)
        for site,(a,_,_,_,_) in enumerate(SITES):
            pairs = {(v['alpha']-a,v['delta_green']) for v in self.targets if v['site']==site}
            self.assertEqual(pairs,{(da,dg) for da in range(-4,5) for dg in range(-8,9)})
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(self.report[flag])

    def test_all_old_bounds_and_new_native_witnesses_are_retained(self):
        old = previous_report()
        native = {}
        for i,x,p,n,m,d,op in self.rows:
            for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
                native[('adjacent',i,x,ch)] = ([p[ch],p[3],mul,offset,op],n[ch])
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
                        if w['key'][0]=='r44':
                            self.assertEqual(w['key'][1:],previous[field]['key'])
                            self.assertEqual(bounds[bound],previous[bound])
                        else:
                            self.assertEqual((w['args'],w['native_channel']),native[tuple(w['key'])])
                            self.assertEqual(lower_bound(tuple(w['args']),space,order,w['native_channel']+step)-step,bounds[bound])
                fits = model['membership_'+group]
                self.assertTrue(all(v['inside']<v['alphas'] for v in fits.values()))

    def test_fixed_sequences_fail_globally_and_at_the_actual_target(self):
        measured = measurements(EVIDENCE/'r44')
        for mode,expected in (('divide',431),('multiply_rounded',418),('multiply_estimated',410)):
            for order in ('alpha_first','opacity_first','joint'):
                key = mode+'/'+order
                actual = 0
                for v in self.targets:
                    _,_,m,d,op = SITES[v['site']]
                    actual += sequence((v['source'][1],v['alpha'],m,d,op),measured[mode],order)==v['native'][1]
                self.assertEqual(actual,expected)
                self.assertEqual(self.report['target_sequences'][key]['exact'],actual)
                report = self.report['direct_sequences'][key]
                self.assertEqual(report['old']['channels'],1057824)
                self.assertEqual(report['new']['channels'],44064)
                for group in report.values():
                    self.assertLess(group['exact'],group['channels'])
                    self.assertEqual(group['channels']-group['exact'],sum(v['occurrences'] for v in group['failures']))

    def test_changed_input_is_rejected_even_with_updated_trace_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy(ROOT/'native/build.json',root/'build.json')
            lines = gzip.decompress((ROOT/'native/native.log.gz').read_bytes()).decode().splitlines()
            for i,line in enumerate(lines):
                fields = line.split('|')
                if len(fields)==8 and fields[6]=='row':
                    values = fields[7].split(',')
                    values[8] = str(int(values[8])^256)
                    fields[7] = ','.join(values)
                    lines[i] = '|'.join(fields)
                    break
            raw = ('\n'.join(lines)+'\n').encode()
            packed = gzip.compress(raw,mtime=0)
            (root/'native.log.gz').write_bytes(packed)
            (root/'trace-sha256.json').write_text(json.dumps({'native.log':hashlib.sha256(raw).hexdigest(),
                                                            'native.log.gz':hashlib.sha256(packed).hexdigest()}))
            with self.assertRaisesRegex(ValueError,'source readback changed'):
                read_native(root)
