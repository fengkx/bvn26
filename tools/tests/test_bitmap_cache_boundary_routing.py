import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_boundary_routing import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r106'


class BitmapCacheBoundaryRoutingTests(unittest.TestCase):
    def test_parent_cache_matches_explicit_materialization(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'], 128)
        self.assertEqual(sum(s['exact'] for s in r['explicit_parent']), 15360)
        expected = {(0,'child_parent'):14825,(0,'clear_child'):14570,(0,'clear_parent'):14985,
                    (1,'child_parent'):14932,(1,'clear_child'):14661,(1,'clear_parent'):14984,
                    ('moved','0'):14806,('moved','1'):14913,('moved','2'):14806}
        for key, exact in expected.items():
            rows = [s for s in r['comparisons'] if (s['route'],s['comparison']) == key]
            self.assertEqual(sum(s['samples'] for s in rows), 15360)
            self.assertEqual(sum(s['exact'] for s in rows), exact)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
