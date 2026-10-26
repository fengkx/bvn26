import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_materialized import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r105'


class BitmapCacheMaterializedTests(unittest.TestCase):
    def test_integer_copy_exact_but_implicit_cache_not_reproduced(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'], 128)
        expected = {0: (15360, 14825, 14985), 1: (15360, 14699, 14506)}
        for mode, counts in expected.items():
            for name, exact in zip(('placement', 'implicit_cache', 'uncached'), counts):
                rows = [s for s in r['results'] if s['mode'] == mode and s['comparison'] == name]
                self.assertEqual(sum(s['samples'] for s in rows), 15360)
                self.assertEqual(sum(s['exact'] for s in rows), exact)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
