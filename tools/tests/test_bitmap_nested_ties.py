import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_nested_ties import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r97'


class BitmapNestedTieTests(unittest.TestCase):
    def test_signed_ties_reject_other_common_rules(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['scores']['scaled_inner_nearest_even']['exact'],86749)
        self.assertEqual(r['scores']['scaled_inner_nearest_away']['exact'],75179)
        self.assertEqual(r['scores']['scaled_inner_nearest_up']['exact'],75756)
        self.assertEqual(r['direct']['exact'],86749)
        self.assertEqual(len(r['tie_cases']),180)
        self.assertEqual(r['old_scale']['scores']['scaled_inner_nearest_even']['exact'],83423)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
