import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_yulong_rotated_source import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r138'


class YulongRotatedSourceTests(unittest.TestCase):
    def test_original_source_and_mask_reproduce_all_native_boundaries(self):
        r=analyze()
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        for v in r['rows']:
            self.assertEqual(v['input']['exact'],240000)
            self.assertEqual(v['glow']['exact'],240000)
            self.assertEqual(v['fringe_exact'],74)
        self.assertEqual(sum(v['exact'] for v in r['pinned']),480000)
        self.assertFalse(r['fractional_coverage_independently_verified'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_evidence_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
