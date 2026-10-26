import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_scale_factors import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r107'


class BitmapCacheScaleFactorTests(unittest.TestCase):
    def test_child_cache_tracks_concatenated_not_local_scale(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'], 128)
        for scale, expected_parent in ((7,11537),(8,11800)):
            for boundary in (0,1,2):
                rows = [s for s in r['comparisons'] if s['scale'] == scale and s['boundary'] == boundary]
                self.assertEqual(sum(s['samples'] for s in rows), 12288)
                self.assertEqual(sum(s['exact'] for s in rows), expected_parent if boundary == 2 else 12288)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
