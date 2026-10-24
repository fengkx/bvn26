import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.probes.analyze_cxform_identity import (
    ROOT, read_identity, read_previous, read_stages, read_zero, stage_transform,
)
from tools.probes.analyze_cxform_intervals import lower_bound

EVIDENCE = ROOT/'evidence/importer-loud-fail/r42'


class CxformIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes()))
        cls.identity = read_identity(EVIDENCE/'native')
        cls.stages = read_stages(EVIDENCE/'stages')
        cls.zero = read_zero(EVIDENCE/'zero')

    def test_channel_identity_cannot_bypass_nonidentity_enclosing_transform(self):
        self.assertEqual(len(self.identity),13248)
        rows = [v for v in self.identity if v[4]==256 and v[6]==100]
        self.assertEqual(len(rows),1472)
        self.assertTrue(all(n[1]==p[1]-1 for i,x,p,n,m,d,op in rows))
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(self.report[flag])
        for group in self.report['combined_intersections'].values():
            self.assertFalse(group['empty_alphas'])
            self.assertTrue(all(v['inside']<v['alphas'] for v in group['measurements'].values()))

    def test_materialized_boundary_is_not_elided(self):
        self.assertEqual(len(self.stages),47520)
        rows = {stage:(p,n) for i,stage,x,p,n,m,d,op in self.stages if i==95 and x==26}
        self.assertEqual(rows[0][0],[62,108,127,135])
        self.assertEqual(rows[0][1][1],107)
        self.assertEqual(rows[1][1],rows[3][0])
        self.assertEqual(rows[3][1][1],106)
        report = self.report['materialization']['multiplier_then_offset']
        self.assertEqual((report['same_rgba_as_one_draw'],report['samples']),(3728,9504))

    def test_zero_green_offset_has_no_reciprocal_degree_of_freedom(self):
        self.assertEqual(len(self.zero),3840)
        self.assertTrue(all(p[1]==0 for i,x,p,n,m,d,op in self.zero))
        self.assertEqual(self.report['zero_offset']['255']['exact'],3840)
        self.assertEqual(self.report['zero_offset']['256']['exact'],2976)
        self.assertTrue(all(n[1]==255 for i,x,p,n,m,d,op in self.zero
                            if p[3]==255 and d==255 and op==100))

    def test_intersection_witnesses_are_native_and_prior_constraints_are_retained(self):
        previous = read_previous()
        needed = {}
        for space,group in self.report['combined_intersections'].items():
            for a,interval in group['intervals'].items():
                old = previous['combined'][space]['intervals'][a]
                self.assertGreaterEqual(interval['low_bits'],old['low_bits'])
                self.assertLessEqual(interval['high_bits'],old['high_bits'])
                for field,bound,step in (('lower_witness','low_bits',0),('upper_witness','high_bits',1)):
                    witness = interval[field]
                    if witness is None:
                        continue
                    if witness['key'][0]=='r41':
                        self.assertEqual(witness['key'][1:],old[field]['key'])
                        self.assertEqual(witness['args'],old[field]['args'])
                        self.assertEqual(interval[bound],old[bound])
                    else:
                        needed[tuple(witness['key'])] = (witness['args'],witness['native_channel'])
                        endpoint = lower_bound(tuple(witness['args']),space,'alpha_first',witness['native_channel']+step)-step
                        self.assertEqual(endpoint,interval[bound])
        actual = {}
        for group,rows in (('identity',self.identity),('zero',self.zero)):
            for i,x,p,n,m,d,op in rows:
                for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
                    key = (group,i,x,ch)
                    if key in needed:
                        actual[key] = ([p[ch],p[3],mul,offset,op],n[ch])
        for i,stage,x,p,n,m,d,op in self.stages:
            mul,offset,actual_op = stage_transform(stage,m,d,op)
            for ch in range(3):
                key = ('stages',i,stage,x,ch)
                if key in needed:
                    actual[key] = ([p[ch],p[3],mul[ch],offset[ch],actual_op],n[ch])
        self.assertEqual(actual,needed)

    def test_changed_materialized_input_fails_even_with_consistent_trace_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            shutil.copy(EVIDENCE/'stages/build.json',path/'build.json')
            lines = gzip.decompress((EVIDENCE/'stages/native.log.gz').read_bytes()).decode().splitlines()
            for i,line in enumerate(lines):
                fields = line.split('|')
                if len(fields)!=8 or fields[6]!='row':
                    continue
                values = fields[7].split(',')
                if values[5]=='3':
                    values[7] = str(int(values[7])^256)
                    fields[7] = ','.join(values)
                    lines[i] = '|'.join(fields)
                    break
            raw = ('\n'.join(lines)+'\n').encode()
            packed = gzip.compress(raw,mtime=0)
            (path/'native.log.gz').write_bytes(packed)
            (path/'trace-sha256.json').write_text(json.dumps({
                'native.log':hashlib.sha256(raw).hexdigest(),
                'native.log.gz':hashlib.sha256(packed).hexdigest()}))
            with self.assertRaisesRegex(ValueError,'Materialized input'):
                read_stages(path)
