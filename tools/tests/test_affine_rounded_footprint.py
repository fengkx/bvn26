import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_rounded_footprint import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r176'

class AffineRoundedFootprintTests(unittest.TestCase):
    def test_all_controls_exact_without_claiming_unobserved_ties(self):
        r=analyze(ROOT/'evidence/importer-loud-fail')
        for v in r['scores'].values():self.assertEqual(v.pop('failures'),[])
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(v['exact'] for k,v in r['scores'].items() if k.endswith('/ties_even')),66882)
        self.assertEqual(r['offset_tie_samples'],0)
        self.assertFalse(r['gpu_advance_allowed'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
