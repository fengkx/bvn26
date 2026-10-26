import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_scan_coverage import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r182'

class AffineScanCoverageTests(unittest.TestCase):
    def test_best_global_scan_construction_still_rejects(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r181/native');f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['scores']['quarter_half_up/scan_half_up']['exact'],161094)
        self.assertFalse(r['coverage_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
