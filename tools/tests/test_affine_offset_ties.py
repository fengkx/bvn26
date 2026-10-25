import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_offset_ties import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r177'

class AffineOffsetTiesTests(unittest.TestCase):
    def test_shared_ties_even_retains_signed_controls(self):
        r=analyze(EVIDENCE/'native');f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['offset_tie_samples'],1080)
        self.assertEqual(sum(v['exact'] for k,v in r['scores'].items() if k.endswith('/ties_even')),1440)
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
