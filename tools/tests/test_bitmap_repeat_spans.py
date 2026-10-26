import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_repeat_spans import analyze, capture
from tools.probes.analyze_bitmap_repeat_rounding import coordinate
from tools.probes.bitmap_repeat_span_candidate import span_modes, sample

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r31'


class BitmapRepeatSpanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze()

    def test_every_continuous_and_scalar_regression_is_exact(self):
        self.assertEqual([(s['exact'], s['samples']) for s in self.report['scores']],
                         [(11256, 11256), (30744, 30744), (5376, 5376), (1008, 1008), (2016, 2016)])
        for row in self.report['regressions']:
            self.assertEqual(row['exact'], row['samples'], row['suite'])
        self.assertEqual(self.report['failures'], [])
        self.assertTrue(self.report['arithmetic_passed'])
        self.assertFalse(self.report['production_admitted'])

    def test_native_interval_constraints_keep_ambiguity_and_scalar_coordinates(self):
        intervals = self.report['coordinate_intervals']
        self.assertEqual(intervals['groups'], 1876)
        self.assertTrue(intervals['all_explained_without_coordinate_change'])
        for row in intervals['rows']:
            self.assertTrue(row['compatible_byte_coordinates_modulo_2'])
            self.assertTrue(row['fixed_scalar_compatible_modes'])
        self.assertTrue(any(len(row['compatible_byte_coordinates_modulo_2']) > 1
                            for row in intervals['rows']))

    def test_geometric_partition_explains_native_length_changes(self):
        y = coordinate(8, 0, 4, 2)
        self.assertEqual(span_modes(5, 0, 4, 4, 2, y, 2)[1], ['vertical']*4)
        self.assertEqual(span_modes(5, 0, 4, 8, 2, y, 2)[1], ['horizontal']*8)
        self.assertEqual(span_modes(3, 15, 4, 5, 2, y, 2)[1], ['byte']+['horizontal']*4)
        _, _, runs = span_modes(5, 0, 3, 513, 2, y, 2)
        self.assertIn(259, [r['end'] for r in runs])
        self.assertIn(515, [r['end'] for r in runs])
        with self.assertRaises(ValueError):
            sample(0, 0, lambda x, y: [0, 0, 0], 'unknown')

    def test_source_hashes_and_capture_validation(self):
        for folder, kind in [('intervals', 'interval'), ('chunks', 'chunk')]:
            build = json.loads((EVIDENCE / folder / 'build.json').read_text())
            self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(), build['source_sha256'])
            text = (EVIDENCE / folder / 'native.log').read_text()
            self.assertIn(build['run_id'], text)
            for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                        text.replace('-r31-', '-r30-', 1), text.replace('|'+kind+'|', '|wrong|', 1)):
                with self.assertRaises(ValueError):
                    capture(bad, kind)
