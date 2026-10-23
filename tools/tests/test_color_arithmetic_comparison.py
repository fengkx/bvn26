import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'color_arithmetic', ROOT / 'tools/probes/compare_flash_color_arithmetic.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ColorArithmeticComparisonTests(unittest.TestCase):
    def setUp(self):
        self.trace = (ROOT / 'evidence/importer-loud-fail/r11/pixels/color-arithmetic/native.log').read_text()
        self.native = MODULE.native_samples(self.trace)

    def test_exact_copy_passes_but_one_channel_difference_fails(self):
        self.assertTrue(MODULE.compare(self.native, self.native)['passed'])
        changed = [{**row, 'premultiplied': list(row['premultiplied'])} for row in self.native]
        changed[0]['premultiplied'][0] += 1
        result = MODULE.compare(self.native, changed)
        self.assertFalse(result['passed'])
        self.assertEqual(result['exact_cases'], 23)

    def test_missing_reordered_or_malformed_samples_fail(self):
        for rows in (self.native[:-1], list(reversed(self.native)),
                     [{**self.native[0], 'premultiplied': [0, 0, 0, 0.0]}] + self.native[1:]):
            with self.assertRaises(ValueError):
                MODULE.compare(self.native, rows)
        with self.assertRaises(ValueError):
            MODULE.compare(self.native[:-1], self.native)
        with self.assertRaises(ValueError):
            MODULE.native_samples(self.trace.replace('|done|ok', '|done|incomplete'))
        with self.assertRaises(ValueError):
            MODULE.native_samples(self.trace + self.trace)
