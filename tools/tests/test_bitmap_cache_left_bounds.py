import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_left_bounds import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r109'


class BitmapCacheLeftBoundsTests(unittest.TestCase):
    def test_bounds_shift_changes_cached_but_not_uncached_prefix(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'], 128)
        for mode in (0,1):
            for kind in ('clear','cached'):
                rows = [s for s in r['comparisons'] if s['mode'] == mode and s['kind'] == kind]
                self.assertEqual(sum(s['samples'] for s in rows), 7524)
                self.assertEqual(sum(s['exact'] for s in rows), 7524 if kind == 'clear' else 7202)
                self.assertEqual(sum(bool(s['failures']) for s in rows), 0 if kind == 'clear' else 12)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
