import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_factor_materialized import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r108'


class BitmapCacheFactorMaterializedTests(unittest.TestCase):
    def test_explicit_normalization_rejects_nonidentity_parent_cases(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'], 128)
        self.assertEqual(r['prior_native_exact'], 73728)
        for mode in (0,1):
            for name, exact in [('integer_copy',24576),('parent_cache',23553),('child_cache',22744)]:
                rows = [s for s in r['comparisons'] if s['mode'] == mode and s['comparison'] == name]
                self.assertEqual(sum(s['samples'] for s in rows), 24576)
                self.assertEqual(sum(s['exact'] for s in rows), exact)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
