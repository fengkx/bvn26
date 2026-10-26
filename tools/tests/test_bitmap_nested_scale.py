import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_nested_scale import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r96'


class BitmapNestedScaleTests(unittest.TestCase):
    def test_outer_scale_and_signed_origins(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['scores']['direct']['composed_double']['exact'],83423)
        for name in ('scaled_inner_nearest_even','scaled_inner_nearest_away'):
            self.assertEqual(r['scores']['nested'][name]['exact'],83423)
            self.assertEqual(r['old_translation_regression'][name]['exact'],26538)
        self.assertEqual(r['scores']['nested']['separate_quarters_before_scale']['exact'],52769)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
