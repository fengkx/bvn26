import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_weight_impulses import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r26'


class BitmapWeightImpulseTests(unittest.TestCase):
    def test_independent_corner_responses_isolate_scalar_fractions(self):
        report = analyze((EVIDENCE / 'weights/native.log').read_text())
        self.assertEqual((report['samples'], report['constant_channel_exact']), (2880, 2880))
        self.assertEqual(report['four_corner_groups'], 720)
        self.assertEqual([r['byte_fraction_solutions'] for r in report['isolated_scalar_controls']],
                         [[[128, 89]], [[128, 115]], [[64, 89]], [[64, 115]]])
        self.assertFalse(report['production_admitted'])

    def test_fixture_hash_and_malformed_capture(self):
        text = (EVIDENCE / 'weights/native.log').read_text()
        build = json.loads((EVIDENCE / 'weights/build.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                         build['source_sha256'])
        self.assertIn(build['run_id'], text)
        for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                    text.replace('-r26-', '-wrong-', 1),
                    text.replace('|weight|0,0,2.5,', '|weight|1,0,2.5,', 1)):
            with self.assertRaises(ValueError):
                analyze(bad)
