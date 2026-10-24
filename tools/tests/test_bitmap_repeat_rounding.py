import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_repeat_rounding import analyze, capture, coordinate

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r30'


class BitmapRepeatRoundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze()
        cls.scores = {r['suite']: r for r in cls.report['scores']}

    def test_scalar_native_suites_are_exact_without_clipped_regressions(self):
        expected = {'r29_coefficient': 1200, 'r29_step': 960, 'scalar-repeat': 1008,
                    'r29_negative': 168, 'r28_binary_routes': 280,
                    'rounding_even_half_and_period': 288, 'half_even_half_and_period': 4032,
                    'spans_scalar_lengths_1_3': 768}
        for name, total in expected.items():
            self.assertEqual((self.scores[name]['exact'], self.scores[name]['samples']), (total, total), name)
        for row in self.report['clipped_regressions']:
            self.assertEqual(row['exact'], row['samples'], row['suite'])

    def test_native_controls_discriminate_rounding_and_period(self):
        self.assertEqual(self.scores['rounding_r29']['exact'], 276)
        self.assertEqual(self.scores['half_r29']['exact'], 3972)
        self.assertEqual(self.scores['half_even_half_only']['exact'], 4024)
        # These coordinate bytes are constrained by independent native impulses.
        self.assertEqual(coordinate(3, -15, 4, 4), 1535/256)
        self.assertEqual(coordinate(5, -7, 5, 2), 2)
        self.assertEqual(coordinate(5, -7, 5, 2, denominator_minus_one=False), 511/256)

    def test_continuous_counterexamples_keep_admission_closed(self):
        for name, exact, total in [('repeat', 571, 1008), ('spans_byte', 3469, 5376),
                                    ('spans_separable', 3981, 5376), ('spans_groups4', 4789, 5376)]:
            self.assertEqual((self.scores[name]['exact'], self.scores[name]['samples']), (exact, total))
        self.assertEqual([r['different'] for r in self.report['span_overlap_controls']],
                         [0, 96, 270, 18, 26, 69, 19, 135, 279])
        self.assertEqual(sum(r['suite'] == 'repeat' for r in self.report['failures']), 437)
        self.assertEqual(sum(r['suite'] == 'spans_groups4' for r in self.report['failures']), 587)
        self.assertFalse(self.report['passed'])
        self.assertFalse(self.report['production_admitted'])

    def test_trace_identity_completion_and_source_hashes(self):
        for folder, kind in [('rounding', 'rounding'), ('half', 'half'), ('spans', 'span')]:
            build = json.loads((EVIDENCE / folder / 'build.json').read_text())
            self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                             build['source_sha256'])
            text = (EVIDENCE / folder / 'native.log').read_text()
            self.assertIn(build['run_id'], text)
            for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                        text.replace('-r30-', '-r29-', 1), text.replace('|'+kind+'|', '|wrong|', 1)):
                with self.assertRaises(ValueError):
                    capture(bad, kind)
