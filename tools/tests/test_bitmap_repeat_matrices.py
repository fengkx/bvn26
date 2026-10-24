import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_repeat_matrices import analyze, capture, signed_byte_coordinate

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r28'


class BitmapRepeatMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze()

    def test_signed_binary_controls_and_remaining_failures(self):
        self.assertEqual(self.report['binary_control_summary'],
                         {'samples': 280, 'floor_exact': 160, 'signed_exact': 280})
        self.assertEqual([(s['exact'], s['samples']) for s in self.report['repeat_scores']],
                         [(862, 1008), (513, 1008)])
        self.assertEqual(len(self.report['failures']), 641)
        self.assertFalse(self.report['passed'])
        self.assertFalse(self.report['production_admitted'])

    def test_clipped_regressions_stay_exact(self):
        for score in self.report['clipped_regressions']:
            self.assertEqual(score['exact'], score['samples'], score['suite'])

    def test_period_controls_and_source_hash(self):
        self.assertEqual(self.report['native_samples'], 2940)
        self.assertEqual(self.report['constant_channel_exact'], 2940)
        self.assertEqual([r['different'] for r in self.report['period_control_summary']], [192, 136, 164])
        build = json.loads((EVIDENCE / 'matrices/build.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                         build['source_sha256'])
        self.assertIn(build['run_id'], (EVIDENCE / 'matrices/native.log').read_text())

    def test_incomplete_mixed_and_wrong_identity_captures_fail(self):
        text = (EVIDENCE / 'matrices/native.log').read_text()
        for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                    text.replace('-r28-', '-r27-', 1),
                    text.replace('|matrix|0,1.01,0,-128,-0.125,', '|matrix|0,1.02,0,-128,-0.125,')):
            with self.assertRaises(ValueError):
                capture(bad)
