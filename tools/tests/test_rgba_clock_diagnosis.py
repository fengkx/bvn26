"""A matching actor boundary must not certify an unrecorded visual clock."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/sampling-upgrade/s253'
spec = importlib.util.spec_from_file_location('s253_diagnosis', EVIDENCE / 'diagnose.py')
diagnosis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnosis)


class RgbaClockDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = gzip.decompress((ROOT / 'evidence/sampling-upgrade/s220/native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.events = diagnosis.events_from(cls.lines)
        cls.rows = [dict(tick=13, **diagnosis.state(e)) for e in cls.events
                    if e['tick'] == 13 and e['kind'] == 'state']

    def test_recompute_preserves_strict_failure_and_phase_limit(self):
        actual = diagnosis.diagnose()
        self.assertEqual(actual, json.loads((EVIDENCE / 'diagnosis.json').read_text()))
        self.assertEqual(actual['strict_rgba']['exit'], 1)
        self.assertEqual(actual['strict_rgba']['exact_frames'], 0)
        self.assertFalse(actual['common_visual_phase_proved'])
        self.assertFalse(actual['clock_fix_proved'])
        self.assertEqual(actual['actor_differences'], [
            dict(tick=0, slot=slot, field='touchFloor', native='undefined', godot=None)
            for slot in ('p1', 'p2')])

    def test_tick_shift_is_detected_without_pixel_alignment(self):
        self.assertEqual(diagnosis.paired_rows(self.events, self.rows, 13), [])
        shifted = [dict(row, tick=12) for row in self.rows]
        self.assertTrue(diagnosis.paired_rows(self.events, shifted, 12))

    def test_missing_actor_is_not_a_common_phase(self):
        with self.assertRaisesRegex(ValueError, 'paired actor'):
            diagnosis.paired_rows(self.events, self.rows[:1], 13)

    def test_broken_sequence_rejects(self):
        with self.assertRaisesRegex(ValueError, 'sequence'):
            diagnosis.events_from(self.lines[:50] + self.lines[51:])

    def test_clock_regression_rejects(self):
        changed = self.lines.copy()
        parts = changed[50].split('|', 7)
        parts[3] = '-1'
        changed[50] = '|'.join(parts)
        with self.assertRaisesRegex(ValueError, 'clock'):
            diagnosis.events_from(changed)


if __name__ == '__main__':
    unittest.main()
