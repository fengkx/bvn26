import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_crossing import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r102'


class BitmapCacheCrossingTests(unittest.TestCase):
    def test_new_origins_reject_all_current_cache_constructions(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['models']['global_uncached']['exact'],240900)
        for name,count in [('cache_consumed_bounds',210078),('cache_authored_bounds',210084),('cache_node_plus_outer_bounds',210086)]:
            self.assertEqual(r['models'][name]['exact'],count)
            self.assertEqual(r['breakdown'][name]['max_channel_delta'],10)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
