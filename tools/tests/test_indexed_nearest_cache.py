import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_nearest_cache import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r192'

class IndexedNearestCacheTests(unittest.TestCase):
    def test_storage_matches_but_cache_remains_distinct(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        for row in r['rows']:
            for cache in range(2):self.assertEqual(row['comparisons'][f'indexed_vs_as/cache{cache}']['exact'],240000)
            for case in (0,2):self.assertEqual(row['comparisons'][f'uncached_model/case{case}']['exact'],240000)
        self.assertEqual([240000-v['comparisons']['cache_vs_uncached/storage0']['exact'] for v in r['rows']],[48,14,22,6])
        self.assertFalse(r['cache_initializer_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
