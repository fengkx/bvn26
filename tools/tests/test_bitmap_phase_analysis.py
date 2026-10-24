import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('bitmap_phase', ROOT / 'tools/probes/analyze_bitmap_phase.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BitmapPhaseAnalysisTests(unittest.TestCase):
    def trace(self, extended=False):
        name = 'bitmap-phase-extended' if extended else 'bitmap-phase'
        return (ROOT / 'evidence/importer-loud-fail/r22' / name / 'native.log').read_text()

    def test_candidate_is_exact_only_on_calibration_not_admitted(self):
        calibration = MODULE.analyze(self.trace())
        self.assertEqual((calibration['samples'], calibration['exact']), (1536, 1536))
        self.assertTrue(calibration['passed'])
        self.assertFalse(calibration['production_admitted'])
        extended = MODULE.analyze(self.trace(True), extended=True)
        self.assertEqual(extended['samples'], 4096)
        self.assertLess(extended['exact'], extended['samples'])
        self.assertFalse(extended['passed'])
        self.assertFalse(extended['production_admitted'])

    def test_missing_duplicate_wrong_case_and_mixed_runs_are_rejected(self):
        text = self.trace()
        for invalid in (text.replace('|done|ok', '|done|no'), text + text,
                        text.replace('|phase|255,2,', '|phase|255,3,'),
                        text.replace('|filter-bitmap-phase-r22-', '|wrong-', 1)):
            with self.assertRaises(ValueError):
                MODULE.analyze(invalid)


if __name__ == '__main__':
    unittest.main()
