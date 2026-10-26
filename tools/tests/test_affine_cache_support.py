import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_cache_support import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r190'

class AffineCacheSupportTests(unittest.TestCase):
    def test_independent_cache_alpha_support(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['scores']['separate']['exact'],66)
        self.assertEqual(r['unchanged_uncached'],{'exact':161350,'samples':161350})
        self.assertTrue(all(v['opaque_alpha_rectangle'] for v in r['rows']))
        self.assertEqual(sum(v['solid_rectangle'] for v in r['rows']),12)
        self.assertFalse(r['cache_allocation_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
