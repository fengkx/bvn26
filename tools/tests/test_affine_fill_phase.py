import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_fill_phase import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r166'

class AffineFillPhaseTests(unittest.TestCase):
    def test_signed_consumption_and_retained_initializer_failures(self):
        r=analyze(EVIDENCE/'native');f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r['scores']['phase0/twip_trunc']['exact'],774)
        self.assertEqual(r['scores']['phase0/declared']['exact'],756)
        self.assertFalse(any(v['declared_linear_feasible'] for v in r['groups']))
        self.assertTrue(all(v['consumed_linear_feasible'] for v in r['groups']))
        self.assertLess(r['scores']['phase1/twip_trunc']['exact'],774)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
