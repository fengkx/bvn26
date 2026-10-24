import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_repeat_coefficients import analyze, capture

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r29'


class BitmapRepeatCoefficientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze()

    def test_native_scores_and_admission_remain_strict(self):
        self.assertEqual([(r['exact'], r['samples']) for r in self.report['scores']],
                         [(1196, 1200), (960, 960), (126, 168), (168, 168),
                          (168, 168), (1008, 1008), (571, 1008)])
        self.assertFalse(self.report['passed'])
        self.assertFalse(self.report['production_admitted'])
        for row in self.report['clipped_regressions']:
            self.assertEqual(row['exact'], row['samples'], row['suite'])

    def test_independent_affine_constraints(self):
        for kind, count, field in [('coefficient', 300, 'normalized_inverse'),
                                   ('step', 240, 'normalized_fixed_step')]:
            constraints = self.report['affine_constraints'][kind]
            self.assertEqual(constraints['groups'], count)
            self.assertEqual(constraints['unresolved'], [])
            self.assertEqual(len(constraints['intervals']), 20)
            for row in constraints['intervals']:
                lo, hi = row['slope_open_interval']
                self.assertTrue(row['feasible'])
                self.assertLess(lo, row[field])
                self.assertLess(row[field], hi)

    def test_sources_match_captures_and_malformed_traces_fail(self):
        for folder, kind in [('coefficients', 'coefficient'), ('step', 'step'), ('negative', 'negative')]:
            build = json.loads((EVIDENCE / folder / 'build.json').read_text())
            self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                             build['source_sha256'])
            text = (EVIDENCE / folder / 'native.log').read_text()
            self.assertIn(build['run_id'], text)
            for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                        text.replace('-r29-', '-r28-', 1),
                        text.replace('|'+kind+'|', '|wrong|', 1)):
                with self.assertRaises(ValueError):
                    capture(bad, kind)
