import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_short_spans import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r25'


class BitmapShortSpanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (EVIDENCE / 'short/native.log').read_text()
        cls.report = analyze(cls.text)

    def test_current_fixture_is_native_capture_source(self):
        build = json.loads((EVIDENCE / 'short/build.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                         build['source_sha256'])
        self.assertIn(build['run_id'], self.text)

    def test_native_length_transition_is_not_a_fitted_formula_selector(self):
        controls = self.report['first_pixel_controls']
        changed = [c for c in controls if c['changed_lengths']]
        self.assertEqual(len(controls), 84)
        self.assertEqual(len(changed), 27)
        for control in changed:
            self.assertEqual(control['changed_lengths'], [4, 5, 6, 7, 8])
            self.assertEqual(len({tuple(rgb) for rgb in control['first_rgb_by_length'][3:]}), 1)
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['passed'])
        self.assertEqual(len(self.report['single_pixel_mode_differences']), 30)

    def test_geometry_fringe_is_retained_and_not_scored_as_pure_sampling(self):
        self.assertEqual(self.report['samples'], 4248)
        self.assertEqual(self.report['geometry_fringe_samples'], 48)
        self.assertEqual(sum(not r['geometry_interior'] for r in self.report['rows']), 48)
        scores = [s for s in self.report['scores'] if s['model'] == 'quantized_inverse']
        self.assertEqual([(s['exact'], s['samples']) for s in scores],
                         [(598, 612), (568, 612), (1194, 1488), (764, 1488)])

    def test_invalid_capture_cannot_produce_parity_claim(self):
        for text in (self.text+self.text, self.text.replace('|done|ok', '|done|failed'),
                     self.text.replace('-r25-', '-wrong-', 1),
                     self.text.replace('|short|0,0,2.5,-1,0.25,3,1,', '|short|0,0,3,-1,0.25,3,1,')):
            with self.assertRaises(ValueError):
                analyze(text)
