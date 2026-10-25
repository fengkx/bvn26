import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_width import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r103'


class BitmapCacheWidthTests(unittest.TestCase):
    def test_width_and_span_do_not_explain_prefix_failures(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'],3056)
        self.assertEqual(sum(v['exact'] for v in r['models'] if v['kind']=='clear'),68544)
        self.assertEqual(sum(v['exact'] for v in r['models'] if v['kind']=='cached'),53556)
        for name in ('width_prefix','mode_prefix'):
            self.assertTrue(all(not v[k]['failures'] for v in r[name] for k in ('clear','cached')))
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
