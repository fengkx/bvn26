import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_wrapper_boundaries import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r189'

class NearestWrapperBoundariesTests(unittest.TestCase):
    def test_clear_passes_but_cache_and_filter_stay_rejected(self):
        r=analyze()
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(v['comparisons']['tint_before_coverage/clear']['exact'] for v in r['rows']),960000)
        self.assertEqual(sum(v['comparisons']['tint_before_coverage/cache']['exact'] for v in r['rows']),959994)
        self.assertEqual(sum(v['comparisons']['tint_before_coverage/authored']['exact'] for v in r['rows']),959990)
        self.assertFalse(r['cache_boundary_admitted'])
        self.assertFalse(r['complete_wrapper_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
