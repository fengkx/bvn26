import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_matrix_bits import analyze, number

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r104'


class BitmapCacheMatrixBitsTests(unittest.TestCase):
    def test_binary_intermediates_do_not_admit_roundtrip_model(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(result['input_exact'], 128)
        for name in {r['model'] for r in result['models']}:
            rows = [r for r in result['models'] if r['model'] == name]
            self.assertEqual(sum(r['samples'] for r in rows), 19980)
            self.assertEqual(sum(r['exact'] for r in rows), 19980 if name == 'uncached' else 16379)
        self.assertEqual(sum(not c['child_roundtrip_equal'] for c in result['cases']), 120)
        self.assertEqual(sum(not c['full_roundtrip_equal'] for c in result['cases']), 64)
        self.assertFalse(result['candidate_admitted'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
