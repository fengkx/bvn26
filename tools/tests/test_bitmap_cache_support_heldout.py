import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_support_heldout import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r117'


class BitmapCacheSupportHeldoutTests(unittest.TestCase):
    def test_independent_support_rejects_simple_expansions(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(result,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(result['input_exact'],480)
        self.assertEqual(sum(v['exact'] for v in result['bounds']),464)
        self.assertEqual(len(result['bounds']),480)
        self.assertEqual(sum(v['exact'] for v in result['cache_interior']),29494)
        self.assertEqual(sum(v['samples'] for v in result['cache_interior']),29494)
        self.assertFalse(result['source_cache_initializer_admitted'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        provenance=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
