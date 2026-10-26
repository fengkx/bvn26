import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'color_ramp', ROOT / 'tools/probes/analyze_flash_color_ramp.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ColorRampAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.trace = (ROOT / 'evidence/importer-loud-fail/r12/pixels/color-arithmetic-ramp/native.log').read_text()

    def test_native_capture_is_complete_and_not_float_parity(self):
        report = MODULE.analyze(self.trace)
        self.assertEqual(report['native_cases'], 2048)
        self.assertEqual([row['different_from_float_model']
                          for row in report['opaque_float_diagnostics']], [82, 2, 0, 2])

    def test_missing_duplicate_or_wrong_identity_is_rejected(self):
        for trace in (self.trace.replace('|done|ok', '|done|incomplete'),
                      self.trace + self.trace,
                      self.trace.replace('|black|100,0,', '|black|100,1,')):
            with self.assertRaises(ValueError):
                MODULE.analyze(trace)
