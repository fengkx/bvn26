import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_affine_spans import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r159'

class NearestAffineSpanTests(unittest.TestCase):
    def test_clip_invariance_and_scalar_counterexamples(self):
        r=analyze(EVIDENCE/'native',ROOT/'evidence/importer-loud-fail/r158/native');f={k:v.pop('failures') for k,v in r['scores'].items()};f['full_row']=r['full_row_comparison'].pop('failures')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r['full_row_comparison']['exact'],23040)
        self.assertEqual(r['length_changed_overlaps'],[])
        self.assertEqual(r['scores']['fixed_inverse_center/length1']['exact'],495)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
