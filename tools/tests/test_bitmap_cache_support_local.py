import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_support_local import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r118'


class BitmapCacheSupportLocalTests(unittest.TestCase):
    def test_independent_support_rejects_simple_expansions(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(result,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(sum(v['exact'] for v in result['consumption']),960)
        self.assertEqual(sum(v['exact'] for v in result['bounds']),480)
        self.assertEqual(result['unchanged_row_pixels'],768000)
        self.assertFalse(result['source_cache_initializer_admitted'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        provenance=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
