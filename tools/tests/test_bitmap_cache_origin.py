import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_origin import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r101'


class BitmapCacheOriginTests(unittest.TestCase):
    def test_independent_cache_origin_controls(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        for name in ('global_uncached','cache_consumed_bounds','cache_authored_bounds','cache_node_plus_outer_bounds'):
            self.assertEqual(r['models'][name]['exact'],37842)
        self.assertEqual(r['models']['local_bounds_after_consumption']['exact'],25266)
        self.assertEqual(r['placement']['cached']['floor']['exact_rows'],224)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
