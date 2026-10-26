"""Reference data must expose missing samples and real pixel differences."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_flash_filters import compare, native_rows

EVIDENCE = ROOT / 'evidence/importer-loud-fail'


class FlashFilterProbeTests(unittest.TestCase):
    def test_native_capture_matches_saved_large_reference(self):
        native = native_rows((EVIDENCE / 'filter-probe-large/native.log').read_text(), 'blur')
        self.assertEqual(native, json.loads((EVIDENCE / 'native-filter-rows.json').read_text()))
        self.assertTrue(compare(native, native, 'blur')['passed'])
        changed = copy.deepcopy(native)
        changed[0]['alpha'][0] += 1
        self.assertFalse(compare(native, changed, 'blur')['passed'])

    def test_bounds_reference_has_all_210_captured_cases(self):
        native = native_rows((EVIDENCE / 'r02/blur-bounds/native.log').read_text(), 'bounds')
        self.assertEqual(len(native), 210)
        self.assertEqual(native, json.loads((EVIDENCE / 'native-bounds-filter-rows.json').read_text()))

    def test_incomplete_duplicate_or_mixed_capture_fails(self):
        log = (EVIDENCE / 'filter-probe-large/native.log').read_text()
        variants = [log.split('|done|')[0], log + log.splitlines()[0] + '\n',
                    log + 'AIREF|other|17|0|0|0|done|ok\n']
        for variant in variants:
            with self.subTest(variant=variant[-80:]), self.assertRaises(ValueError):
                native_rows(variant, 'blur')

    def test_small_reference_is_not_replaced_with_large_reference(self):
        small = native_rows((EVIDENCE / 'filter-probe/native.log').read_text(), 'blur')
        self.assertEqual(small, json.loads((EVIDENCE / 'native-small-filter-rows.json').read_text()))
        large = native_rows((EVIDENCE / 'filter-probe-large/native.log').read_text(), 'blur')
        with self.assertRaisesRegex(ValueError, 'sample counts'):
            compare(small, large, 'blur')

    def test_direct_color_reference_does_not_allow_error(self):
        native = [{'type': 'glow', 'opacity': 50, 'pixels': [0x80ff0000], 'premultiplied': [[128, 0, 0, 128]]}]
        actual = [{'type': 'glow', 'opacity': 50, 'pixels': [[128, 0, 0, 128]]}]
        self.assertTrue(compare(native, actual, 'color')['passed'])
        actual[0]['pixels'][0][0] -= 1
        self.assertFalse(compare(native, actual, 'color')['passed'])

    def test_color_capture_requires_direct_black_readback(self):
        log = (EVIDENCE / 'r03/colors/native.log').read_text()
        rows = native_rows(log, 'color')
        self.assertEqual(rows, json.loads((EVIDENCE / 'r03/native-color-rows.json').read_text()))
        without_black = '\n'.join(line for line in log.splitlines() if '|black|' not in line)
        with self.assertRaisesRegex(ValueError, 'black-background'):
            native_rows(without_black, 'color')
        del rows[0]['premultiplied']
        with self.assertRaisesRegex(ValueError, 'black-background'):
            compare(rows, [{'type': 'glow', 'opacity': 100}] * len(rows), 'color')


if __name__ == '__main__':
    unittest.main()
