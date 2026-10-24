import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_bitmap_inverse import analyze as analyze_inverse
from tools.probes.analyze_bitmap_spans import analyze

EVIDENCE = Path(__file__).resolve().parents[2] / 'evidence/importer-loud-fail/r24'


class BitmapSpanAnalysisTests(unittest.TestCase):
    def test_native_captures_pin_current_fixture_sources(self):
        root = Path(__file__).resolve().parents[2]
        for name in ('spans', 'scalar-clipped', 'scalar-repeat'):
            build = json.loads((EVIDENCE / name / 'build.json').read_text())
            self.assertEqual(hashlib.sha256((root / build['source']).read_bytes()).hexdigest(),
                             build['source_sha256'])
            self.assertIn(build['run_id'], (EVIDENCE / name / 'native.log').read_text())

    def test_same_coordinate_depends_on_draw_context(self):
        report = analyze((EVIDENCE / 'spans/native.log').read_text())
        self.assertEqual(report['native_rows'], 96)
        self.assertEqual(report['context_dependent_comparisons'], 26)
        self.assertFalse(report['production_admitted'])
        tail = next(row for row in report['rows']
                    if row['left'] == (0, 520, 0, 2.5, 224))
        self.assertEqual([d['x'] for d in tail['differences']], [517, 518, 519])

    def test_scalar_hypothesis_still_rejects_admission(self):
        for kind, exact in [('scalar-clipped', 1004), ('scalar-repeat', 854)]:
            report = analyze_inverse((EVIDENCE / kind / 'native.log').read_text(), kind)
            self.assertEqual((report['samples'], report['exact']), (1008, exact))
            self.assertFalse(report['passed'])
            self.assertFalse(report['production_admitted'])

    def test_capture_identity_and_completion_are_required(self):
        for kind in ('spans', 'scalar-clipped', 'scalar-repeat'):
            text = (EVIDENCE / kind / 'native.log').read_text()
            parse = analyze if kind == 'spans' else lambda text: analyze_inverse(text, kind)
            for invalid in (text + text, text.replace('|done|ok', '|done|failed'),
                            text.replace('-r24-', '-wrong-', 1)):
                with self.assertRaises(ValueError):
                    parse(invalid)

    def test_sample_loss_and_wrong_identity_are_rejected(self):
        text = (EVIDENCE / 'spans/native.log').read_text()
        for invalid in (text.replace('|span|0,260,0,2.5,-224,', '|span|0,260,0,3,-224,'),
                        text.replace('|span|0,260,0,2.5,-224,', '|span|0,260,0,2.5,')):
            with self.assertRaises(ValueError):
                analyze(invalid)
