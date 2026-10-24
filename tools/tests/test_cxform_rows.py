import json
from pathlib import Path
import tempfile
import unittest

from tools.probes.analyze_cxform_rows import analyze, load_reciprocals, row_cx

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r39'


class CxformRowTests(unittest.TestCase):
    def test_independent_controls_do_not_admit_nested_counterexamples(self):
        report = analyze(EVIDENCE, ROOT/'evidence/importer-loud-fail/r38')
        self.assertEqual(report, json.loads((EVIDENCE/'arithmetic.json').read_text()))
        self.assertFalse(report['cpu_hypothesis_passed'])
        self.assertFalse(report['production_admitted'])
        for name, count in (('rows',25920),('scalar',3072),('spans',8652),('varied',8652)):
            self.assertEqual(report['scores'][name]['exact'], count)
            self.assertEqual(report['scores'][name]['pixels'], count)
        self.assertEqual(report['scores']['native_buffer_boundaries']['exact'],43006)
        self.assertEqual(report['scores']['exact_reciprocal_negative_control']['exact'],25621)

    def test_reciprocal_measurements_require_complete_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'reciprocal.txt'
            path.write_text('1 3f800000\n')
            with self.assertRaisesRegex(ValueError,'Incomplete'):
                load_reciprocals(path)

    def test_outside_clip_must_not_select_an_arithmetic_path(self):
        for x in (-1,16):
            with self.assertRaisesRegex(ValueError,'outside'):
                row_cx([37,104,125,135],100,16,x,{})
