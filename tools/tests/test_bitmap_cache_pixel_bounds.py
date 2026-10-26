import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_pixel_bounds import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r114'


class BitmapCachePixelBoundsTests(unittest.TestCase):
    def test_public_bounds_do_not_admit_hidden_allocation(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['public_bounds_invariant'],64)
        for kind in ('clear','cached'):
            rows=[s for s in r['comparisons'] if s['kind']==kind]
            self.assertEqual(sum(s['samples'] for s in rows),6400)
            self.assertEqual(sum(s['exact'] for s in rows),6400)
        rows=[s for s in r['comparisons'] if s['kind']=='bounds_translation']
        self.assertEqual(sum(s['exact'] for s in rows),7)
        self.assertFalse(r['hidden_cache_allocation_verified'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
