import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_sampling_r27 import analyze, events, origin_identities
from tools.probes.bitmap_sampling_candidate import coordinates, use_byte_weights

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r27'


class BitmapSamplingR27Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze()

    def test_independent_clipped_suites_are_exact_but_repeat_blocks_admission(self):
        scores = {r['suite']: r for r in self.report['scores']}
        for name, score in scores.items():
            if name in ('repeat', 'scalar-repeat'):
                self.assertLess(score['exact'], score['samples'])
            else:
                self.assertEqual(score['exact'], score['samples'], name)
        self.assertEqual(scores['row']['exact'], 6048)
        self.assertEqual(scores['independent_clipped_widths']['exact'], 24080)
        self.assertEqual(scores['repeat']['exact'], 511)
        self.assertEqual(scores['scalar-repeat']['exact'], 858)
        self.assertFalse(self.report['passed'])
        self.assertFalse(self.report['production_admitted'])

    def test_native_origin_and_width_controls(self):
        controls = self.report['quarter_origin_controls']
        self.assertEqual(len(controls), 108)
        self.assertEqual(sum(not c['exact'] for c in controls), 20)
        self.assertEqual(self.report['width_controls_exact'], 1344)
        self.assertEqual(self.report['boundary_single_vs_span_counts'], {0: [1200, 0], 1: [1200, 204]})
        self.assertEqual(self.report['outside_clip_observations_excluded'], 16)

    def test_current_sources_match_native_builds(self):
        for name in ('boundary', 'origin'):
            build = json.loads((EVIDENCE / name / 'build.json').read_text())
            self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                             build['source_sha256'])
            self.assertIn(build['run_id'], (EVIDENCE / name / 'native.log').read_text())

    def test_incomplete_or_wrong_origin_capture_is_rejected(self):
        text = (EVIDENCE / 'origin/native.log').read_text()
        for bad in (text+text, text.replace('|done|ok', '|done|failed'),
                    text.replace('-r27-', '-wrong-', 1),
                    text.replace('|origin|0,2.5,4,-8,', '|origin|0,3,4,-8,')):
            with self.assertRaises(ValueError):
                events(bad, 'bitmap-origin-sweep', origin_identities(), lambda _: 1, 'origin')

    def test_out_of_scope_geometry_is_not_silently_sampled(self):
        with self.assertRaises(ValueError):
            coordinates(-1, 0, 0, 0, 0)
        with self.assertRaises(ValueError):
            use_byte_weights(5, .75, 0, 0, 4, clip_left=0, clip_right=520,
                             source_width=1024, source_height=1024)
