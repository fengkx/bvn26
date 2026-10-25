import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_reveal_buffer import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r115'


class BitmapCacheRevealBufferTests(unittest.TestCase):
    def test_measured_filtered_origin_explains_bounded_input(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(sum(s['exact'] for s in r['identity_comparisons']),102400)
        self.assertEqual(sum(s['exact'] for s in r['measured_origin_checks']),2904)
        self.assertEqual([v['rectangle'][0] for v in r['revealed_rectangles']],[123,124,127,128,128,129,130,131])
        self.assertTrue(all(v['rectangle'][1]==4 and v['rectangle'][3]==13 for v in r['revealed_rectangles']))
        self.assertFalse(r['cache_only_allocation_equivalence_proven'])
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
