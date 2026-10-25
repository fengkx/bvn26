import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_component_coverage import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r187'

class NearestComponentCoverageTests(unittest.TestCase):
    def test_complete_original_leaf_and_boundary_negative(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r179/native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(v['scores']['clamp']['exact'] for v in r['rows']),1440000)
        self.assertEqual(sum(v['scores']['clear']['exact'] for v in r['rows']),1439991)
        self.assertFalse(r['complete_wrapper_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
