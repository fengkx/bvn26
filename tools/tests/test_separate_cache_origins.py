import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_separate_cache_origins import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r119'


class SeparateCacheOriginsTests(unittest.TestCase):
    def test_common_origin_clears_all_retained_cache_families(self):
        result=analyze()
        self.assertEqual(result,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(sum(v['samples'] for v in result['comparisons'].values()),436116)
        for score in result['comparisons'].values():
            self.assertEqual(score['exact'],score['samples'])
            self.assertEqual(score['max_channel_delta'],0)
            self.assertFalse(score['failures'])
        self.assertFalse(result['source_cache_initializer_admitted'])
        self.assertFalse(result['gpu_advance_allowed'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_native_references_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
