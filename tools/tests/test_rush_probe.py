"""Exact rush comparison must reject low-bit drift and incomplete captures."""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'probes'))
from compare_rush_probe import compare, native_rows


class RushProbeTests(unittest.TestCase):
    def capture(self):
        return '\n'.join(
            [line for tick in range(21) for line in (
                f'AIREF|test|0|0|{tick}|0|clock|1',
                f'AIREF|test|0|0|{tick}|0|pixels|' + ','.join(['0'] * 81))]
            + ['AIREF|test|0|0|20|0|done|ok'])

    def test_one_channel_and_clock_drift_fail(self):
        expected = native_rows(self.capture())
        self.assertTrue(compare(expected, expected)['passed'])
        for field in ('frame', 'pixels'):
            actual = copy.deepcopy(expected)
            if field == 'frame':
                actual[16]['frame'] = 0
            else:
                actual[16]['pixels'][0] = 1
            self.assertFalse(compare(expected, actual)['passed'])

    def test_truncated_duplicate_and_mixed_samples_fail(self):
        text = self.capture()
        for bad in (text.replace('|done|ok', '|done|no'),
                    text.replace('AIREF|test|0|0|0|0|clock|1\n', ''),
                    text + '\nAIREF|test|0|0|0|0|clock|1',
                    text.replace('AIREF|test|0|0|0|', 'AIREF|other|0|0|0|'),
                    text.replace(',0', '', 1)):
            with self.subTest(bad=bad[:50]), self.assertRaises(ValueError):
                native_rows(bad)
