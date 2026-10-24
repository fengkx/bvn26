import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.probes import analyze_bitmap_inverse as inverse
from tools.probes import analyze_bitmap_phase as phase
from tools.probes.analyze_bitmap_axis_ramps import analyze, split_coordinates

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail'


class BitmapAxisRampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (EVIDENCE / 'r26/axis/native.log').read_text()
        cls.report = analyze(cls.text)

    def test_capture_matches_current_fixture(self):
        build = json.loads((EVIDENCE / 'r26/axis/build.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest(),
                         build['source_sha256'])
        self.assertIn(build['run_id'], self.text)

    def test_axis_isolation_and_short_overlap_controls(self):
        self.assertEqual(self.report['samples'], 8064)
        self.assertEqual(self.report['constant_channel_exact'], 8064)
        controls = self.report['scalar_overlap_controls']
        self.assertEqual(len(controls), 336)
        self.assertTrue(all(c['exact'] for c in controls))
        self.assertEqual(self.report['single_coordinate_comparisons'], 3024)
        self.assertEqual(len(self.report['context_differences']), 825)
        self.assertFalse(self.report['passed'])
        self.assertFalse(self.report['production_admitted'])

    def test_fifth_pixel_can_change_in_both_repeat_textures(self):
        differences = [r for r in self.report['context_differences']
                       if r['identity'][-1] == 5 and r['offset'] == 4]
        self.assertEqual(len(differences), 8)
        self.assertEqual({r['identity'][0] for r in differences}, {1, 3})
        self.assertTrue(any(r['single_rgb'][1] != r['span_rgb'][1] for r in differences))

    def test_local_scalar_improvement_is_rejected_by_independent_native_suites(self):
        def coords(scale, p, x, y, extended=True):
            tx = math.trunc(p/256*4)/4
            ty = math.trunc(-p/512*4)/4 if extended else 0
            return split_coordinates(scale, tx, ty, x, y)
        # Patching only the isolated diagnostic makes the rejected hypothesis reproducible.
        with patch.object(phase, 'candidate_coordinates', coords):
            report = phase.analyze((EVIDENCE / 'r22/bitmap-phase-extended/native.log').read_text(),
                                   extended=True)
            self.assertEqual((report['exact'], report['samples']), (3775, 4096))
            self.assertFalse(report['passed'])
        with patch.object(inverse, 'candidate_coordinates', coords):
            report = inverse.analyze((EVIDENCE / 'r24/scalar-clipped/native.log').read_text(),
                                     'scalar-clipped')
            self.assertEqual((report['exact'], report['samples']), (751, 1008))
            self.assertFalse(report['passed'])

    def test_missing_or_misidentified_capture_fails(self):
        for bad in (self.text+self.text, self.text.replace('|done|ok', '|done|failed'),
                    self.text.replace('-r26-', '-wrong-', 1),
                    self.text.replace('|axis|0,2.5,-0.5,0.25,1,1,', '|axis|0,3,-0.5,0.25,1,1,')):
            with self.assertRaises(ValueError):
                analyze(bad)
